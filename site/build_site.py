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


def page(title, body, desc="", cls="", head=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or 'Spirit of Islam – a magazine for the journey of life. Read every issue since 2013, with read-along audio and search.')}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
{head}
</head>
<body class="{cls}">
<a class="soi-skip" href="#soi-main">Skip to content</a>
<header class="soi-top">
  <div class="soi-wrap soi-top-in">
    <a class="soi-brand" href="/"><span class="soi-brand-mark" aria-hidden="true"></span><span>Spirit of Islam</span></a>
    <nav class="soi-nav" aria-label="Main">
      <a href="/archive/">Archive</a>
      <a href="/quotes/">Quotes</a>
      <a href="/search/" class="soi-nav-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><span>Search</span></a>
    </nav>
  </div>
</header>
<main id="soi-main">
{body}
</main>
<footer class="soi-foot">
  <div class="soi-wrap">
    <p class="soi-foot-name">Spirit of Islam</p>
    <p>Towards global peace and spiritual living · Bimonthly periodical</p>
    <p class="soi-foot-small"><a href="/archive/">Full archive</a> · <a href="/quotes/">Quotes</a> · <a href="/search/">Search</a></p>
    <p class="soi-foot-small">Website by Md Abullais</p>
  </div>
</footer>
</body>
</html>
"""


def card(i):
    n = len(i["articles"])
    audio = sum(a["audio"] for a in i["articles"])
    tags = [f"{n} articles"] + (["Read-along audio"] if audio else []) + (["Quiz"] if i["quiz"] else [])
    firsts = [a["title"] for a in i["articles"] if a["type"] == "article"][:3]
    return (f'<a class="soi-card" href="/issues/{i["slug"]}/">'
            f'<span class="soi-card-no">{("Issue " + str(i["number"])) if i["number"] else "Issue"}</span>'
            f'<span class="soi-card-period">{esc(i["period"])}</span>'
            f'<span class="soi-card-list">{esc(" · ".join(firsts))}</span>'
            f'<span class="soi-card-tags">{"".join(f"<i>{esc(t)}</i>" for t in tags)}</span></a>')


SEARCH_FORM = ('<form class="soi-search" action="/search/" method="get" role="search">'
               '<label class="sr-only" for="soi-q">Search all issues</label>'
               '<input id="soi-q" name="q" type="search" placeholder="Search every article since 2013…" autocomplete="off">'
               '<button type="submit">Search</button></form>')


def build():
    issues = load_issues()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"))
    shutil.copy(os.path.join(HERE, "site.css"), os.path.join(OUT, "assets", "site.css"))
    if os.path.isdir(os.path.join(HERE, "fonts")):
        shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(OUT, "assets", "fonts"),
                        ignore=shutil.ignore_patterns("*.otf"))      # only the web (woff2) files are published
    years = sorted({i["year"] for i in issues}, reverse=True)
    latest = issues[-1]
    total_articles = sum(len(i["articles"]) for i in issues)

    def write(path, text):
        p = os.path.join(OUT, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)

    # ---- quotes library
    import quotes as quotes_lib
    n_quotes, n_dropped = quotes_lib.build(ROOT, OUT, issues, page, write)
    # ---- home
    redirects = json.dumps(old_links(issues), separators=(",", ":"))
    recent = "".join(card(i) for i in reversed(issues[-7:-1]))
    home = f"""
<section class="soi-hero">
  <div class="soi-wrap">
    <span class="soi-pill">Spirit of Islam <b>•</b> Bimonthly Periodical</span>
    <h1>A Magazine for <em>The Journey of Life</em></h1>
    <p class="soi-hero-sub">{len(issues)} issues and {total_articles:,} articles since 2013 — to read, to listen to, and to search.</p>
    {SEARCH_FORM}
  </div>
</section>
<section class="soi-wrap soi-block">
  <h2 class="soi-h2"><span>Latest issue</span></h2>
  <a class="soi-latest" href="/issues/{latest['slug']}/">
    <span class="soi-latest-no">Issue {latest['number']}</span>
    <span class="soi-latest-period">{esc(latest['period'])}</span>
    <span class="soi-latest-list">{esc(' · '.join(a['title'] for a in latest['articles'][:5]))}…</span>
    <span class="soi-btn soi-btn-solid">Read this issue</span>
  </a>
</section>
<section class="soi-wrap soi-block">
  <h2 class="soi-h2"><span>Quote of the day</span><small><a href="/quotes/">All {n_quotes:,} quotes</a></small></h2>
  <div id="soi-home-q"></div>
  <script>(function(){{fetch('/assets/quotes.json').then(function(r){{return r.json()}}).then(function(d){{
    var p=d.quotes.filter(function(q){{return q.t.length<260}}),day=Math.floor(Date.now()/864e5-new Date().getTimezoneOffset()/1440),q=p[(day*7919)%p.length],
        e=function(s){{return String(s).replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]}})}};
    document.getElementById('soi-home-q').innerHTML='<article class="soi-q soi-q-big"><blockquote><p>'+e(q.t)+'</p></blockquote><p class="soi-q-src"><a href="/issues/'+q.s+'/#soi-'+q.a+'">'+e(q.at)+'</a> · Issue '+q.n+', '+e(q.p)+'</p></article>';
  }}).catch(function(){{}})}})();</script>
</section>
<section class="soi-wrap soi-block">
  <h2 class="soi-h2"><span>Recent issues</span></h2>
  <div class="soi-grid">{recent}</div>
</section>
<section class="soi-wrap soi-block">
  <h2 class="soi-h2"><span>Browse by year</span></h2>
  <div class="soi-years">{''.join(f'<a href="/archive/#y{y}">{y}</a>' for y in years)}</div>
</section>
<script>(function(){{var m={redirects},id=new URLSearchParams(location.search).get('page_id');if(id&&m[id])location.replace(m[id]);}})();</script>
"""
    write("index.html", page("Spirit of Islam – A Magazine for the Journey of Life", home, cls="soi-home"))

    # ---- archive
    blocks = []
    for y in years:
        ys = [i for i in issues if i["year"] == y]
        blocks.append(f'<section class="soi-year" id="y{y}"><h2 class="soi-h2"><span>{y}</span><small>{len(ys)} issues</small></h2>'
                      f'<div class="soi-grid">{"".join(card(i) for i in ys)}</div></section>')
    arch = (f'<section class="soi-wrap soi-block soi-page-head"><h1>Archive</h1><p>Every issue from January 2013 to today.</p>'
            f'<div class="soi-years">{"".join(f"<a href=#y{y}>{y}</a>" for y in years)}</div></section>'
            f'<div class="soi-wrap">{"".join(blocks)}</div>')
    write("archive/index.html", page("Archive – Spirit of Islam", arch, "Every issue of Spirit of Islam from 2013 to today."))

    # ---- issues
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
        write(f"issues/{i['slug']}/index.html", page(f"{label} – Spirit of Islam", body, desc, cls="soi-issue-page"))

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
    write("search/index.html", page("Search – Spirit of Islam", search, "Search every article of Spirit of Islam since 2013."))
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
                         "bytes": len(b), "v": hashlib.sha1(b).hexdigest()[:10]})
    write("issues.json", json.dumps({"issues": manifest}, ensure_ascii=False, separators=(",", ":")))
    write("_headers", "/issues/*\n  Access-Control-Allow-Origin: *\n/issues.json\n  Access-Control-Allow-Origin: *\n"
                      "/assets/quotes.json\n  Access-Control-Allow-Origin: *\n")
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
