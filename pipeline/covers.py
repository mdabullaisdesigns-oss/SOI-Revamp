#!/usr/bin/env python3
"""Cover picture of an issue = page 1 of its PDF.   covers.py <slug> <pdf>  ->  site/covers/<slug>.webp
(600 px wide for cards and menus, and <slug>@2x.webp 1100 px for the large cover in the app / hero)."""
import os, sys
import fitz
from PIL import Image

def main(slug, pdf):
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site", "covers")
    os.makedirs(out, exist_ok=True)
    page = fitz.open(pdf)[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(1200 / page.rect.width, 1200 / page.rect.width), alpha=False)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    for name, w, q in ((f"{slug}.webp", 600, 78), (f"{slug}@2x.webp", 1100, 76)):
        im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(os.path.join(out, name), "WEBP", quality=q, method=6)
    print(slug, im.size)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
