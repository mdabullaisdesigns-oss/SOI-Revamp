#!/usr/bin/env python3
"""
Stage 4 - narration (separate from the build; run it when the voice is ready).

  prepare   issues/<slug>/narration.json : for every article the exact sentences
            to be spoken, in the same order as the <span class="ev-s"> spans of
            the page (title, body, closing reflection; not the notes, footnotes
            or boxed pull quotes), with character counts for the TTS budget.
  attach    after the MP3s exist and have been timed (align step from the
            Issue 133 toolkit), write issues/<slug>/audio.json:
              { "<article id>": { "url": "https://…/SOI-<slug>-<id>.mp3",
                                  "duration": 180.4, "times": [0.0, 2.8, …] } }
            build.py then adds the player and the sentence timings by itself.

The TTSMaker ("Gary", voice 2560) call is not wired in yet: the API key and the
confirmed API details come later (open question 1 in the handoff).  Until then
every article is "pending" and the page is built without players.

Usage: python3 pipeline/narrate.py prepare <slug> [<slug> …]
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build

SPOKEN = ("p", "lead", "h", "qh", "quote", "ayah", "bismillah", "thought", "intro", "qa_intro")


def strip_tags(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()


def prepare(slug):
    base = os.path.join("issues", slug)
    issue = json.load(open(os.path.join(base, "issue.json"), encoding="utf-8"))
    audio = json.load(open(os.path.join(base, "audio.json"), encoding="utf-8")) if os.path.exists(os.path.join(base, "audio.json")) else {}
    out, total = {}, 0
    for a in issue["articles"]:
        sents = [a["title"]]
        thought = []
        for i in a["items"]:
            if i["k"] not in SPOKEN:
                continue
            s = [strip_tags(x) for x in build.sentences(i["runs"], emphasis=False)]
            (thought if i["k"] == "thought" else sents).extend(s)
        sents += thought[:len(thought)]
        chars = sum(len(s) for s in sents) + len(sents)
        total += chars
        out[a["id"]] = {"title": a["title"], "status": "ready" if a["id"] in audio else "pending",
                        "file": f"SOI-{slug}-{a['id']}.mp3", "chars": chars, "sentences": sents}
    json.dump({"slug": slug, "voice": "TTSMaker Gary (2560)", "chars": total, "articles": out},
              open(os.path.join(base, "narration.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pend = sum(1 for v in out.values() if v["status"] == "pending")
    print(f"{slug}: {len(out)} articles, {total:,} characters to narrate, {pend} pending")
    return total


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "prepare":
        sys.exit(__doc__)
    t = sum(prepare(s) for s in sys.argv[2:])
    if len(sys.argv) > 3:
        print(f"total: {t:,} characters")
