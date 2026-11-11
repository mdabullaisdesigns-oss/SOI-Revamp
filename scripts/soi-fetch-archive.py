#!/usr/bin/env python3
"""
SOI archive fetcher: lists every magazine PDF, audio file and issue page on
spiritofislam.co.in through the public WordPress REST API, writes inventory
CSVs, and downloads the PDFs.

Run on your Mac from the VS Code terminal (no installs needed):
    python3 soi-fetch-archive.py              # inventory + download PDFs
    python3 soi-fetch-archive.py --list-only  # inventory only, no downloads
    python3 soi-fetch-archive.py --audio      # also download the MP3s

Output (next to this script):
    soi-archive/pdfs/<year>/<file>.pdf
    soi-archive/audio/<year>/<file>.mp3   (only with --audio)
    soi-archive/inventory-pdfs.csv
    soi-archive/inventory-audio.csv
    soi-archive/inventory-pages.csv
Re-running skips files that are already downloaded at full size.
"""
import csv, html, json, os, sys, time, urllib.parse, urllib.request

SITE = "https://spiritofislam.co.in"
OUT = os.environ.get("SOI_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "soi-archive")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) SOI-archive-fetcher"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r), r.headers


def list_all(endpoint, params):
    items, page = [], 1
    while True:
        q = dict(params, per_page=100, page=page)
        url = f"{SITE}/wp-json/wp/v2/{endpoint}?{urllib.parse.urlencode(q)}"
        try:
            data, headers = get(url)
        except urllib.error.HTTPError as e:
            if e.code == 400 and page > 1:  # past the last page
                break
            raise
        items += data
        total_pages = int(headers.get("X-WP-TotalPages", "1"))
        print(f"  {endpoint}: page {page}/{total_pages} ({len(items)} items)")
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.5)
    return items


def media_rows(items):
    rows = []
    for m in items:
        url = m.get("source_url", "")
        details = m.get("media_details") or {}
        rows.append({
            "id": m["id"],
            "date": m.get("date", "")[:10],
            "title": html.unescape(m.get("title", {}).get("rendered", "")),
            "file": os.path.basename(urllib.parse.urlparse(url).path),
            "size_mb": round(details.get("filesize", 0) / 1e6, 2) if details.get("filesize") else "",
            "attached_to_page": m.get("post") or "",
            "url": url,
        })
    return sorted(rows, key=lambda r: r["date"])


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path} ({len(rows)} rows)")


def download(rows, folder):
    for i, r in enumerate(rows, 1):
        year = r["url"].split("/uploads/")[-1].split("/")[0] if "/uploads/" in r["url"] else "other"
        dest_dir = os.path.join(OUT, folder, year)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, r["file"])
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue
        print(f"  [{i}/{len(rows)}] {r['file']}")
        try:
            req = urllib.request.Request(r["url"], headers=UA)
            with urllib.request.urlopen(req, timeout=300) as resp, open(dest + ".part", "wb") as f:
                while chunk := resp.read(1 << 20):
                    f.write(chunk)
            os.replace(dest + ".part", dest)
        except Exception as e:
            print(f"    FAILED: {e}")
        time.sleep(0.3)


def main():
    os.makedirs(OUT, exist_ok=True)
    print("Listing PDFs…")
    pdfs = media_rows(list_all("media", {"mime_type": "application/pdf"}))
    write_csv(os.path.join(OUT, "inventory-pdfs.csv"), pdfs)

    print("Listing audio…")
    audio = media_rows(list_all("media", {"media_type": "audio"}))
    write_csv(os.path.join(OUT, "inventory-audio.csv"), audio)

    print("Listing issue pages…")
    pages = list_all("pages", {"search": "ISSUE", "_fields": "id,date,link,title"})
    page_rows = sorted(
        ({"id": p["id"], "date": p["date"][:10],
          "title": html.unescape(p["title"]["rendered"]), "link": p["link"]}
         for p in pages if html.unescape(p["title"]["rendered"]).upper().startswith("ISSUE")),
        key=lambda r: r["date"])
    write_csv(os.path.join(OUT, "inventory-pages.csv"), page_rows)

    if "--list-only" not in sys.argv:
        print("Downloading PDFs…")
        download(pdfs, "pdfs")
        if "--audio" in sys.argv:
            print("Downloading audio…")
            download(audio, "audio")
    print("Done.")


if __name__ == "__main__":
    main()
