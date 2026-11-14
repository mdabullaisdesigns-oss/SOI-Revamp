#!/usr/bin/env python3
"""
Static website generator.

  issues/<slug>/issue.json + SOI-<slug>-complete.html   (made by the pipeline)
  -> dist/                    plain HTML/CSS/JS, ready for Cloudflare Pages
       index.html             home: latest issue, search, years
       archive/               every issue, by year
       issues/<slug>/         one page per issue = the approved e-version block
       search/                Pagefind search across every article of every issue
       pagefind/              the search index (one record per article, linking to
                              the article's own tab: /issues/<slug>/#soi-<article>)

Usage: python3 site/build_site.py [--out dist] [--base https://example.org]
Needs: pip install "pagefind[bin]"
"""
import asyncio, csv, html, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
OUT = os.path.join(ROOT, arg("--out", "dist"))
esc = html.escape
MONTHS = "January February March April May June July August September October November December".split()
TYPE_LABEL = {"article": "Articles", "qa": "Questions & Answers", "scripture": "The Word of God",
              "newsletter": "CPS Newsletter", "children": "Children’s Corner", "glossary": "Glossary"}


def load_issues():
    out = []
    for slug in sorted(os.listdir(os.path.join(ROOT, "issues"))):
        base = os.path.join(ROOT, "issues", slug)
        block = os.path.join(base, f"SOI-{slug}-complete.html")
        rt = os.path.join(base, "route.txt")
        if os.path.exists(rt) and open(rt).read().startswith("skip"):
            continue
        if not (os.path.exists(os.path.join(base, "issue.json")) and os.path.exists(block)):
            continue
        i = json.load(open(os.path.join(base, "issue.json"), encoding="utf-8"))
        audio = json.load(open(os.path.join(base, "audio.json"), encoding="utf-8")) if os.path.exists(os.path.join(base, "audio.json")) else {}
        arts = []
        for a in i["articles"]:
            text = " ".join("".join(r[1] for r in x["runs"]) for x in a["items"])
            arts.append({"id": a["id"], "title": a["title"], "kicker": a.get("kicker", ""), "author": a.get("author", ""),
                         "type": a.get("type", "article"), "text": re.sub(r"\s+", " ", text).strip(), "words": a["words"],
                         "audio": a["id"] in audio and "times" in audio[a["id"]] and not audio[a["id"]].get("flag")})
        y, m = int(slug[:4]), int(slug[5:7])
        out.append({"slug": slug, "year": y, "month": m, "number": i.get("number"),
                    "period": i.get("period") or f"{MONTHS[m - 1]} {y}", "block": open(block, encoding="utf-8").read(),
                    "articles": arts, "quiz": os.path.exists(os.path.join(base, "quiz.json"))})
    # Issue 133 is the hand-finished reference build: its block is used as it is
    ref = os.path.join(ROOT, "reference", "issue-133-live.html")
    if os.path.exists(ref) and not any(x["slug"] == "2026-11" for x in out):
        block = open(ref, encoding="utf-8").read()
        arts = []
        for m in re.finditer(r'<section class="ev-item" id="soi-([\w-]+)".*?</section>', block, re.S):
            sec = m.group(0)
            title = re.sub(r"<[^>]+>", "", re.search(r'class="ev-tab-title">(.*?)</span>\s*</span>', sec, re.S).group(1)).strip()
            kick = re.search(r'class="ev-kicker">(.*?)</span>', sec, re.S)
            body = sec[sec.index('class="ev-body"'):] if 'class="ev-body"' in sec else sec
            text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style|svg).*?</\1>", " ", body, flags=re.S)))).strip()
            arts.append({"id": m.group(1), "title": html.unescape(title), "kicker": html.unescape(re.sub(r"<[^>]+>", "", kick.group(1))) if kick else "",
                         "author": "", "type": "article", "text": text, "words": len(text.split()), "audio": "ev-player" in sec})
        out.append({"slug": "2026-11", "year": 2026, "month": 11, "number": 133, "period": "November–December 2026",
                    "block": block, "articles": arts, "quiz": True})
    out.sort(key=lambda x: x["slug"])
    return out


