#!/usr/bin/env python3
"""
Stage 1 - extract.  Magazine PDF -> issues/<slug>/raw/

  pages.json      every text line of every page with its position, font size and
                  style (used to rebuild the articles), plus link annotations
  pdftotext.txt   an independent second reading of the same PDF (poppler), used
                  only by the word-match check
  meta.json       page count, which pages needed OCR, file hash

Pages without a usable text layer (scanned issues) are read with Tesseract OCR.
Page pictures (for visual checks) are written to --pages-dir when given; they
are never committed to main.

Usage:  python3 pipeline/extract.py <slug> <file.pdf> [--pages-dir DIR] [--out issues]
Needs:  pip install pymupdf ; poppler-utils ; tesseract-ocr (only for scans)
"""
import argparse, hashlib, json, os, subprocess, sys, tempfile
import pymupdf

MIN_WORDS_FOR_TEXT_PAGE = 25      # fewer words than this + a big picture = scanned page
OCR_DPI = 300


def r1(x):
    return round(float(x), 1)


def text_page(page):
    """Lines from the PDF text layer."""
    d = page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_LIGATURES * 0 | pymupdf.TEXT_DEHYPHENATE * 0)
    blocks = []
    for b in d["blocks"]:
        if b.get("type") != 0:
            continue
        lines = []
        for ln in b["lines"]:
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = "".join(s["text"] for s in ln["spans"]).strip()
            big = max(spans, key=lambda s: len(s["text"]))
            runs = []
            for s in ln["spans"]:      # keep bold / italic runs so emphasis survives
                st = ("b" if s["flags"] & 16 or "Bold" in s["font"] else "") + \
                     ("i" if s["flags"] & 2 or "Italic" in s["font"] or "Oblique" in s["font"] else "")
                if runs and runs[-1][0] == st:
                    runs[-1][1] += s["text"]
                else:
                    runs.append([st, s["text"]])
            line = {
                "t": text,
                "bb": [r1(v) for v in ln["bbox"]],
                "sz": r1(big["size"]),
                "f": big["font"],
                "c": "%06x" % big["color"],
            }
            if any(st for st, _ in runs):
                line["runs"] = runs
            if ln.get("dir") and abs(ln["dir"][0]) < 0.9:
                line["rot"] = 1                    # rotated text (page-edge labels)
            lines.append(line)
        if lines:
            blocks.append({"bb": [r1(v) for v in b["bbox"]], "lines": lines})
    return blocks


def ocr_page(page):
    """Lines from Tesseract, in PDF points so they look like text-layer lines."""
    pix = page.get_pixmap(dpi=OCR_DPI, colorspace=pymupdf.csGRAY)
    k = 72.0 / OCR_DPI
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, "p.png")
        pix.save(png)
        tsv = subprocess.run(["tesseract", png, "stdout", "--psm", "3", "-l", "eng", "tsv"],
                             capture_output=True, text=True, check=True).stdout
    groups, order = {}, []
    for row in tsv.splitlines()[1:]:
        c = row.split("\t")
        if len(c) < 12 or c[0] != "5" or not c[11].strip():
            continue
        key = (int(c[2]), int(c[3]), int(c[4]))           # block, paragraph, line
        x, y, w, h, conf = int(c[6]), int(c[7]), int(c[8]), int(c[9]), float(c[10])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append((c[11], x, y, x + w, y + h, conf))
    blocks, cur_key, cur = [], None, None
    for key in order:
        ws = groups[key]
        bb = [min(w[1] for w in ws) * k, min(w[2] for w in ws) * k, max(w[3] for w in ws) * k, max(w[4] for w in ws) * k]
        line = {"t": " ".join(w[0] for w in ws), "bb": [r1(v) for v in bb],
                "sz": r1((bb[3] - bb[1]) * 0.72), "f": "ocr", "c": "000000",
                "conf": round(sum(w[5] for w in ws) / len(ws))}
        if key[:2] != cur_key:                             # new block or paragraph
            cur = {"bb": list(line["bb"]), "lines": []}
            blocks.append(cur)
            cur_key = key[:2]
        cur["lines"].append(line)
        cur["bb"] = [min(cur["bb"][0], line["bb"][0]), min(cur["bb"][1], line["bb"][1]),
                     max(cur["bb"][2], line["bb"][2]), max(cur["bb"][3], line["bb"][3])]
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("pdf")
    ap.add_argument("--out", default="issues")
    ap.add_argument("--pages-dir")
    ap.add_argument("--force-ocr", action="store_true")
    a = ap.parse_args()

    raw = os.path.join(a.out, a.slug, "raw")
    os.makedirs(raw, exist_ok=True)
    doc = pymupdf.open(a.pdf)
    pages, ocr_pages = [], []
    for i, page in enumerate(doc, 1):
        blocks = text_page(page)
        words = sum(len(l["t"].split()) for b in blocks for l in b["lines"])
        big_image = any(
            (r.width * r.height) > 0.5 * page.rect.width * page.rect.height
            for img in page.get_images(full=True) for r in page.get_image_rects(img[0]))
        source = "pdf"
        if a.force_ocr or (words < MIN_WORDS_FOR_TEXT_PAGE and big_image):
            try:
                ocr = ocr_page(page)
                if sum(len(l["t"].split()) for b in ocr for l in b["lines"]) > words:
                    blocks, source = ocr, "ocr"
                    ocr_pages.append(i)
            except Exception as e:                          # keep going, record it
                print(f"  page {i}: OCR failed: {e}", file=sys.stderr)
        for n, b in enumerate(blocks):
            b["id"] = f"p{i}b{n}"
        links = [{"uri": l["uri"], "bb": [r1(v) for v in l["from"]]}
                 for l in page.get_links() if l.get("uri")]
        pages.append({"n": i, "w": r1(page.rect.width), "h": r1(page.rect.height),
                      "src": source, "words": sum(len(l["t"].split()) for b in blocks for l in b["lines"]),
                      "blocks": blocks, "links": links})
        if a.pages_dir:
            os.makedirs(os.path.join(a.pages_dir, a.slug), exist_ok=True)
            page.get_pixmap(dpi=80).pil_save(
                os.path.join(a.pages_dir, a.slug, f"p{i:03d}.jpg"), quality=55, optimize=True)

    with open(os.path.join(raw, "pages.json"), "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, separators=(",", ":"))

    # independent second reading for the word-match check
    try:
        txt = subprocess.run(["pdftotext", "-enc", "UTF-8", a.pdf, "-"],
                             capture_output=True, text=True, check=True).stdout
    except Exception as e:
        txt = ""
        print(f"  pdftotext failed: {e}", file=sys.stderr)
    with open(os.path.join(raw, "pdftotext.txt"), "w", encoding="utf-8") as f:
        f.write(txt)

    meta = {"slug": a.slug, "pdf": os.path.basename(a.pdf), "pages": len(pages),
            "ocr_pages": ocr_pages, "words": sum(p["words"] for p in pages),
            "sha256": hashlib.sha256(open(a.pdf, "rb").read()).hexdigest(),
            "bytes": os.path.getsize(a.pdf)}
    with open(os.path.join(raw, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
