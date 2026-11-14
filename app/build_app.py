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
from build_site import page  # same header/footer as the website

FONT_DIR = os.path.join(HERE, "node_modules", "@fontsource", "plus-jakarta-sans", "files")
FACES = [(400, "normal"), (400, "italic"), (500, "normal"), (600, "normal"), (700, "normal"), (800, "normal")]
INJECT = '<link rel="stylesheet" href="/assets/app.css">\n<script src="/assets/app.js"></script>\n</head>'


def prep(html, fonts):
    if fonts:
        html = re.sub(r'<link[^>]+fonts\.(?:googleapis|gstatic)\.com[^>]*>\s*', "", html)
    html = html.replace('content="width=device-width, initial-scale=1"',
                        'content="width=device-width, initial-scale=1, viewport-fit=cover"', 1)
    assert "</head>" in html
    return html.replace("</head>", INJECT, 1)


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
        if os.path.abspath(d) == os.path.join(DIST, "issues"):
            return [n for n in names if n not in keep]
        return [n for n in names if n in ("_headers", "robots.txt")]
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
    write("reader.html", prep(page("Spirit of Islam", '<div class="soi-app-page" id="soi-app-reader"><h1>Opening the issue…</h1></div>'), fonts))
    write("saved.html", prep(page("Saved issues – Spirit of Islam", """<div class="soi-app-page" id="soi-app-saved">
<h1>Saved issues</h1>
<p>Every issue you open is kept on this phone, so you can read it again without internet. Audio needs a connection.</p>
<p class="soi-app-stat" role="status" aria-live="polite">&nbsp;</p>
<button type="button" class="soi-app-all" hidden>Save all remaining issues</button>
<ul class="soi-app-list"></ul>
</div>"""), fonts))

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
    shutil.copy(os.path.join(HERE, "src", "app.js"), os.path.join(WWW, "assets", "app.js"))
    art = os.path.join(HERE, "resources", "app-art.png")
    if os.path.exists(art):
        shutil.copy(art, os.path.join(WWW, "assets", "app-art.png"))
    write("assets/app-config.json", json.dumps({"remote": cfg["remote"].rstrip("/"), "bundled": bundled, "fonts": fonts}))

    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(WWW) for f in fs)
    print(f"app/www ready: {n} pages, {len(bundled)} issues packed ({', '.join(bundled)}), {size/1048576:.1f} MB, "
          f"fonts {'packed' if fonts else 'from Google'}, other issues from {cfg['remote']}")


if __name__ == "__main__":
    main()