def old_links(issues):
    """WordPress page id -> new address, so links shared over 13 years keep working (/?page_id=659)."""
    have = {i["slug"] for i in issues}
    m = {}
    p = os.path.join(ROOT, "inventory", "inventory-pages.csv")
    if not os.path.exists(p):
        return m
    for r in csv.DictReader(open(p, encoding="utf-8")):
        t = r["title"]
        y = re.search(r"20\d\d", t)
        mo = next((k + 1 for w in re.findall(r"[A-Za-z]+", t) for k, n in enumerate(MONTHS)
                   if w.upper() != "ISSUE" and len(w) >= 3 and n.lower().startswith(w.lower()[:3])), None)
        if y and mo and f"{y.group(0)}-{mo:02d}" in have:
            m[r["id"]] = f"/issues/{y.group(0)}-{mo:02d}/"
    return m


MENU = json.load(open(os.path.join(HERE, "menu.json"), encoding="utf-8"))
SHORT = {"January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr", "June": "Jun", "July": "Jul", "August": "Aug",
         "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"}
ICON_SEARCH = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>'
ICON_SAVED = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>'
LATEST = {"slug": ""}            # filled in by build()


def short_period(p):
    """November–December 2026 -> Nov–Dec 2026 (cards and menus)."""
    return re.sub("|".join(SHORT), lambda m: SHORT[m.group(0)], p)


def ext(href):
    return ' target="_blank" rel="noopener"' if href.startswith("http") else ""


def sub(items):
    return "".join(f'<li><a href="{esc(i["href"])}"{ext(i["href"])}>{esc(i["label"])}</a></li>' for i in items)


def photo(key, cls=""):
    """A photo slot. Until a photo is approved for it (menu.json: photos) it shows a plain drawn landscape."""
    f = MENU.get("photos", {}).get(key)
    if f:
        return f'<span class="soi-ph {cls}"><img src="/assets/photos/{esc(f)}" alt="" loading="lazy" decoding="async"></span>'
    return f'<span class="soi-ph soi-ph-wait {cls}" aria-hidden="true"></span>'


def cover(i, big=False):
    f = f'{i["slug"]}{"@2x" if big else ""}.webp'
    img = (f'<img src="/assets/covers/{f}" alt="" loading="lazy" decoding="async" width="600" height="850">'
           if os.path.exists(os.path.join(HERE, "covers", f)) else "")
    return (f'<span class="soi-cover"><span class="soi-cover-fb" aria-hidden="true"><b>Spirit of Islam</b><i>{esc(i["period"])}</i></span>{img}</span>')


def page(title, body, desc="", cls="", head="", current=""):
    cur = lambda k: ' aria-current="page"' if k == current else ""
    c = MENU["contact"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or 'Spirit of Islam – a magazine for the journey of life. Read every issue since 2013, with read-along audio and search.')}">
<link rel="icon" href="/assets/brand/Peogen-logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/site.js"></script>
{head}
</head>
<body class="{cls}">
<a class="soi-skip" href="#soi-main">Skip to content</a>
<header class="soi-hdr">
  <a class="soi-hdr-in" href="/" aria-label="Spirit of Islam – home">
    <img class="soi-hdr-bird" src="/assets/brand/Peogen-logo.png" alt="" width="470" height="453">
    <span class="soi-hdr-words">
      <img src="/assets/brand/Spirit-of-Islam-Logo.png" alt="Spirit of Islam" width="1600" height="164">
      <img src="/assets/brand/Slogan-Line.png" alt="Towards Global Peace &amp; Spiritual Living" width="1600" height="138">
    </span>
  </a>
