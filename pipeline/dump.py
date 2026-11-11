#!/usr/bin/env python3
"""Compact view of issues/<slug>/raw/pages.json for writing the outline.
Usage: python3 pipeline/dump.py <slug> [first_page] [last_page] [--full]
Each block: id, font size/face of its first line, word count, opening words."""
import json, sys
slug = sys.argv[1]
args = [a for a in sys.argv[2:] if not a.startswith("--")]
full = "--full" in sys.argv
lo = int(args[0]) if args else 1
hi = int(args[1]) if len(args) > 1 else 10 ** 6
for p in json.load(open(f"issues/{slug}/raw/pages.json", encoding="utf-8")):
    if not lo <= p["n"] <= hi:
        continue
    print(f"--- page {p['n']} ({p['src']}, {p['words']} words, {len(p['links'])} links)")
    for b in p["blocks"]:
        l0 = b["lines"][0]
        text = " ".join(l["t"] for l in b["lines"])
        n = len(text.split())
        face = l0["f"].split("-")[-1][:8] if "-" in l0["f"] else l0["f"][:8]
        print(f"{b['id']:>8} {l0['sz']:>4} {face:<8} x{int(b['bb'][0]):<3} y{int(b['bb'][1]):<3} {n:>4}w  {text if full else text[:90]}")
