#!/usr/bin/env python3
"""
Listens to the recordings that already exist on the site (the Gary audio) and
writes, for every article, the words that are spoken and when:

  issues/<slug>/audio-raw/<article id>.json   {"url", "duration", "words": [[word, start, end], …]}

Runs in GitHub Actions (the MP3s are downloaded there and never enter git).
align.py then compares these words with the article text.

Usage: python3 pipeline/transcribe.py <slug> [--model small.en]
Needs: pip install faster-whisper
"""
import json, os, subprocess, sys, tempfile, urllib.request

slug = sys.argv[1]
model_name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "small.en"
base = f"issues/{slug}"
src = json.load(open(f"{base}/audio-source.json", encoding="utf-8"))
os.makedirs(f"{base}/audio-raw", exist_ok=True)
from faster_whisper import WhisperModel
model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
tmp = tempfile.mkdtemp()
for aid, a in src.items():
    out = f"{base}/audio-raw/{aid}.json"
    if os.path.exists(out):
        continue
    url = a["url"].replace("http://", "https://")
    f = os.path.join(tmp, "a.mp3")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) SOI-archive-fetcher"})
        open(f, "wb").write(urllib.request.urlopen(req, timeout=120).read())
    except Exception as e:
        json.dump({"url": url, "error": str(e)}, open(out, "w"))
        print(f"{slug} {aid}: DOWNLOAD FAILED {e}", flush=True)
        continue
    segs, info = model.transcribe(f, language="en", word_timestamps=True, vad_filter=True, beam_size=1,
                                  condition_on_previous_text=False)
    words = [[w.word.strip(), round(w.start, 2), round(w.end, 2)] for s in segs for w in s.words]
    json.dump({"url": url, "duration": round(info.duration, 1), "bytes": os.path.getsize(f), "model": model_name, "words": words},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{slug} {aid}: {info.duration:.0f}s, {len(words)} words", flush=True)