</header>
<div class="soi-menubar">
  <nav class="soi-menu" aria-label="Main">
    <button class="soi-menu-toggle" type="button" aria-expanded="false" aria-controls="soi-menu-list"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg><span>Menu</span></button>
    <ul class="soi-menu-list" id="soi-menu-list">
      <li><a href="/"{cur("home")}>Home</a></li>
      <li><a href="/issues/{LATEST['slug']}/"{cur("latest")}>Latest Issue</a></li>
      <li class="soi-has-sub soi-has-mega"><a class="soi-menu-top" href="/archive/" aria-haspopup="true" aria-expanded="false"{cur("archive")}>Archives <i aria-hidden="true">▾</i></a>
        <div class="soi-mega">
          <div class="soi-mega-side"><div class="soi-mega-years"></div><a class="soi-mega-all" href="/archive/">All years, 2013 → {LATEST.get('year', '')} →</a></div>
          <div class="soi-mega-main"><p class="soi-mega-label">Issues</p><div class="soi-mega-covers"></div></div>
        </div>
      </li>
      <li><a href="/quotes/"{cur("quotes")}>Quotes</a></li>
      <li><a href="/listen/"{cur("listen")}>Listen</a></li>
      <li class="soi-has-sub"><button class="soi-menu-top" type="button" aria-expanded="false">About Us <i aria-hidden="true">▾</i></button><ul class="soi-sub">{sub(MENU["about"])}</ul></li>
      <li class="soi-has-sub"><button class="soi-menu-top" type="button" aria-expanded="false">Further Reading <i aria-hidden="true">▾</i></button><ul class="soi-sub">{sub(MENU["reading"])}</ul></li>
      <li class="soi-has-sub"><button class="soi-menu-top" type="button" aria-expanded="false">Our Websites <i aria-hidden="true">▾</i></button><ul class="soi-sub">{sub(MENU["websites"])}</ul></li>
      <li><a href="{esc(c['href'])}"{cur("contact")}>{esc(c['label'])}</a></li>
    </ul>
    <span class="soi-menu-right">
      <a class="soi-menu-ico" href="/search/" aria-label="Search">{ICON_SEARCH}</a>
      <a class="soi-menu-ico" href="/saved/" aria-label="Saved">{ICON_SAVED}</a>
      <a class="soi-menu-signin" href="/signin/">Sign in</a>
    </span>
  </nav>
</div>
<main id="soi-main">
{body}
</main>
<footer class="soi-foot">
  <div class="soi-foot-in">
    <div><img src="/assets/brand/Spirit-of-Islam-Logo.png" alt="Spirit of Islam" width="240" height="25" loading="lazy"><p>Towards Global Peace &amp; Spiritual Living</p></div>
    <div><strong>Read</strong><a href="/issues/{LATEST['slug']}/">Latest issue</a><a href="/archive/">Archive</a><a href="/quotes/">Quotes</a><a href="/listen/">Listen</a><a href="/search/">Search</a></div>
    <div><strong>About</strong>{"".join(f'<a href="{esc(i["href"])}">{esc(i["label"])}</a>' for i in MENU["about"])}<a href="{esc(c['href'])}">Contact</a></div>
    <div><strong>Our websites</strong>{"".join(f'<a href="{esc(i["href"])}"{ext(i["href"])}>{esc(i["label"])}</a>' for i in MENU["websites"])}</div>
  </div>
  <div class="soi-foot-credit">Design &amp; Development by Md Abullais</div>
