#!/usr/bin/env python3
"""Turn issue PDFs into page pictures (run in GitHub Actions, where the PDFs can be downloaded from R2).

  python3 scripts/pdf_pages.py back  <slug|all>   -> site/covers/back/<slug>.webp  (the back cover)
  python3 scripts/pdf_pages.py pages <slug ...>   -> out-pages/<slug>/p001.webp ... (+ issues/<slug>/pages.json)

The promotional "We asked ChatGPT about CPS International" page at the end of each PDF is
never used (CLAUDE.md): any page whose text mentions ChatGPT is skipped.
Needs: poppler-utils (pdftoppm, pdftotext, pdfinfo), Pillow, aws cli with R2 credentials.
"""
import csv, glob, json, os, re, subprocess, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRA = {"2026-11": "SOI-NOV-DEC-26-Magazine-file.pdf"}


def r2_key(pdf):
    for r in csv.DictReader(open(os.path.join(ROOT, "inventory", "inventory-pdfs.csv"), encoding="utf-8")):
        if r["file"] == pdf:
            return "pdfs/" + (r["url"].split("/uploads/")[-1].split("/")[0] if "/uploads/" in r["url"] else "other") + "/" + pdf


def pdf_of(slug):
    p = os.path.join(ROOT, "issues", slug, "issue.json")
    return EXTRA.get(slug) or (json.load(open(p, encoding="utf-8")).get("pdf") if os.path.exists(p) else None)


def fetch(slug):
    pdf = pdf_of(slug); key = pdf and r2_key(pdf)
    if not key:
        print(f"{slug}: no PDF known"); return None
    dst = f"/tmp/pdf/{slug}.pdf"; os.makedirs("/tmp/pdf", exist_ok=True)
    if not os.path.exists(dst):
        subprocess.run(["aws", "s3", "cp", f"s3://{os.environ['R2_BUCKET']}/{key}", dst, "--endpoint-url", os.environ["R2_ENDPOINT"], "--only-show-errors"], check=True)
    return dst


def npages(pdf):
    return int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))


def promo(pdf, n):
    t = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), pdf, "-"], capture_output=True, text=True).stdout
    return bool(re.search(r"chat\s*gpt", t, re.I))


def render(pdf, n, out, width):
    base = out[:-5]
    subprocess.run(["pdftoppm", "-f", str(n), "-l", str(n), "-scale-to-x", str(width), "-scale-to-y", "-1", "-jpeg", "-jpegopt", "quality=92", "-singlefile", pdf, base], check=True)
    Image.open(base + ".jpg").convert("RGB").save(out, "WEBP", quality=80, method=6); os.remove(base + ".jpg")


def main():
    mode, args = sys.argv[1], sys.argv[2:]
    slugs = sorted(d for d in os.listdir(os.path.join(ROOT, "issues")) if pdf_of(d)) if args == ["all"] else args
    for slug in slugs:
        pdf = fetch(slug)
        if not pdf:
            continue
        n = npages(pdf)
        keep = [k for k in range(1, n + 1) if not (k > n - 3 and promo(pdf, k))]
        if mode == "back":
            os.makedirs(os.path.join(ROOT, "site/covers/back"), exist_ok=True)
            render(pdf, keep[-1], os.path.join(ROOT, f"site/covers/back/{slug}.webp"), 600)
            print(f"{slug}: back cover = page {keep[-1]} of {n}" + (" (promotional page skipped)" if keep[-1] != n else ""))
        else:
            d = f"out-pages/{slug}"; os.makedirs(d, exist_ok=True)
            for i, k in enumerate(keep, 1):
                render(pdf, k, f"{d}/p{i:03d}.webp", 1400)
            w, h = Image.open(f"{d}/p001.webp").size
            json.dump({"count": len(keep), "w": w, "h": h, "base": f"/media/pages/{slug}/"}, open(os.path.join(ROOT, "issues", slug, "pages.json"), "w"))
            print(f"{slug}: {len(keep)} pages (of {n})")


if __name__ == "__main__":
    main()
