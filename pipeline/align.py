#!/usr/bin/env python3
"""
Read-along timings for recordings that already exist (the Gary issues).

  issues/<slug>/narration.json     the sentences of each article, in page order
  issues/<slug>/audio-raw/<id>.json the words heard in the recording, with times
                                    (written by the "Listen to existing audio" workflow)
  -> issues/<slug>/audio.json      { id: {url, duration, times[], match, …} }

For every article the text is lined up word by word with what was heard.
"match" is the share of the article's words that are heard in the recording, in
order.  A recording is flagged when the match is low or when a whole passage of
the text is not in it (or the other way round); build.py still adds the player
with timings, and check_wp.py lists the flagged ones for re-recording.

Usage: python3 pipeline/align.py <slug>
"""
import difflib, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check import norm

LOW, GAP = 88.0, 30        # heard-in-order share below this, or this many words in a row missing -> flagged


def runs_of(flags, words):
    out, cur = [], []
    for w, f in zip(words, flags):
        if not f:
            cur.append(w)
        elif cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return sorted(out, key=len, reverse=True)


def main():
    slug = sys.argv[1]
    base = f"issues/{slug}"
    narr = json.load(open(base + "/narration.json", encoding="utf-8"))["articles"]
    src = json.load(open(base + "/audio-source.json", encoding="utf-8"))
    audio = {}
    full = {a["id"]: a for a in json.load(open(base + "/issue.json", encoding="utf-8"))["articles"]}
    for aid, a in narr.items():
        raw = f"{base}/audio-raw/{aid}.json"
        if aid not in src or not os.path.exists(raw):
            continue
        r = json.load(open(raw, encoding="utf-8"))
        if r.get("error") or not r.get("words"):
            audio[aid] = {"url": src[aid]["url"].replace("http://", "https://"), "error": r.get("error", "no speech found")}
            continue
        tw, tsent = [], []                           # text words, and the sentence each belongs to
        for si, s in enumerate(a["sentences"]):
            for w in norm(s):
                tw.append(w); tsent.append(si)
        hw, ht = [], []                              # heard words and their start times
        for w, st, en in r["words"]:
            for x in norm(w):
                hw.append(x); ht.append(st)
        sm = difflib.SequenceMatcher(None, tw, hw, autojunk=False)
        ft, fh, when = [False] * len(tw), [False] * len(hw), [None] * len(tw)
        for i, j, n in sm.get_matching_blocks():
            if n >= 2 or (n == 1 and len(tw) < 4):
                for k in range(n):
                    ft[i + k] = fh[j + k] = True
                    when[i + k] = ht[j + k]
        # start time of each sentence: its first heard word (stepped back if the opening words were missed)
        n_s = len(a["sentences"])
        first = [None] * n_s
        pos = {}
        for k, si in enumerate(tsent):
            pos.setdefault(si, k)
            if when[k] is not None and first[si] is None:
                first[si] = max(0.0, when[k] - 0.33 * (k - pos[si]))
        known = [(si, t) for si, t in enumerate(first) if t is not None]
        times = []
        for si in range(n_s):
            if first[si] is not None:
                t = first[si]
            else:                                    # sentence not heard: place it between its neighbours
                before = max(((s, t) for s, t in known if s < si), default=(-1, 0.0))
                after = min(((s, t) for s, t in known if s > si), default=(n_s, r["duration"]))
                t = before[1] + (after[1] - before[1]) * (si - before[0]) / max(1, after[0] - before[0])
            times.append(round(max(t, times[-1] if times else 0.0), 2))
        # the old recordings also read the kicker, the author note and the boxed quotes, which are on the page
        # but outside the read-along sentences: those words are not a difference between recording and text
        fw = norm(" ".join([full.get(aid, {}).get("kicker", ""), full.get(aid, {}).get("author", "")] +
                           ["".join(x[1] for x in it["runs"]) for it in full.get(aid, {}).get("items", [])]))
        fh_page = list(fh)
        for i, j, n in difflib.SequenceMatcher(None, fw, hw, autojunk=False).get_matching_blocks():
            if n >= 4:
                for k in range(n):
                    fh_page[j + k] = True
        match = round(100.0 * sum(ft) / max(1, len(tw)), 1)
        extra = round(100.0 * (len(hw) - sum(fh)) / max(1, len(hw)), 1)
        miss, more = runs_of(ft, tw), runs_of(fh_page, hw)
        entry = {"url": src[aid]["url"].replace("http://", "https://"), "duration": r["duration"], "times": times,
                 "match": match, "not_in_text": extra, "voice": src[aid].get("voice", "Gary (existing recording)")}
        notes = []
        if miss and len(miss[0]) >= GAP:
            notes.append(f"{len(miss[0])} words of the text are not read (“{' '.join(miss[0][:8])}…”)")
        if more and len(more[0]) >= GAP:
            notes.append(f"the recording has {len(more[0])} words that are not in the text (“{' '.join(more[0][:8])}…”)")
        if match < LOW:
            notes.append(f"only {match}% of the text is heard in the recording")
        if notes:
            entry["flag"] = "; ".join(notes)
        audio[aid] = entry
    json.dump(audio, open(base + "/audio.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = [a for a in audio.values() if "times" in a]
    flagged = [k for k, a in audio.items() if a.get("flag") or a.get("error")]
    print(f"{slug}: {len(ok)} recordings timed, average match "
          f"{round(sum(a['match'] for a in ok) / max(1, len(ok)), 1)}%, flagged: {flagged or 'none'}")


if __name__ == "__main__":
    main()