</footer>
</body>
</html>
"""


def card(i):
    return (f'<a class="soi-icard" href="/issues/{i["slug"]}/">{cover(i)}'
            f'<b>{esc(short_period(i["period"]))}</b><small>{("Issue " + str(i["number"])) if i["number"] else ""}</small></a>')


SEARCH_FORM = ('<form class="soi-search" action="/search/" method="get" role="search">'
               '<label class="sr-only" for="soi-q">Search all issues</label>'
               '<input id="soi-q" name="q" type="search" placeholder="Search every article since 2013…" autocomplete="off">'
               '<button type="submit">Search</button></form>')


WELCOME = """
<section class="soi-welcome-band">
  <article class="soi-welcome">
    <h1>Welcome to Spirit of Islam</h1>
    <p class="soi-welcome-sub">A Magazine for the Journey of Life</p>
    <div class="soi-rule" aria-hidden="true"><span></span><i></i><span></span></div>
    <div class="soi-welcome-text">
      <p>Dear Readers,</p>
      <p>Welcome to the <strong>Spirit of Islam</strong> magazine, a bimonthly publication dedicated to guiding you on a journey of spiritual enlightenment. Rooted in the profound wisdom of the esteemed Islamic scholar Maulana Wahiduddin Khan, a recipient of numerous national and international accolades, this magazine serves as a beacon for those seeking deeper understanding and inspiration.</p>
      <p>Our readership spans diverse backgrounds, each finding unique and meaningful insights within our pages. The <strong>Spirit of Islam</strong> stands out by focusing on the core principles of reason and science, emphasizing the spirit of Islam over mere form and ritual. Each article is crafted either directly by Maulana Wahiduddin Khan, translated from his Urdu works, or developed by a team he has personally trained and guided.</p>
      <p>In each bimonthly issue, <strong>Spirit of Islam</strong>:</p>
      <ol>
        <li>Presents Islam in a contemporary context, helping readers rediscover Islam from its original sources.</li>
        <li>Explains the Creation Plan of God for humankind, offering clarity and purpose.</li>
        <li>Promotes Global Peace, addressing contemporary issues with wisdom and compassion.</li>
        <li>Guides Readers through Life’s Challenges, providing practical and spiritual support.</li>
        <li>Offers Spirituality to a broad audience, welcoming seekers from all walks of life.</li>
        <li>Fosters Greater Communal Harmony, encouraging understanding and unity through religious insight.</li>
      </ol>
      <p class="soi-welcome-join">Join us as we explore the profound depths of Islam, nurturing your spirit and enriching your journey through life.</p>
      <p class="soi-welcome-sign">-Team Spirit of Islam</p>
    </div>
  </article>
