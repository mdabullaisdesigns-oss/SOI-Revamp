#!/usr/bin/env python3
"""
Survey of every magazine PDF: does it have a text layer (or need OCR), and does
it use the magazine's standard type system that structure.py relies on?

Usage: python3 pipeline/survey.py <folder with PDFs> <out.csv> [--ocr-check FILE.pdf OUT.md]
  --ocr-check reads one PDF twice (text layer and OCR) and reports how closely
  the OCR reading agrees, page by page - a measure of what OCR would cost in
  accuracy if a scanned issue ever turns up.
"""
import csv, os, sys, collections, json, subprocess, tempfile
import pymupdf


def survey_one(path):
    doc = pymupdf.open(path)
    words = no_text = titles = body = total_lines = 0
    for page in doc:
        d = page.get_text("dict")
        pw = 0
        for b in d["blocks"]:
            for ln in b.get("lines", []):
                for s in ln["spans"]:
                    n = len(s["text"].split())
                    pw += n
                    if "nevis" in s["font"] and 15.5 <= s["size"] <= 16.5 and n:
                        titles += 1
                    if "OpenSans" in s["font"] and 9.6 <= s["size"] <= 10.6:
                        body += n
        words += pw
        if pw < 25 and any((r.width * r.height) > 0.5 * page.rect.width * page.rect.height
                           for img in page.get_images(full=True) for r in page.get_image_rects(img[0])):
            no_text += 1
    return {"file": os.path.basename(path), "pages": len(doc), "words": words, "pages_needing_ocr": no_text,
            "standard_titles": titles, "standard_body_share": round(body / words, 2) if words else 0,
            "route": "ocr" if no_text > 0.3 * len(doc) else ("rules" if titles >= 8 and body > 0.5 * words else "check")}


def main():
    folder, out = sys.argv[1], sys.argv[2]
    rows = []
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if f.lower().endswith(".pdf"):
                try:
                    rows.append(survey_one(os.path.join(root, f)))
                except Exception as e:
                    rows.append({"file": f, "pages": 0, "words": 0, "pages_needing_ocr": 0, "standard_titles": 0,
                                 "standard_body_share": 0, "route": f"error: {e}"})
    rows.sort(key=lambda r: r["file"].lower())
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(collections.Counter(r["route"] for r in rows))

    if "--ocr-check" in sys.argv:
        pdf, md = sys.argv[sys.argv.index("--ocr-check") + 1], sys.argv[sys.argv.index("--ocr-check") + 2]
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import check
        with tempfile.TemporaryDirectory() as td:
            here = os.path.dirname(os.path.abspath(__file__))
            for name, flag in (("text", []), ("ocr", ["--force-ocr"])):
                subprocess.run([sys.executable, os.path.join(here, "extract.py"), name, pdf, "--out", td] + flag, check=True)
            load = lambda n: json.load(open(os.path.join(td, n, "raw", "pages.json"), encoding="utf-8"))
            lines = ["# OCR check", "", f"`{os.path.basename(pdf)}` read twice: from its text layer and by Tesseract OCR (300 dpi).", "",
                     "| Page | Words (text layer) | Words OCR also found, in order | Agreement |", "|---|---|---|---|"]
            tot = hit = 0
            for a, b in zip(load("text"), load("ocr")):
                wa = check.norm(" ".join(l["t"] for bl in a["blocks"] for l in bl["lines"]))
                wb = check.norm(" ".join(l["t"] for bl in b["blocks"] for l in bl["lines"]))
                if len(wa) < 40:
                    continue
                h, _, _ = check.match(wa, wb)
                tot, hit = tot + len(wa), hit + h
                lines.append(f"| {a['n']} | {len(wa)} | {h} | {100 * h / len(wa):.1f}% |")
            lines += ["", f"**Overall: {100 * hit / max(tot, 1):.2f}% of {tot:,} words.**"]
            open(md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            print(lines[-1])


if __name__ == "__main__":
    main()
