#!/usr/bin/env python3
"""List (and with --delete, remove) audio in R2 that the site no longer uses.

Kept: every MP3 named in any issues/*/audio.json or audio-source.json (the new narration,
Issue 133, and old recordings still used by Children's Corner / CPS Newsletter), plus all
Issue 133 files. Everything else under audio/ is an old copy (e.g. Gary recordings that the new
narration replaced); the originals still exist on the WordPress site.
"""
import glob, json, os, subprocess, sys
used = set()
for f in glob.glob("issues/*/audio.json") + glob.glob("issues/*/audio-source.json"):
    for v in json.load(open(f, encoding="utf-8")).values():
        u = v.get("url", "")
        used.add(u.rsplit("/", 1)[-1])
ls = subprocess.run(["aws", "s3", "ls", f"s3://{os.environ['R2_BUCKET']}/audio/", "--recursive", "--endpoint-url", os.environ["R2_ENDPOINT"]],
                    capture_output=True, text=True, check=True).stdout.splitlines()
old, keep, size = [], 0, 0
for line in ls:
    parts = line.split(None, 3)
    if len(parts) < 4:
        continue
    n, key = int(parts[2]), parts[3]
    name = key.rsplit("/", 1)[-1]
    if name in used or "133" in name or name.startswith("SOI-2026-11"):
        keep += 1
    else:
        old.append(key); size += n
print(f"keep {keep} files; old and unused: {len(old)} files, {size / 1e9:.2f} GB")
for k in old[:15]:
    print("  e.g.", k)
if "--delete" in sys.argv:
    for k in old:
        subprocess.run(["aws", "s3", "rm", f"s3://{os.environ['R2_BUCKET']}/{k}", "--endpoint-url", os.environ["R2_ENDPOINT"], "--only-show-errors"], check=True)
    print(f"deleted {len(old)} files")