</section>
"""


def minutes(words):
    return max(1, round(words / 200))


def wp_page(wp_id):
    """Words of a page of the live site (copied into sources/pages/<id>.html), without the Divi layout.
    Pictures and forms are not carried over here; the text is kept word for word."""
    f = os.path.join(ROOT, "sources", "pages", f"{wp_id}.html")
    if not os.path.exists(f):
        return None
    s = open(f, encoding="utf-8").read()
    a = s.find('id="main-content"')
    if a < 0:
        return None
    b = s.find("<footer", a)
    c = s[s.index(">", a) + 1: b if b > 0 else len(s)]
    has_form = "<form" in c
    c = re.sub(r"<(script|style|noscript|svg|form|iframe).*?</\1>", "", c, flags=re.S)
    keep = "p|h1|h2|h3|h4|ul|ol|li|strong|b|em|i|a|br|blockquote"
    c = re.sub(rf"<(?!/?(?:{keep})\b)[^>]+>", "", c)
    c = re.sub(r"<(p|h[1-4]|ul|ol|li|strong|b|em|i|blockquote)\b[^>]*>", r"<\1>", c)
    c = re.sub(r'<a\b[^>]*?href="([^"]*)"[^>]*>', r'<a href="\1">', c)
    c = re.sub(r"<h1>", "<h2>", c).replace("</h1>", "</h2>")
    c = re.sub(r"<(p|h[2-4])>\s*(?:&nbsp;)?\s*</\1>", "", c)
    c = re.sub(r"\n\s*\n+", "\n", c).strip()
    return {"html": c, "form": has_form}


def build():
    issues = load_issues()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"))
    for f in ("site.css", "site.js"):
        shutil.copy(os.path.join(HERE, f), os.path.join(OUT, "assets", f))
    if os.path.isdir(os.path.join(HERE, "fonts")):
        shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(OUT, "assets", "fonts"),
                        ignore=shutil.ignore_patterns("*.otf"))      # only the web (woff2) files are published
    for d in ("brand", "covers", "photos"):
        if os.path.isdir(os.path.join(HERE, d)):
            shutil.copytree(os.path.join(HERE, d), os.path.join(OUT, "assets", d))
    years = sorted({i["year"] for i in issues}, reverse=True)
    latest = issues[-1]
    LATEST.update(slug=latest["slug"], year=latest["year"])
    total_articles = sum(len(i["articles"]) for i in issues)
    no_cover = [i["slug"] for i in issues if not os.path.exists(os.path.join(HERE, "covers", i["slug"] + ".webp"))]
    if no_cover:
        print("no cover picture yet:", " ".join(no_cover))

    def write(path, text):
        p = os.path.join(OUT, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)

    # ---- quotes library
    import quotes as quotes_lib
    n_quotes, n_dropped = quotes_lib.build(ROOT, OUT, issues, page, write)
    # ---- home (approved canvas "SOI Redesign")
    redirects = json.dumps(old_links(issues), separators=(",", ":"))
    lab = f"Issue {latest['number']} · {short_period(latest['period'])}"
    n_audio = sum(a["audio"] for a in latest["articles"])
    line = MENU.get("hero_line", {}).get(latest["slug"]) or next((a["title"] for a in latest["articles"] if a["type"] == "article"), latest["period"])
    first = next((a for a in latest["articles"] if a["type"] == "article"), latest["articles"][0])
    guides = "".join(f'<div class="soi-guide">{photo(f"guide{k + 1}", "soi-guide-ph")}<span class="soi-guide-play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M7 4l13 8-13 8z"/></svg></span>'
                     f'<div class="soi-guide-txt"><b>{esc(g)}</b><small>Video coming soon</small></div></div>' for k, g in enumerate(MENU["guides"]))
    topics = "".join(f'<a class="soi-topic" href="/search/?q={esc(t.replace("&", "").replace("  ", " ").replace(" ", "+"))}">{photo("topic-" + re.sub("[^a-z]+", "-", t.lower()).strip("-"))}<b>{esc(t)}</b></a>'
                     for t in MENU["topics"])
    home = WELCOME + f"""
<section class="soi-wide soi-sec">
  <h2 class="soi-h">Our latest issue</h2>
  <div class="soi-hero-grid">
    <div class="soi-hero-main">{photo("hero", "soi-hero-ph")}
      <div class="soi-hero-over">
        <p class="soi-kick">New · {esc(lab)}</p>
        <p class="soi-hero-line">{esc(line)}</p>
        <div class="soi-hero-btns">
          <a class="soi-pillbtn soi-pillbtn-gold" href="/issues/{latest['slug']}/">Read the issue</a>
          {f'<a class="soi-pillbtn soi-pillbtn-line" href="/issues/{latest["slug"]}/#soi-{first["id"]}">Listen · {n_audio} articles</a>' if n_audio else ''}
        </div>
      </div>
    </div>
    <div class="soi-hero-side">
      <div class="soi-cont" id="soi-continue">
        <p class="soi-kick soi-cont-kicker">Start reading</p>
        <h3 class="soi-cont-title">{esc(first['title'])}</h3>
        <p class="soi-cont-meta">{esc(lab)} · {minutes(first['words'])} min</p>
        <div class="soi-cont-bar"><i></i></div>
        <a class="soi-cont-go" href="/issues/{latest['slug']}/#soi-{first['id']}">Read <span aria-hidden="true">→</span></a>
      </div>
      <div class="soi-qotd" id="soi-qotd-home">
        <p class="soi-kick">Quote of the day</p>
        <p class="soi-qotd-text">&nbsp;</p>
        <p class="soi-qotd-src"></p>
        <button type="button" class="soi-qotd-share">Share as image <span aria-hidden="true">→</span></button>
      </div>
    </div>
  </div>
</section>
<section class="soi-wide soi-sec">
  <div class="soi-h-row"><h2 class="soi-h">Latest issues</h2><a href="/archive/">Browse all {len(issues)} issues →</a></div>
  <div class="soi-covers soi-covers-6">{"".join(card(i) for i in reversed(issues[-6:]))}</div>
