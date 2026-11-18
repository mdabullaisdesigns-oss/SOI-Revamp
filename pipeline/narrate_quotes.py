#!/usr/bin/env python3
"""Narrate the quotes that have no article recording to point at (pipeline/quote-audio/todo.json),
same voice and settings as the archive (Gemini 3.8 Flash-Lite TTS, Charon). Writes
out/quotes/q-<key>.mp3 and pipeline/quote-audio/done.json {key: {url, d}}."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narrate_gcp as g

todo = json.load(open("pipeline/quote-audio/todo.json", encoding="utf-8"))
done_p = "pipeline/quote-audio/done.json"
done = json.load(open(done_p, encoding="utf-8")) if os.path.exists(done_p) else {}
os.makedirs("out/quotes", exist_ok=True)
for q in todo:
    if q["key"] in done:
        continue
    text = g.prepare(q["t"])
    tmp = tempfile.mkdtemp(); raw = os.path.join(tmp, "raw.wav"); trim = os.path.join(tmp, "t.wav")
    dst = f"out/quotes/q-{q['key']}.mp3"
    try:
        g.synth_wav(text, g.MODELS[0], raw)
    except Exception:
        g.synth_wav(text, g.MODELS[1], raw)
    g.run(["ffmpeg", "-y", "-i", raw, "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,"
           "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse", trim])
    g.run(["ffmpeg", "-y", "-i", trim, "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", "44100", "-ac", "1", "-b:a", "96k", dst])
    d = round(g.duration(dst), 2)
    wpm = len(text.split()) / max(d, 1) * 60
    print(f"{q['key']}: {d}s, {wpm:.0f} words/min  {q['t'][:50]}")
    done[q["key"]] = {"url": f"/media/audio/quotes/q-{q['key']}.mp3", "d": d}
json.dump(done, open(done_p, "w", encoding="utf-8"), indent=1)
print(f"{len(done)} of {len(todo)} quotes narrated")
