#!/usr/bin/env python3
"""Make app/www – the files packed inside the Android/iOS app.

    python3 site/build_site.py      # the website (dist/)
    python3 app/build_app.py        # dist/ + app/src/ -> app/www/

The app is one page (src/shell.html + core.js + screens.js + app.css) that never reloads. From the website it
takes only data: the list of issues, the newest issue pages (app-config.json: bundle_latest), every small
cover, the quotes, the search index, the fonts and the logo files of site/brand/. Every other issue is fetched
once from the website (app-config.json: remote) and then kept on the phone; audio is streamed, or saved with
the issue when the reader asks for it. Audio is never packed in the app.
"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST, WWW, SRC = os.path.join(ROOT, "dist"), os.path.join(HERE, "www"), os.path.join(HERE, "src")
FONT_DIR = os.path.join(HERE, "node_modules", "@fontsource", "plus-jakarta-sans", "files")
FACES = [(400, "normal"), (400, "italic"), (500, "normal"), (600, "normal"), (700, "normal"), (800, "normal")]
BRAND = ["Peogen-logo.png", "Spirit-of-Islam-Logo.png", "Slogan-Line.png"]       # only the logo files of site/brand/


def main():
    cfg = json.load(open(os.path.join(HERE, "app-config.json")))
    if not os.path.exists(os.path.join(DIST, "issues.json")):
        sys.exit("dist/ is missing – run: python3 site/build_site.py")
    issues = json.load(open(os.path.join(DIST, "issues.json")))["issues"]
    bundled = [i["slug"] for i in issues[-int(cfg.get("bundle_latest", 3)):]]
    if not all(os.path.exists(os.path.join(FONT_DIR, f"plus-jakarta-sans-latin-{w}-{s}.woff2")) for w, s in FACES):
        sys.exit("Plus Jakarta Sans is missing – run `npm install` in app/ first")

    shutil.rmtree(WWW, ignore_errors=True)
    A = os.path.join(WWW, "assets")
    os.makedirs(os.path.join(A, "fonts")); os.makedirs(os.path.join(A, "brand")); os.makedirs(os.path.join(A, "covers"))
    shutil.copy(os.path.join(DIST, "issues.json"), WWW)
    shutil.copy(os.path.join(DIST, "assets", "quotes.json"), A)
    shutil.copytree(os.path.join(DIST, "pagefind"), os.path.join(WWW, "pagefind"))
    for slug in bundled:
        os.makedirs(os.path.join(WWW, "issues", slug))
        shutil.copy(os.path.join(DIST, "issues", slug, "index.html"), os.path.join(WWW, "issues", slug))
    no_cover = []
    for i in issues:                       # small cover of every issue; the large one only for the packed issues
        for f in [i["slug"] + ".webp"] + ([i["slug"] + "@2x.webp"] if i["slug"] in bundled else []):
            p = os.path.join(DIST, "assets", "covers", f)
            if os.path.exists(p): shutil.copy(p, os.path.join(A, "covers"))
            elif "@" not in f: no_cover.append(i["slug"])
    for f in BRAND:
        shutil.copy(os.path.join(ROOT, "site", "brand", f), os.path.join(A, "brand"))
    for f in os.listdir(os.path.join(DIST, "assets", "fonts")):
        if f.endswith(".woff2"): shutil.copy(os.path.join(DIST, "assets", "fonts", f), os.path.join(A, "fonts"))
    faces = ""
    for w, s in FACES:
        name = f"plus-jakarta-sans-latin-{w}-{s}.woff2"
        shutil.copy(os.path.join(FONT_DIR, name), os.path.join(A, "fonts", name))
        faces += (f'@font-face {{ font-family: "Plus Jakarta Sans"; font-style: {s}; font-weight: {w}; font-display: swap; '
                  f'src: url("/assets/fonts/{name}") format("woff2"); }}\n')
    open(os.path.join(A, "app.css"), "w", encoding="utf-8").write(faces + open(os.path.join(SRC, "app.css"), encoding="utf-8").read())
    for f in ("core.js", "screens.js"):
        shutil.copy(os.path.join(SRC, f), os.path.join(A, f))
    shutil.copy(os.path.join(SRC, "shell.html"), os.path.join(WWW, "index.html"))
    json.dump({"remote": cfg["remote"].rstrip("/"), "share": cfg.get("share", cfg["remote"]).rstrip("/"), "bundled": bundled},
              open(os.path.join(A, "app-config.json"), "w"))

    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(WWW) for f in fs)
    if no_cover: print("no cover picture:", " ".join(no_cover))
    print(f"app/www ready: {len(bundled)} issues packed ({', '.join(bundled)}), {len(issues)} covers, {size/1048576:.1f} MB, "
          f"other issues from {cfg['remote']}")


if __name__ == "__main__":
    main()