</section>
<section class="soi-wide soi-sec">
  <h2 class="soi-h">New here? Start with these</h2>
  <p class="soi-h-sub">Short guides to reading, listening and earning gems.</p>
  <div class="soi-guides">{guides}</div>
</section>
<section class="soi-wide soi-sec">
  <h2 class="soi-h">Read by topic</h2>
  <div class="soi-topics">{topics}</div>
</section>
<section class="soi-wide soi-sec">
  <div class="soi-getapp">
    <div class="soi-getapp-txt">
      <p class="soi-kick">The SOI app</p>
      <h2>Read offline, listen with the screen off, and earn gems as you go.</h2>
      <div class="soi-getapp-btns"><span class="soi-storebtn">App Store<small>Coming soon</small></span><span class="soi-storebtn">Google Play<small>Coming soon</small></span></div>
    </div>
    <div class="soi-getapp-nums">
      <div><b>{total_articles:,}</b><span>articles</span></div>
      <div><b>{len(issues)}</b><span>issues since 2013</span></div>
    </div>
  </div>
</section>
<script>(function(){{var m={redirects},id=new URLSearchParams(location.search).get('page_id');if(id&&m[id])location.replace(m[id]);}})();</script>
"""
    write("index.html", page("Spirit of Islam – A Magazine for the Journey of Life", home, cls="soi-home", current="home"))

    # ---- archive
    blocks = []
    for y in years:
        ys = [i for i in issues if i["year"] == y]
        blocks.append(f'<section class="soi-year" id="y{y}"><div class="soi-h-row"><h2 class="soi-h">{y}</h2><span>{len(ys)} issues</span></div>'
                      f'<div class="soi-covers soi-covers-6">{"".join(card(i) for i in reversed(ys))}</div></section>')
    arch = (f'<section class="soi-wide soi-sec soi-page-head"><h1>Archive</h1><p>Every issue from January 2013 to today.</p>'
            f'<div class="soi-years">{"".join(f"<a href=#y{y}>{y}</a>" for y in years)}</div></section>'
            f'<div class="soi-wide">{"".join(blocks)}</div>')
    write("archive/index.html", page("Archive – Spirit of Islam", arch, "Every issue of Spirit of Islam from 2013 to today.", current="archive"))

    # ---- listen: the issues that have read-along audio
    heard = [i for i in reversed(issues) if any(a["audio"] for a in i["articles"])]
    lcards = "".join(f'<a class="soi-icard" href="/issues/{i["slug"]}/">{cover(i)}<b>{esc(short_period(i["period"]))}</b>'
                     f'<small>{sum(a["audio"] for a in i["articles"])} articles with audio</small></a>' for i in heard)
    write("listen/index.html", page("Listen – Spirit of Islam",
          f'<section class="soi-wide soi-sec soi-page-head"><h1>Listen</h1><p>{len(heard)} issues have read-along audio so far: press play on any article and the text follows the voice. '
          f'Audio for the earlier issues is being prepared.</p></section><div class="soi-wide soi-sec"><div class="soi-covers soi-covers-6">{lcards}</div></div>',
          "Issues of Spirit of Islam with read-along audio.", current="listen"))

    # ---- saved (kept in this browser) and sign in (comes with the app)
    write("saved/index.html", page("Saved – Spirit of Islam",
          '<section class="soi-wrap soi-sec soi-page-head"><h1>Saved</h1><p>Articles and quotes you save are kept in this browser. Signing in, to carry them across devices, comes with the app.</p></section>'
          '<section class="soi-wrap soi-sec" id="soi-saved-web"></section>'))
    write("signin/index.html", page("Sign in – Spirit of Islam",
          '<section class="soi-wrap soi-sec soi-page-head"><h1>Sign in</h1><p>Accounts arrive together with the Spirit of Islam app: one sign-in to keep your place, saved articles and gems on every device.</p>'
          '<p>Until then nothing is needed. Your reading place and saved items are remembered in this browser.</p><p><a class="soi-btn soi-btn-solid" href="/saved/">See what is saved here</a></p></section>'))

    # ---- About and Contact pages, word for word from the live site
    for item, cur_key in [(x, "") for x in MENU["about"]] + [(MENU["contact"], "contact")]:
        w = wp_page(item.get("wp"))
        live = f'https://spiritofislam.co.in/?page_id={item.get("wp")}'
        if not w:
            print("page not copied from the live site yet:", item["label"])
            w = {"html": f'<p>This page is being moved from the current website. <a href="{live}">Read it there</a>.</p>', "form": False}
        if w["form"]:      # the message form needs somewhere to send to; until that is decided it stays on the current site
            w["html"] = f'<p>To write to Spirit of Islam, please use the message form on the current website.</p><p><a class="soi-btn soi-btn-solid" href="{live}" target="_blank" rel="noopener">Open the contact form</a></p>'
        write(item["href"].strip("/") + "/index.html", page(f'{item["label"]} – Spirit of Islam',
              f'<section class="soi-wrap soi-sec soi-prose soi-about">{w["html"]}</section>' if not w["form"] else
              f'<section class="soi-wrap soi-sec soi-page-head"><h1>{esc(item["label"])}</h1></section><section class="soi-wrap soi-prose">{w["html"]}</section>', current=cur_key))

    # ---- issues: header, menu and the archive banner, then the magazine
    for k, i in enumerate(issues):
        prev, nxt = (issues[k - 1] if k else None), (issues[k + 1] if k + 1 < len(issues) else None)
        label = f"Issue {i['number']} · {i['period']}" if i["number"] else i["period"]
        nav = ('<nav class="soi-wrap soi-pager" aria-label="Other issues">'
               + (f'<a href="/issues/{prev["slug"]}/"><small>Previous issue</small>{esc(prev["period"])}</a>' if prev else "<span></span>")
               + (f'<a class="soi-next" href="/issues/{nxt["slug"]}/"><small>Next issue</small>{esc(nxt["period"])}</a>' if nxt else "<span></span>")
               + "</nav>")
        body = f"""
