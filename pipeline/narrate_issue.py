#!/usr/bin/env python3
"""
Narrate one whole issue with Gemini TTS, voice Charon, Issue 133 settings
(model gemini-3.8-flash-lite-tts, temperature 0.5, the original style prompt).

  1. narration.json  (narrate.py prepare: the spoken sentences, in page order)
  2. one MP3 per article -> out/<slug>/SOI-<slug>-<id>.mp3   (uploaded to R2 by the workflow)
  3. audio-source.json  { id: {url, file} }  so transcribe.py + align.py can time every sentence

Every article is narrated except: articles marked "audio": false, Children's Corner,
CPS Newsletter (owner's decision 15 Nov). Earlier Gary recordings are replaced.
Articles already in R2 (listed in the file named by --done) are skipped, so a
stopped run can simply be started again.

Usage: python3 pipeline/narrate_issue.py <slug> [--done done.txt] [--only id,id] [--threads 4]
"""
import json, os, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build, narrate, narrate_gcp

EXCLUDE = {"children’s corner", "children's corner", "cps newsletter"}
VOICE = "Charon (" + narrate_gcp.MODELS[0].split(":")[-1].replace("gemini-", "Gemini ").replace("-flash-lite-tts", " Flash-Lite TTS").replace("-flash-tts", " Flash TTS") + ")"
AUDIO_BASE = os.environ.get("SOI_AUDIO_BASE", "/media/audio")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def paras_of(a):
    body, thought = [], []
    for i in a["items"]:
        if i["k"] not in narrate.SPOKEN:
            continue
        t = " ".join(narrate.strip_tags(x) for x in build.sentences(i["runs"], emphasis=False)).strip()
        if t:
            (thought if i["k"] == "thought" else body).append(t)
    return body + thought


def main():
    slug = sys.argv[1]
    base = f"issues/{slug}"
    narrate.prepare(slug)
    issue = json.load(open(f"{base}/issue.json", encoding="utf-8"))
    done = set(open(arg("--done")).read().split()) if arg("--done") and os.path.exists(arg("--done")) else set()
    only = set(arg("--only", "").split(",")) - {""}
    out_dir = f"out/{slug}"
    os.makedirs(out_dir, exist_ok=True)
    src_path = f"{base}/audio-source.json"
    src = json.load(open(src_path, encoding="utf-8")) if os.path.exists(src_path) else {}
    jobs, skipped = [], []
    for a in issue["articles"]:
        name = f"SOI-{slug}-{a['id']}.mp3"
        if a.get("audio") is False or a["title"].strip().lower() in EXCLUDE:
            skipped.append(a["title"]); continue          # an existing recording of these (if any) is kept
        if only and a["id"] not in only:
            continue
        url = f"{AUDIO_BASE}/{slug[:4]}/{name}"
        if name in done:
            src[a["id"]] = {"url": url, "voice": VOICE}; continue
        jobs.append((a, name, url))
    print(f"{slug}: {len(jobs)} articles to narrate, {len(done)} already in R2; not narrated: {', '.join(skipped) or 'none'}", flush=True)

    def one(job):
        a, name, url = job
        dst = os.path.join(out_dir, name)
        secs = narrate_gcp.article({"title": a["title"], "paras": paras_of(a)}, dst)
        return a["id"], url, dst, secs

    failed, total = [], 0.0
    with cf.ThreadPoolExecutor(int(arg("--threads", "4"))) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for f in cf.as_completed(futs):
            a = futs[f][0]
            try:
                aid, url, dst, secs = f.result()
            except Exception as e:
                failed.append(a["id"]); print(f"FAILED {a['id']}: {str(e)[:300]}", flush=True); continue
            total += secs
            src[aid] = {"url": url, "file": dst, "voice": VOICE}
            raw = f"{base}/audio-raw/{aid}.json"
            if os.path.exists(raw):                    # the old (Gary) timing is replaced
                os.remove(raw)
    json.dump(src, open(src_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{slug}: {total / 60:.1f} min of new audio, about {total * 25 / 1e6 * 6:.2f} USD; failed: {failed or 'none'}")
    if failed:
        open(f"{out_dir}/FAILED.txt", "w").write("\n".join(failed))


if __name__ == "__main__":
    main()
