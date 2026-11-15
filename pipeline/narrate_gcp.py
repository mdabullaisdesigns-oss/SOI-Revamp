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
AUTH_KEY = os.environ.get("GCP_AUTH_KEY", "")      # API key bound to the soi-tts service account (Agent Platform API)
VERTEX = "https://aiplatform.googleapis.com/v1/publishers/google/models/{}:generateContent?key="
TEMPERATURE = float(os.environ.get("SOI_TTS_TEMPERATURE", "0.5"))   # owner chose the Issue 133 sound (16 Nov): 0.5, original prompt
TOKEN = os.environ.get("GCP_ACCESS_TOKEN", "")     # short-lived token from GitHub's keyless sign-in (Workload Identity Federation)
PROJECT = os.environ.get("GCP_PROJECT", "project-2c2c83fa-e3a5-4e94-895")
URL = "https://texttospeech.googleapis.com/v1/text:synthesize?key="
MODELS = [m for m in os.environ.get("SOI_TTS_MODELS", "").split(",") if m] or (
    ["vertex:gemini-3.8-flash-lite-tts", "vertex:gemini-3.8-flash-tts", "vertex:gemini-3.1-flash-tts-preview",
     "vertex:gemini-2.5-flash-preview-tts", "vertex:gemini-2.5-flash-tts"] if (os.environ.get("GCP_AUTH_KEY") or os.environ.get("GCP_ACCESS_TOKEN")) else []) + [
    "gemini-2.5-flash-tts", "gemini-3.1-flash-tts-preview"]     # (2.5 Flash-Lite allows only 512 bytes with the prompt)
VOICE = "Charon"
PROMPT = """# AUDIO PROFILE: The Narrator
A mature male narrator for a spiritual magazine podcast. Warm, deep, smooth voice, recorded close to a premium studio microphone.

## THE SCENE
A quiet studio. He is reading a reflective article aloud to listeners who want to learn and contemplate.

### DIRECTOR'S NOTES
Style: calm, sincere, reflective and gently persuasive. Smooth and pleasing on the ears, soft "s" sounds.
Pace: moderate and unhurried, slightly brisk, never rushed. A natural breath between sentences.
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


def request(url, key, body):
    h = {"Content-Type": "application/json"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
        h["x-goog-user-project"] = PROJECT
    elif key:
        url += "?key=" + key
    return urllib.request.Request(url, data=json.dumps(body).encode(), headers=h)


def synth(text, model):
    if model.startswith("vertex:"):
        return synth_vertex(text, model[7:])
    body = {"input": {"prompt": PROMPT, "text": text},
            "voice": {"languageCode": "en-US", "name": VOICE, "modelName": model},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000}}
    req = request(URL.split("?")[0], KEY, body)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return base64.b64decode(json.load(r)["audioContent"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:600]
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(8 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")


def synth_vertex(text, model):
    """Gemini TTS through Google Cloud (Agent Platform / Vertex AI), the same request as AI Studio."""
    body = {"contents": [{"role": "user", "parts": [{"text": PROMPT + "\n\n#### TRANSCRIPT\n\n" + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "temperature": TEMPERATURE,
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
    url = (f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/global/publishers/google/models/{model}:generateContent"
           if TOKEN else VERTEX.format(model).split("?")[0])
    req = request(url, AUTH_KEY, body)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                d = json.load(r)
            part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
            return base64.b64decode(part["data"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:600]
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(8 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")
        except (KeyError, IndexError) as e:
            raise RuntimeError("no audio in the reply: " + json.dumps(d)[:400])


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode().strip())


def to_wav(audio, path):
    if audio[:4] != b"RIFF":                              # raw PCM: wrap as 24 kHz 16-bit mono WAV
        open(path + ".pcm", "wb").write(audio)
        run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", path + ".pcm", path])
    else:
        open(path, "wb").write(audio)


def synth_wav(text, model, path, depth=0):
    """One piece to a WAV file. If Google refuses it (e.g. the copyright filter on quoted
    Quran translations) or returns nothing, the piece is split into shorter parts and joined."""
    try:
        to_wav(synth(text, model), path)
        return
    except Exception as e:
        sents = re.split(r"(?<=[.!?”’\"])\s+", text)
        if depth >= 3 or len(sents) < 2:
            raise
        print(f"    piece refused ({str(e)[:120]}); retrying in {min(len(sents), 2 if depth else 3)} shorter parts")
    n = 2 if depth else 3
    size = -(-len(sents) // n)
    parts = [" ".join(sents[k:k + size]) for k in range(0, len(sents), size)]
    files = []
    for k, t in enumerate(parts):
        f = f"{path}.{k}.wav"
        synth_wav(t, model, f, depth + 1)
        files.append(f)
    lst = path + ".txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-ar", "24000", "-ac", "1", path])


def article(src, dst, model=None):
    a = json.load(open(src, encoding="utf-8")) if isinstance(src, str) else src
    parts = pieces(a["title"], a["paras"])
    models = [model] if model else MODELS[:2]             # 3.8 Flash-Lite, then 3.8 Flash (same voice) if Lite fails
    tmp = tempfile.mkdtemp()
    files, words = [], 0
    for k, (text, cont) in enumerate(parts):
        n = len(text.split())
        best = None
        for attempt in range(3):                          # re-record a piece whose pace is off (cut off, or long silences)
            raw = os.path.join(tmp, f"p{k}-{attempt}.wav")
            err = None
            for m in models:
                try:
                    synth_wav(text, m, raw); err = None; break
                except Exception as e:
                    err = e
            if err:
                raise err
            trimmed = os.path.join(tmp, f"t{k}-{attempt}.wav")
            run(["ffmpeg", "-y", "-i", raw, "-af",
                 "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,"
                 "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse", trimmed])
            wpm = n / max(duration(trimmed), 1) * 60
            score = abs(wpm - 150)
            if best is None or score < best[0]:
                best = (score, trimmed, wpm)
            if 80 <= wpm <= 210 or n < 30:               # short headings always look slow (padding)
                break
            print(f"    piece {k + 1}: {wpm:.0f} words/min, recording again")
        _, trimmed, wpm = best
        words += n
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
            print(f"NO    {m}  " + " ".join(str(e).split())[:400])
    return ok


if __name__ == "__main__":
    if not (KEY or AUTH_KEY or TOKEN):
        sys.exit("no Google sign-in: GCP_ACCESS_TOKEN, GCP_AUTH_KEY or GCP_TTS_API_KEY")
    if sys.argv[1:2] == ["probe"]:
        sys.exit(0 if probe() else 1)
    if sys.argv[1:2] == ["article"]:
        article(sys.argv[2], sys.argv[3], os.environ.get("SOI_TTS_MODEL") or None)
    else:
        sys.exit(__doc__)