<section class="soi-wrap soi-banner">
  <span class="soi-pill">Spirit of Islam <b>•</b> Bimonthly Periodical</span>
  <h1><small>{esc(label)}</small>A Magazine for <em>The Journey of Life</em></h1>
  <div class="soi-banner-btns">
    <a class="soi-btn" href="/archive/">Browse Full Archive</a>
    <a class="soi-btn" href="/archive/#y{i['year']}">Past Issues of {i['year']}</a>
  </div>
</section>
<div class="soi-issue">
{i['block']}
</div>
{nav}
"""
        desc = f"Spirit of Islam, {label}: " + ", ".join(a["title"] for a in i["articles"][:6]) + "."
        short = f"Issue {i['number']} · {short_period(i['period'])}" if i["number"] else short_period(i["period"])
        head = (f'<meta name="soi-issue" content="{i["slug"]}" data-label="{esc(short)}">'
                f'<meta property="og:title" content="{esc(label)} – Spirit of Islam"><meta property="og:image" content="/assets/covers/{i["slug"]}@2x.webp">')
        write(f"issues/{i['slug']}/index.html", page(f"{label} – Spirit of Islam", body, desc, cls="soi-issue-page", head=head,
                                                      current="latest" if i is latest else ""))

    # ---- search
    search = f"""
<section class="soi-wrap soi-block soi-page-head">
  <h1>Search</h1>
  <p>Across {total_articles:,} articles in {len(issues)} issues. A result opens the article itself. Quran references work too, for example <a href="/search/?q=51%3A56">51:56</a>.</p>
