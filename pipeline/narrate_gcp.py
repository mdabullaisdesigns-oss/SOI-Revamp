#!/usr/bin/env python3
"""
Narration with Google Cloud Text-to-Speech (Gemini-TTS, voice "Charon").
Settings: docs/narration-settings.md (the owner's "SOI narration settings", 15 Nov 2026 update).

Billing goes to the Google Cloud project "SOI Narration" (free-trial credit), not to AI Studio.
Key: environment variable GCP_TTS_API_KEY (GitHub secret; never stored in files).

  python3 pipeline/narrate_gcp.py article <article.json> <out.mp3>
        article.json = {"title": ..., "paras": [paragraph text, ...]}
  python3 pipeline/narrate_gcp.py probe
        tries the candidate model names once and reports which ones this key may use

Pieces are split at paragraph boundaries and kept under Cloud TTS's 4,000-byte limit;
each piece is trimmed of silence (0.06 s kept) and joined with 0.65 s between paragraphs
(0.32 s where one paragraph had to be split); the result is loudness-normalised and saved
as 96 kbps mono 44.1 kHz MP3.
"""
import base64, json, os, re, subprocess, sys, tempfile, time, urllib.error, urllib.request

KEY = os.environ.get("GCP_TTS_API_KEY", "")
URL = "https://texttospeech.googleapis.com/v1/text:synthesize?key="
MODELS = [m for m in os.environ.get("SOI_TTS_MODELS", "").split(",") if m] or [
    "gemini-3.8-flash-lite-tts", "gemini-3.8-flash-lite-preview-tts", "gemini-3.8-flash-tts",
    "gemini-2.5-flash-lite-preview-tts", "gemini-2.5-flash-tts"]
VOICE = "Charon"
PROMPT = """# AUDIO PROFILE: The Narrator
A mature male narrator for a spiritual magazine podcast. Warm, deep, smooth voice, recorded close to a premium studio microphone.

## THE SCENE
A quiet studio. He is reading a reflective article aloud to listeners who want to learn and contemplate.

### DIRECTOR'S NOTES
Style: calm, sincere, reflective and gently persuasive. Smooth and pleasing on the ears, soft "s" sounds.
Pace: steady and even from the first word to the last. Never speed up, swallow or trail off at the end of a sentence; say the final words as clearly as the first.
Clarity: articulate every word fully for listeners who are still learning English. Leave a short, clear pause after each sentence.
Accent: clear, neutral international English."""
MAX_BYTES = 3600          # text field limit is 4,000 bytes; keep a margin


def prepare(t):
    t = re.sub(r"\s*\((?:\d{1,3}\s*:\s*\d{1,3}(?:[-–]\d{1,3})?(?:[,;]\s*)?)+\)", "", t)          # (51: 56)
    t = re.sub(r"\s*\((?:Sahih|Sunan|Musnad|Jami|Muwatta|Mishkat|Tirmidhi|Bukhari|Muslim|Abu Dawud|Ibn Majah|Matthew|Mark|Luke|John)[^)]*\)", "", t)
    t = re.sub(r"\bProf\.?(?=\s)", "Professor", t)
    return re.sub(r"\s+", " ", t).strip()


def pieces(title, paras):
    """[(text, joins_previous_paragraph)] each under MAX_BYTES."""
    out = []
    first = True
    for p in paras:
        p = prepare(p)
        if first:
            p = prepare(title).rstrip(".") + ". " + p
            first = False
        if len(p.encode()) <= MAX_BYTES:
            out.append((p, False)); continue
        sents, cur, cont = re.split(r"(?<=[.!?”’\"])\s+", p), "", False
        for s in sents:
            if cur and len((cur + " " + s).encode()) > MAX_BYTES:
                out.append((cur, cont)); cur, cont = s, True
            else:
                cur = (cur + " " + s).strip()
        if cur:
            out.append((cur, cont))
    return out


def synth(text, model):
    body = {"input": {"prompt": PROMPT, "text": text},
            "voice": {"languageCode": "en-US", "name": VOICE, "modelName": model},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000}}
    req = urllib.request.Request(URL + KEY, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return base64.b64decode(json.load(r)["audioContent"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:600]
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(8 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode().strip())


def article(src, dst, model=None):
    a = json.load(open(src, encoding="utf-8"))
    parts = pieces(a["title"], a["paras"])
    model = model or MODELS[0]
    tmp = tempfile.mkdtemp()
    files, words = [], 0
    for k, (text, cont) in enumerate(parts):
        raw = os.path.join(tmp, f"p{k}.wav")
        audio = synth(text, model)
        if audio[:4] != b"RIFF":                          # raw PCM: wrap as 24 kHz 16-bit mono WAV
            open(raw + ".pcm", "wb").write(audio)
            run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", raw + ".pcm", raw])
        else:
            open(raw, "wb").write(audio)
        trimmed = os.path.join(tmp, f"t{k}.wav")
        run(["ffmpeg", "-y", "-i", raw, "-af",
             "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,"
             "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse", trimmed])
        n = len(text.split()); words += n
        wpm = n / max(duration(trimmed), 1) * 60
        print(f"  piece {k + 1}/{len(parts)}: {n} words, {duration(trimmed):.1f} s, {wpm:.0f} words/min" + ("  <- check pace" if not 100 <= wpm <= 200 else ""))
        if files:
            gap = os.path.join(tmp, f"g{k}.wav")
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.32" if cont else "0.65", gap])
            files.append(gap)
        files.append(trimmed)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-af", "loudnorm=I=-16:TP=-1.5:LRA=7",
         "-ar", "44100", "-ac", "1", "-b:a", "96k", dst])
    secs = duration(dst)
    print(f"{dst}: {len(parts)} pieces, {words} words, {secs / 60:.1f} min, about {secs * 25 / 1e6 * 6:.3f} USD at $6 per million audio tokens")
    return secs


def probe():
    ok = []
    for m in MODELS:
        try:
            a = synth("Spirit of Islam. A test.", m)
            print(f"OK    {m}  ({len(a)} bytes)"); ok.append(m)
        except Exception as e:
            print(f"NO    {m}  {str(e)[:300]}")
    return ok


if __name__ == "__main__":
    if not KEY:
        sys.exit("GCP_TTS_API_KEY is not set")
    if sys.argv[1:2] == ["probe"]:
        sys.exit(0 if probe() else 1)
    if sys.argv[1:2] == ["article"]:
        article(sys.argv[2], sys.argv[3], os.environ.get("SOI_TTS_MODEL") or None)
    else:
        sys.exit(__doc__)
