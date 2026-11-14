#!/usr/bin/env python3
"""Make app/www – the files packed inside the Android/iOS app.

    python3 site/build_site.py      # the website (dist/)
    python3 app/build_app.py        # dist/ -> app/www/

What goes inside the app: home, archive, search (with its index), quotes, the fonts, and the newest
issues (app-config.json: bundle_latest). Every other issue is fetched once from the website
(app-config.json: remote) and then kept on the phone. Audio is streamed, never packed in the app.
"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST, WWW = os.path.join(ROOT, "dist"), os.path.join(HERE, "www")
sys.path.insert(0, os.path.join(ROOT, "site"))

FONT_DIR = os.path.join(HERE, "node_modules", "@fontsource", "plus-jakarta-sans", "files")
FACES = [(400, "normal"), (400, "italic"), (500, "normal"), (600, "normal"), (700, "normal"), (800, "normal")]
INJECT = '<link rel="stylesheet" href="/assets/app.css">\n<script src="/assets/app.js"></script>\n</head>'
SCREENS = {"index.html": ("home", "Spirit of Islam"), "search.html": ("search", "Search"), "saved.html": ("saved", "Saved"),
           "profile.html": ("profile", "Profile"), "gems.html": ("gems", "SOI Gems")}


def prep(html, fonts):
    """A website page, made ready for the app: fonts from inside the app, notch-safe, app layer added."""
    if fonts:
        html = re.sub(r'<link[^>]+fonts\.(?:googleapis|gstatic)\.com[^>]*>\s*', "", html)
    html = html.replace('<html lang="en">', '<html lang="en" class="soi-app">', 1)
    html = html.replace('content="width=device-width, initial-scale=1"',
                        'content="width=device-width, initial-scale=1, viewport-fit=cover"', 1)
    assert "</head>" in html
    return html.replace("</head>", INJECT, 1)


def screen(name, title, extra=""):
    """One of the app's own screens (Home, Search, Saved, Profile, Gems); screens.js draws it."""
    return f"""<!doctype html>
<html lang="en" class="soi-app">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} – Spirit of Islam</title>
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/site.js"></script>
<link rel="stylesheet" href="/assets/app.css">
<script src="/assets/app.js"></script>
<script src="/assets/screens.js"></script>
</head>
<body data-screen="{name}">
<main class="soi-app-screen" id="soi-app-screen">{extra}</main>
</body>
</html>
"""


def main():
    cfg = json.load(open(os.path.join(HERE, "app-config.json")))
    if not os.path.exists(os.path.join(DIST, "issues.json")):
        sys.exit("dist/ is missing – run: python3 site/build_site.py")
    issues = json.load(open(os.path.join(DIST, "issues.json")))["issues"]
    bundled = [i["slug"] for i in issues[-int(cfg.get("bundle_latest", 3)):]]
    fonts = all(os.path.exists(os.path.join(FONT_DIR, f"plus-jakarta-sans-latin-{w}-{s}.woff2")) for w, s in FACES)

    shutil.rmtree(WWW, ignore_errors=True)
    keep = set(bundled)
    def skip(d, names):
        d = os.path.abspath(d)
        if d == os.path.join(DIST, "issues"):
            return [n for n in names if n not in keep]
        if d == os.path.join(DIST, "assets", "covers"):       # large covers only for the issues packed in the app
            return [n for n in names if "@2x" in n and n.split("@")[0] not in keep]
        if d == DIST:                                          # the app has its own Home, Search, Saved and Profile
            return [n for n in names if n in ("_headers", "robots.txt", "index.html", "search", "saved", "signin", "404.html")]
        return []
    shutil.copytree(DIST, WWW, ignore=skip)

    n = 0
    for d, _, files in os.walk(WWW):
        for f in files:
            if f.endswith(".html"):
                p = os.path.join(d, f)
                html = prep(open(p, encoding="utf-8").read(), fonts)
                open(p, "w", encoding="utf-8").write(html); n += 1

    def write(rel, text):
        open(os.path.join(WWW, rel), "w", encoding="utf-8").write(text)
    for f, (name, title) in SCREENS.items():
        write(f, screen(name, title)); n += 1
    write("reader.html", screen("", "Spirit of Islam", '<div class="soi-app-page" id="soi-app-reader"><h1>Opening the issue…</h1></div>').replace(' data-screen=""', "")
          .replace('<script src="/assets/screens.js"></script>\n', ""))

    css = open(os.path.join(HERE, "src", "app.css"), encoding="utf-8").read()
    if fonts:
        os.makedirs(os.path.join(WWW, "assets", "fonts"), exist_ok=True)
        faces = ""
        for w, s in FACES:
            name = f"plus-jakarta-sans-latin-{w}-{s}.woff2"
            shutil.copy(os.path.join(FONT_DIR, name), os.path.join(WWW, "assets", "fonts", name))
            faces += (f'@font-face {{ font-family: "Plus Jakarta Sans"; font-style: {s}; font-weight: {w}; font-display: swap; '
                      f'src: url("/assets/fonts/{name}") format("woff2"); }}\n')
        css = faces + css
    else:
        print("note: run `npm install` in app/ first to pack Plus Jakarta Sans inside the app (using Google Fonts links for now)")
    write("assets/app.css", css)
    for f in ("app.js", "screens.js"):
        shutil.copy(os.path.join(HERE, "src", f), os.path.join(WWW, "assets", f))
    write("assets/app-config.json", json.dumps({"remote": cfg["remote"].rstrip("/"), "share": cfg.get("share", cfg["remote"]).rstrip("/"),
                                                "bundled": bundled, "fonts": fonts}))

    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(WWW) for f in fs)
    print(f"app/www ready: {n} pages, {len(bundled)} issues packed ({', '.join(bundled)}), {size/1048576:.1f} MB, "
          f"fonts {'packed' if fonts else 'from Google'}, other issues from {cfg['remote']}")


if __name__ == "__main__":
    main()