</section>
<section class="soi-wrap soi-searchbox"><div id="soi-search"></div></section>
<link rel="stylesheet" href="/pagefind/pagefind-ui.css">
<script src="/pagefind/pagefind-ui.js"></script>
<script>
(function () {{
  var ui = new PagefindUI({{ element: '#soi-search', showSubResults: false, showImages: false, pageSize: 10, resetStyles: false,
    openFilters: ['Year'], translations: {{ placeholder: 'Search every article since 2013…', zero_results: 'Nothing found for [SEARCH_TERM]' }},
    processResult: function (r) {{ if (r.meta && r.meta.issue) r.meta.title = r.meta.title + ' — ' + r.meta.issue; return r; }},
    processTerm: function (t) {{ return t.replace(/(\\d{{1,3}})\\s*:\\s*(\\d{{1,3}})/g, '$1:$2'); }} }});
  var q = new URLSearchParams(location.search).get('q');
  if (q) ui.triggerSearch(q);
}})();
</script>
"""
    write("search/index.html", page("Search – Spirit of Islam", search, "Search every article of Spirit of Islam since 2013.", current="search"))
    write("404.html", page("Page not found – Spirit of Islam",
                           '<section class="soi-wrap soi-block soi-page-head"><h1>Page not found</h1><p>Try the <a href="/archive/">archive</a> or the <a href="/search/">search</a>.</p></section>'))
    write("robots.txt", "User-agent: *\nAllow: /\n")
    # ---- for the phone app: list of issues (so it can show and fetch issues newer than the ones packed
    #      inside it) and permission for the app's web view to fetch issue pages from this site
    import hashlib
    manifest = []
    for i in issues:
        f = os.path.join(OUT, "issues", i["slug"], "index.html")
        b = open(f, "rb").read() if os.path.exists(f) else b""
        manifest.append({"slug": i["slug"], "number": i["number"], "period": i["period"], "year": i["year"],
                         "articles": len(i["articles"]), "audio": sum(a["audio"] for a in i["articles"]),
                         "quiz": bool(i["quiz"]), "titles": [a["title"] for a in i["articles"][:5]],
                         "arts": [[a["id"], a["title"], a["kicker"], minutes(a["words"]), int(bool(a["audio"]))] for a in i["articles"]],
                         "line": MENU.get("hero_line", {}).get(i["slug"], ""),
                         "bytes": len(b), "v": hashlib.sha1(b).hexdigest()[:10]})
    write("issues.json", json.dumps({"issues": manifest}, ensure_ascii=False, separators=(",", ":")))
    write("_headers", "/issues/*\n  Access-Control-Allow-Origin: *\n/issues.json\n  Access-Control-Allow-Origin: *\n"
                      "/assets/*\n  Access-Control-Allow-Origin: *\n")
    asyncio.run(index(issues))
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    print(f"site: {len(issues)} issues, {total_articles} articles, {size / 1e6:.1f} MB in {os.path.relpath(OUT, ROOT)}/")


async def index(issues):
    from pagefind.index import PagefindIndex, IndexConfig
    async with PagefindIndex(config=IndexConfig(output_path=os.path.join(OUT, "pagefind"))) as idx:
        for i in issues:
            label = f"Issue {i['number']} · {i['period']}" if i["number"] else i["period"]
            for a in i["articles"]:
                refs = sorted({f"{x}:{y}" for x, y in re.findall(r"\b(\d{1,3})\s*:\s*(\d{1,3})\b", a["text"])})
                content = a["title"] + ". " + a["text"] + ((" Quran references: " + " ".join(refs)) if refs else "")
                filters = {"Year": [str(i["year"])], "Section": [TYPE_LABEL.get(a["type"], "Articles")], "Issue": [label]}
                if a["author"]:
                    filters["Author"] = [a["author"]]
                if a["audio"]:
                    filters["Audio"] = ["With read-along audio"]
                await idx.add_custom_record(
                    url=f"/issues/{i['slug']}/#soi-{a['id']}", content=content, language="en",
                    meta={"title": a["title"], "issue": label, "section": a["kicker"] or TYPE_LABEL.get(a["type"], "")},
                    filters=filters, sort={"date": i["slug"]})


if __name__ == "__main__":
    build()
