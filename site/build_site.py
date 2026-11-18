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
                    "articles": arts, "quiz": os.path.exists(os.path.join(base, "quiz.json")), "pdf": i.get("pdf", "")})
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
                    "block": block, "articles": arts, "quiz": True, "pdf": "SOI-NOV-DEC-26-Magazine-file.pdf"})
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
# Filled icons, Boxicons v3 style (https://boxicons.com · free licence: https://docs.boxicons.com/free). The archive, team,
# reading and sign-in icons are the owner's picks; the rest are drawn to match.
_F = '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true">{}</svg>'
ICON_SEARCH = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20.5 20.5-4.5-4.5"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
ICON_SAVED = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3.5h12a1 1 0 0 1 1 1v16l-7-4.5-7 4.5v-16a1 1 0 0 1 1-1z"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
I_HOME = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 10.5 12 3.5l8.5 7V20a1 1 0 0 1-1 1H15v-6H9v6H4.5a1 1 0 0 1-1-1z"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
I_ARCH = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h3.2v16H4zM9.4 4h3.2v16H9.4zM14.6 5.1l3.1-.8 3.8 15-3.1.8z"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
I_QUOTE = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><path d="M4.5 4.5h15a1.5 1.5 0 0 1 1.5 1.5v10a1.5 1.5 0 0 1-1.5 1.5H11l-4.5 3.5v-3.5h-2A1.5 1.5 0 0 1 3 16V6a1.5 1.5 0 0 1 1.5-1.5z"/><path d="M8.5 9h2.2v2c0 1.3-.7 2.1-2 2.5M13.3 9h2.2v2c0 1.3-.7 2.1-2 2.5"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
I_ABOUT = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20.5v-1A4.5 4.5 0 0 1 7 15h4a4.5 4.5 0 0 1 4.5 4.5v1M16 4.6a3.5 3.5 0 0 1 0 6.8M18.5 15.2a4.5 4.5 0 0 1 3 4.3v1"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
I_MAIL = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
I_READ = _F.format('<path d="M21 8c-.2 0-4.85.03-9 2.01C7.85 8.03 3.2 8 3 8c-.55 0-1 .45-1 1v9.88c0 .27.11.53.31.72.19.19.45.3.73.28.04 0 3.97-.11 8.54 2.02.02 0 .03 0 .05.01.12.05.24.08.37.08s.25-.03.37-.08c.02 0 .03 0 .05-.01 4.54-2.12 8.51-2.03 8.54-2.02.27.02.53-.09.73-.28.19-.19.31-.45.31-.72V9c0-.55-.45-1-1-1M4 10.05c1.49.11 4.38.48 7 1.69v7.74c-3.02-1.18-5.62-1.5-7-1.58v-7.86Zm16 7.86c-1.38.08-3.98.4-7 1.58v-7.74c2.62-1.21 5.51-1.58 7-1.69v7.86ZM12 2a3 3 0 1 0 0 6 3 3 0 1 0 0-6"/>')
I_USER = '<svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3.5h4.5a1.5 1.5 0 0 1 1.5 1.5v14a1.5 1.5 0 0 1-1.5 1.5H14M9.5 16.5 14 12l-4.5-4.5M14 12H3.5"/></svg>'   # menu icon set A (owner's choice 17 Nov): one 1.75 px stroke
I_GRID = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/></svg>'
I_LIST = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/></svg>'
LATEST = {"slug": ""}            # filled in by build()


def short_period(p):
    """November–December 2026 -> Nov–Dec 2026 (cards and menus)."""
    return re.sub("|".join(SHORT), lambda m: SHORT[m.group(0)], p)


# Footer: social accounts of CPS International (from the footer of cpsglobal.org) and "Ask AI" links.
_S = '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true">{}</svg>'
SOCIAL = {  # Simple Icons (CC0), https://simpleicons.org
    "fb": _S.format('<path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/>'),
    "yt": _S.format('<path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>'),
    "ig": _S.format('<path d="M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"/>'),
    "x": _S.format('<path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/>'),
    "in": _S.format('<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>'),
    "q": _S.format('<path d="M7.3799.9483A11.9628 11.9628 0 0 1 21.248 19.5397l2.4096 2.4225c.7322.7362.21 1.9905-.8272 1.9905l-10.7105.01a12.52 12.52 0 0 1-.304 0h-.02A11.9628 11.9628 0 0 1 7.3818.9503Zm7.3217 4.428a7.1717 7.1717 0 1 0-5.4873 13.2512 7.1717 7.1717 0 0 0 5.4883-13.2511Z"/>'),
    "udemy": _S.format('<path d="M12 0 5.81 3.573v3.574l6.189-3.574 6.191 3.574V3.573zM5.81 10.148v8.144c0 1.85.589 3.243 1.741 4.234S10.177 24 11.973 24s3.269-.482 4.448-1.474c1.179-.991 1.768-2.439 1.768-4.314v-8.064h-3.242v7.85c0 2.036-.509 3.055-2.948 3.055-1.215 0-2.004-.413-2.39-.995-.387-.582-.508-1.217-.508-2.06v-7.85z"/>'),
    "wa": _S.format('<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>'),
}
CREDIT_HREF = MENU.get("credit_href", "https://timer-media.kaafnoonarts.com/")
_AI_Q = __import__("urllib.parse").parse.quote(MENU.get("ask_ai_prompt", ""))
ASK_AI = "".join(
    f'<a class="soi-ai" href="{h}" target="_blank" rel="noopener"{x} title="Ask {n}">'
    f'<img src="https://www.google.com/s2/favicons?domain={d}&amp;sz=64" alt="" width="20" height="20" loading="lazy"><span>{n}</span></a>'
    for n, d, h, x in [
        ("ChatGPT", "chatgpt.com", f"https://chatgpt.com/?q={_AI_Q}", ""),
        ("Claude", "claude.ai", f"https://claude.ai/new?q={_AI_Q}", ""),
        ("Gemini", "gemini.google.com", "https://gemini.google.com/app", ' data-copy-prompt="1"'),
        ("Perplexity", "perplexity.ai", f"https://www.perplexity.ai/search?q={_AI_Q}", ""),
        ("Grok", "grok.com", f"https://grok.com/?q={_AI_Q}", ""),
    ])


def ext(href):
    return ' target="_blank" rel="noopener"' if href.startswith("http") else ""


def sub(items):
    return "".join(f'<li><a href="{esc(i["href"])}"{ext(i["href"])}>{esc(i["label"])}</a></li>' for i in items)


def photo(key, cls=""):
    """A photo slot. Until a photo is approved for it (menu.json: photos) it shows a plain drawn landscape."""
    f = MENU.get("photos", {}).get(key)
    if f and os.path.exists(os.path.join(HERE, "photos", f)):
        return f'<span class="soi-ph {cls}"><img src="/assets/photos/{esc(f)}" alt="" loading="lazy" decoding="async"></span>'
    return f'<span class="soi-ph soi-ph-wait {cls}" aria-hidden="true"></span>'


def cover(i, big=False):
    f = f'{i["slug"]}{"@2x" if big else ""}.webp'
    img = (f'<img src="/assets/covers/{f}" alt="" loading="lazy" decoding="async" width="600" height="850" onload="this.classList.add(\'is-in\')" onerror="this.remove()">'
           if os.path.exists(os.path.join(HERE, "covers", f)) else "")
    return (f'<span class="soi-cover"><span class="soi-cover-fb" aria-hidden="true"><img class="soi-cover-dove" src="/assets/brand/Peogen-logo.png" alt="" width="470" height="453"><b>Spirit of Islam</b><i>{esc(i["period"])}</i></span>{img}</span>')


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
      <li><a href="/"{cur("home")}>{I_HOME}<span>Home</span></a></li>
      <li class="soi-has-sub soi-has-mega"><a class="soi-menu-top" href="/archive/" aria-haspopup="true" aria-expanded="false"{cur("archive")}>{I_ARCH}<span>Archives</span> <i aria-hidden="true">▾</i></a>
        <div class="soi-mega">
          <div class="soi-mega-side"><div class="soi-mega-years"></div><a class="soi-mega-all" href="/archive/">All years, 2013 → {LATEST.get('year', '')} →</a></div>
          <div class="soi-mega-main"><p class="soi-mega-label">Issues</p><div class="soi-mega-covers"></div></div>
        </div>
      </li>
      <li><a href="/quotes/"{cur("quotes")}>{I_QUOTE}<span>Quotes</span></a></li>
      <li><a href="/about/"{cur("about")}>{I_ABOUT}<span>About Us</span></a></li>
      <li><a href="{esc(c['href'])}"{cur("contact")}>{I_MAIL}<span>{esc(c['label'])}</span></a></li>
    </ul>
    <span class="soi-menu-right">
      <a class="soi-menu-ico" href="/search/" aria-label="Search">{ICON_SEARCH}</a>
      <a class="soi-menu-ico" href="/saved/" aria-label="Saved">{ICON_SAVED}</a>
      <a class="soi-menu-ico soi-gem-ico" href="/gems/" aria-label="Gems: earn gems by reading, listening and sharing" data-tip="Earn gems"><svg class="soi-fi soi-fi-st" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/><path d="M2.5 9h19M9 3.5 7.5 9 12 20.5 16.5 9 15 3.5"/></svg></a>
      <a class="soi-menu-signin" href="/signin/">{I_USER}<span>Sign in</span></a>
    </span>
  </nav>
</div>
<main id="soi-main">
{body}
</main>
<footer class="soi-foot soi-foot2">
  <div class="soi-foot2-in">
    <a class="soi-foot2-brand" href="/" aria-label="Spirit of Islam – home"><span class="soi-foot2-lock"><img class="soi-foot2-bird" src="/assets/brand/Peogen-logo.png" alt="" width="470" height="453" loading="lazy"><span class="soi-foot2-rule" aria-hidden="true"></span><img class="soi-foot2-mark" src="/assets/brand/soi-mark-white.svg" alt="Spirit of Islam" width="790" height="511" loading="lazy"></span><img src="/assets/brand/Slogan-Line.png" alt="Towards Global Peace &amp; Spiritual Living" width="1600" height="138" loading="lazy"></a>
    <div class="soi-foot2-col"><h2>Read</h2><a href="/issues/{LATEST['slug']}/">Latest issue</a><a href="/archive/">Archives</a><a href="/quotes/">Quotes</a><a href="/search/">Search</a><a href="/saved/">Saved</a><a href="/?tour=1" data-soi-tour>Take the website tour</a></div>
    <div class="soi-foot2-col"><h2>About</h2><a href="/about/">About Spirit of Islam</a><a href="/about/#founder">Our Founder</a><a href="/about/#team">SOI Team</a><a href="{esc(c['href'])}">Contact Us</a></div>
    <div class="soi-foot2-col"><h2>More from CPS</h2>{"".join(f'<a href="{esc(i["href"])}" target="_blank" rel="noopener">{esc(i["label"])}</a>' for i in MENU["more_cps"])}</div>
    <div class="soi-foot2-col"><h2>Follow</h2><p class="soi-foot2-follow">Maulana Wahiduddin Khan and CPS International</p><div class="soi-soc">{"".join(f'<a href="{esc(i["href"])}" target="_blank" rel="noopener" aria-label="{esc(i["label"])}" title="{esc(i["label"])}">{SOCIAL[i["icon"]]}</a>' for i in MENU["social"])}</div></div>
  </div>
  <div class="soi-foot2-base">
    <div class="soi-ask-ai" data-prompt="{esc(MENU.get('ask_ai_prompt', ''))}"><span>Ask AI <svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2c.4 3.9 2.1 5.6 6 6-3.9.4-5.6 2.1-6 6-.4-3.9-2.1-5.6-6-6 3.9-.4 5.6-2.1 6-6m6.5 11c.2 2 1.1 2.8 3 3-1.9.2-2.8 1.1-3 3-.2-1.9-1.1-2.8-3-3 1.9-.2 2.8-1 3-3"/></svg> about Spirit of Islam</span>{ASK_AI}</div>
  </div>
</footer>
<section class="soi-credit" aria-label="Website credit">
  <p class="soi-credit-in"><span>Design &amp; Development by Md Abullais</span><a class="soi-credit-click" href="{CREDIT_HREF}" target="_blank" rel="noopener" aria-label="Contact Md Abullais, the website developer">Click</a></p>
</section>
</body>
</html>
"""


TS_KEY = MENU.get("turnstile_sitekey", "")
TS_TAG = (f'<div class="cf-turnstile" data-sitekey="{TS_KEY}" data-theme="light" data-size="flexible"></div>'
          '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>') if TS_KEY else ""
FORM_JS = """<script>
(function () {
  [].forEach.call(document.querySelectorAll('form.soi-api-form'), function (f) {
    var t = f.querySelector('[name=t]'); if (t) t.value = Date.now();
    var out = f.querySelector('.soi-form-out'), btn = f.querySelector('[type=submit]');
    f.addEventListener('submit', function (e) {
      e.preventDefault(); btn.disabled = true; out.className = 'soi-form-out'; out.textContent = 'Sending…';
      fetch(f.action, { method: 'POST', body: new FormData(f) }).then(function (r) { return r.json(); }).then(function (j) {
        if (j.ok) { out.className = 'soi-form-out is-ok'; out.textContent = f.dataset.ok; f.reset(); if (t) t.value = Date.now(); }
        else { out.className = 'soi-form-out is-err'; out.textContent = j.error || 'Please try again.'; }
      }).catch(function () { out.className = 'soi-form-out is-err'; out.textContent = 'No connection. Please try again.'; })
        .then(function () { btn.disabled = false; if (window.turnstile) try { turnstile.reset(); } catch (x) {} });
    });
  });
})();
</script>"""
CONTACT_FORM = f"""
<form class="soi-api-form soi-contact-form" action="/api/contact" method="post" data-ok="Thank you. Your message has been sent; we will reply by email.">
  <div class="soi-form-row"><label>Your name<input name="name" required maxlength="120" autocomplete="name"></label>
  <label>Your email<input name="email" type="email" required maxlength="200" autocomplete="email"></label></div>
  <label>Subject<input name="subject" maxlength="160"></label>
  <label>Message<textarea name="message" required minlength="10" maxlength="5000" rows="6"></textarea></label>
  <label class="soi-hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
  <input type="hidden" name="t" value="0">
  {TS_TAG}
  <p class="soi-form-foot"><button class="soi-btn soi-btn-solid" type="submit">Send message</button><span class="soi-form-out" role="status"></span></p>
  <p class="soi-form-note">Protected against spam. Your details are used only to reply to you.</p>
</form>{FORM_JS}"""


def _pdf_map():
    """issue PDF file name -> /media/pdfs/<upload year>/<file> (the R2 copy of the WordPress upload)"""
    import csv
    m = {}
    p = os.path.join(ROOT, "inventory", "inventory-pdfs.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            y = r["url"].split("/uploads/")[-1].split("/")[0] if "/uploads/" in r["url"] else "other"
            m.setdefault(r["file"], f"/media/pdfs/{y}/{r['file']}")
    return m


PDFS = None


def pdf_href(i):
    global PDFS
    if PDFS is None:
        PDFS = _pdf_map()
    return PDFS.get(i.get("pdf") or "", "")


I_PDF = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3.5H6.5A1.5 1.5 0 0 0 5 5v14a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19V8.5z"/><path d="M14 3.5v5h5"/></svg>'


I_LISTEN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 9.5v5h3.5l4.5 4v-13l-4.5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>'
I_READ_PDF = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3.5H6.5A1.5 1.5 0 0 0 5 5v14a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19V8.5z"/><path d="M14 3.5v5h5M8.5 13h7M8.5 16.5h5"/></svg>'
I_FLIP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5zM12 6.5v13"/></svg>'
STAR = '<svg class="soi-act-star" viewBox="0 0 44 44" aria-hidden="true"><path d="M22 1l6 7 9-1-1 9 7 6-7 6 1 9-9-1-6 7-6-7-9 1 1-9-7-6 7-6-1-9 9 1z"/></svg>'
ARROW_GO = '<span class="soi-act-go" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span>'


def act_card(href, icon, title, sub, tab=False):
    return (f'<a class="soi-act" href="{esc(href)}"{' target="_blank" rel="noopener"' if tab else ""}><span class="soi-act-badge">{STAR}{icon}</span>'
            f'<span class="soi-act-txt"><b>{title}</b><small>{sub}</small></span>{ARROW_GO}</a>')


def spine_color(slug):
    """A deep colour taken from the cover picture, for the book's spine."""
    import colorsys
    try:
        from PIL import Image
        im = Image.open(os.path.join(HERE, "covers", slug + ".webp")).convert("RGB").resize((40, 56))
        px = [p for p in im.getdata()]
        best = max(px, key=lambda p: colorsys.rgb_to_hsv(*[c / 255 for c in p])[1] * (0.4 + colorsys.rgb_to_hsv(*[c / 255 for c in p])[2]))
        h, s_, v = colorsys.rgb_to_hsv(*[c / 255 for c in best])
        r, g, b = colorsys.hsv_to_rgb(h, min(.75, max(.35, s_)), .38)
        return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
    except Exception:
        return "#173A48"


def back_cover(i):
    f = os.path.join(HERE, "covers", "back", i["slug"] + ".webp")
    if os.path.exists(f):
        return f'<img src="/assets/covers/back/{i["slug"]}.webp" alt="Back cover of {esc(i["period"])}" loading="lazy" width="600" height="850">'
    return '<span class="soi-book-backfb"><img src="/assets/brand/Peogen-logo.png" alt="" width="470" height="453"><b>Spirit of Islam</b><i>spiritofislam.co.in</i></span>'


def card_actions(i):
    pdf = pdf_href(i)
    return (f'<p class="soi-icard-act"><a class="soi-ib soi-ib-main" href="/issues/{i["slug"]}/">Read &amp; Listen</a>'
            + (f'<a class="soi-ib" href="{esc(pdf)}" target="_blank" rel="noopener" aria-label="Read the PDF of {esc(i["period"])} (opens in a new tab)">{I_PDF}PDF</a>' if pdf else "")
            + "</p>")


def card(i):
    num = (f'<span class="soi-icard-no" aria-hidden="true">{i["number"]}</span>' if i["number"] else "")
    return (f'<div class="soi-icard"><a class="soi-icard-link" href="/issues/{i["slug"]}/">'
            f'<span class="soi-icard-mon">{esc(i["period"])}</span>'
            f'<span class="soi-icard-cv">{cover(i)}{num}</span>'
            f'<b class="sr-only">{esc(short_period(i["period"]))}</b><small class="soi-icard-sub">{("Issue " + str(i["number"])) if i["number"] else ""}'
            f'<span class="soi-icard-meta">{len(i["articles"])} articles</span></small>'
            f'<span class="soi-icard-more">{len(i["articles"])} articles · {esc(", ".join(a["title"] for a in i["articles"][:3]))}…</span></a>'
            f'{card_actions(i)}</div>')


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
    guides = "".join(f'<div class="soi-guide"><div class="soi-guide-ph soi-guide-blank" aria-hidden="true"><img src="/assets/brand/Peogen-logo.png" alt="" width="470" height="453" loading="lazy"><span>Tutorial {k + 1}</span></div><span class="soi-guide-play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M7 4l13 8-13 8z"/></svg></span>'
                     f'<div class="soi-guide-txt"><b>{esc(g)}</b><small>Video coming soon</small></div></div>' for k, g in enumerate(MENU["guides"]))
    topics = "".join(f'<a class="soi-topic" href="/search/?q={esc(t.replace("&", "").replace("  ", " ").replace(" ", "+"))}">{photo("topic-" + re.sub("[^a-z]+", "-", t.lower()).strip("-"))}<b>{esc(t)}</b></a>'
                     for t in MENU["topics"])
    home = WELCOME + f"""
<section class="soi-wide soi-sec">
  <h2 class="soi-h">Our latest issue</h2>
  <div class="soi-latest">
    <div class="soi-book-wrap">
      <button type="button" class="soi-book-scene" aria-label="Turn the magazine over to see the back cover" style="--spine:{spine_color(latest['slug'])}">
        <span class="soi-book">
          <span class="soi-book-back">{back_cover(latest)}</span>
          <span class="soi-book-spine"></span>
          <span class="soi-book-pages"></span>
          <span class="soi-book-front">{cover(latest)}</span>
        </span>
      </button>
      <span class="soi-book-shadow"></span>
      <small class="soi-book-hint">Tap the magazine to turn it over</small>
    </div>
    <div class="soi-latest-txt">
      <p class="soi-kick">New · {esc(lab)}</p>
      <p class="soi-latest-line">{esc(line)}</p>
      <div class="soi-acts">
        {act_card(f"/issues/{latest['slug']}/", I_LISTEN, "Read &amp; Listen", f"{len(latest['articles'])} articles · audio for every article")}
        {act_card(pdf_href(latest), I_READ_PDF, "Read the PDF", "The printed magazine, opens in a new tab", tab=True) if pdf_href(latest) else ""}
      </div>
      <div class="soi-cont soi-cont-mini" id="soi-continue">
        <p class="soi-kick soi-cont-kicker">Start reading</p>
        <h3 class="soi-cont-title">{esc(first['title'])}</h3>
        <p class="soi-cont-meta">{esc(lab)} · {minutes(first['words'])} min</p>
        <div class="soi-cont-bar"><i></i></div>
        <a class="soi-cont-go" href="/issues/{latest['slug']}/#soi-{first['id']}">Read <span aria-hidden="true">→</span></a>
      </div>
    </div>
  </div>
</section>
<section class="soi-wide soi-sec soi-qotd-sec">
  <h2 class="soi-h">Quote of the day</h2>
  <div class="soi-q2-spot soi-qotd-spot" id="soi-qotd-home" aria-live="polite"><div class="soi-q2-spot-in"><blockquote><p>&nbsp;</p></blockquote></div></div>
  <p class="soi-qotd-more"><a class="soi-pillbtn soi-pillbtn-line" href="/quotes/">More quotes <span aria-hidden="true">→</span></a></p>
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
<section class="soi-wide soi-sec soi-news" aria-labelledby="soi-news-h">
  <div class="soi-news-in">
    <div class="soi-news-art" aria-hidden="true">{"".join(f'<span class="soi-news-cv soi-news-cv{k}">{cover(x)}</span>' for k, x in enumerate(issues[-3:]))}</div>
    <div class="soi-news-body">
      <p class="soi-kick">Stay connected · it’s free</p>
      <h2 id="soi-news-h">Never miss an issue</h2>
      <p>Get every new issue of Spirit of Islam free in your inbox, with a quote to reflect on and the audio links. About six emails a year. No spam, unsubscribe in one click.</p>
      <form class="soi-api-form soi-news-form" action="/api/subscribe" method="post" data-ok="Almost done: please confirm from the email we have just sent you.">
        <label class="sr-only" for="soi-news-n">Your name (optional)</label><input id="soi-news-n" name="name" placeholder="Your name (optional)" maxlength="100" autocomplete="given-name">
        <label class="sr-only" for="soi-news-e">Your email address</label><input id="soi-news-e" name="email" type="email" required placeholder="Your email address" maxlength="200" autocomplete="email">
        <label class="soi-hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
        {TS_TAG.replace('data-theme="light"', 'data-theme="dark"')}
        <button class="soi-pillbtn soi-pillbtn-gold" type="submit">Subscribe for free</button>
        <span class="soi-form-out" role="status"></span>
      </form>
    </div>
  </div>
</section>
{FORM_JS}
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
            f'<div class="soi-years">{"".join(f"<a href=#y{y}>{y}</a>" for y in years)}</div>'
            f'<div class="soi-view" role="group" aria-label="Show issues as"><button type="button" data-view="grid" aria-pressed="true">{I_GRID}<span>Grid</span></button>'
            f'<button type="button" data-view="list" aria-pressed="false">{I_LIST}<span>List</span></button></div></section>'
            f'<div class="soi-wide soi-arch" data-view="grid">{"".join(blocks)}</div>')
    write("archive/index.html", page("Archive – Spirit of Islam", arch, "Every issue of Spirit of Islam from 2013 to today.", current="archive"))

    # ---- saved (kept in this browser) and sign in (comes with the app)
    write("saved/index.html", page("Saved – Spirit of Islam",
          '<section class="soi-wrap soi-sec soi-page-head"><h1>Saved</h1><p>Articles and quotes you save are kept in this browser. Signing in, to carry them across devices, comes with the app.</p></section>'
          '<section class="soi-wrap soi-sec" id="soi-saved-web"></section>'))
    write("gems/index.html", page("Gems – Spirit of Islam", """
<section class="soi-wrap soi-sec soi-page-head"><p class="soi-kicker">New</p><h1>Earn gems as you read</h1>
<p>Gems are a small thank-you for spending time with Spirit of Islam. Collect them on the website and in the app, and see where you stand on the leaderboard.</p></section>
<section class="soi-wrap soi-sec"><ul class="soi-cover-grid soi-gem-ways"><li><span class="soi-cov-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5zM4 20.5A2.5 2.5 0 0 0 6.5 23H20"/><path d="m9 10 2 2 4-4"/></svg></span><span class="soi-gem-pts"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/></svg>+10</span><b>Finish an article</b><span>Reading or listening to the end</span></li><li><span class="soi-cov-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14"/><path d="M12 17.5h.01"/></svg></span><span class="soi-gem-pts"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/></svg>+5</span><b>Each correct quiz answer</b><span>Ten questions in every issue</span></li><li><span class="soi-cov-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/></svg></span><span class="soi-gem-pts"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/></svg>+20</span><b>Quiz score 7 or more</b><span>A bonus for a strong score</span></li><li><span class="soi-cov-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/></svg></span><span class="soi-gem-pts"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/></svg>+5</span><b>Share an article or quote</b><span>Up to 25 gems a day</span></li><li><span class="soi-cov-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 7v5c0 4.4 3.4 8.4 8 9 4.6-.6 8-4.6 8-9V7z"/><path d="m9 12 2 2 4-4"/></svg></span><span class="soi-gem-pts"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/></svg>+50</span><b>Finish a whole issue</b><span>Every article of one issue</span></li><li><span class="soi-cov-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2c1 3.5 5 5.5 5 10a5 5 0 0 1-10 0c0-2 1-3.5 2-4.5.3 1.6 1.2 2.5 2 3 0-3 .5-6 1-8.5z"/></svg></span><span class="soi-gem-pts"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/></svg>+5 a day</span><b>Daily reading streak</b><span>Come back every day</span></li></ul>
<p class="soi-gem-note">These values are a first proposal and may change before accounts open.</p>
<div class="soi-gem-board"><h2>Leaderboard</h2><p>The leaderboard opens with free accounts, together with the Spirit of Islam app. Gems you collect before then are kept in this browser and move to your account when you sign up.</p>
<p><a class="soi-btn soi-btn-solid" href="/signin/">Sign up free</a></p></div></section>""", "How to earn gems on Spirit of Islam: reading, listening, quizzes and sharing.", current="gems"))
    write("signin/index.html", page("Sign in – Spirit of Islam",
          '<section class="soi-wrap soi-sec soi-page-head"><h1>Sign in</h1><p>Accounts arrive together with the Spirit of Islam app: one sign-in to keep your place, saved articles and gems on every device.</p>'
          '<p>Until then nothing is needed. Your reading place and saved items are remembered in this browser.</p><p><a class="soi-btn soi-btn-solid" href="/saved/">See what is saved here</a></p></section>'))

    # ---- About and Contact pages, word for word from the live site
    # ---- About Us: one page (about the magazine, the founder, the mission and the team)
    team = MENU["team"]
    def initials(n):
        w = [x for x in re.sub(r"^(Prof|Dr|Mr|Ms|Mrs)\.?\s+", "", n).split() if x[:1].isalpha()]
        return (w[0][0] + (w[-1][0] if len(w) > 1 else "")).upper()
    lead, rest = team["people"][0], team["people"][1:]
    member = lambda role, n: f'<li class="soi-tm"><small>{esc(role)}</small><b>{esc(n)}</b></li>'
    team_html = (f'<ul class="soi-tm-grid">{member(lead[0], lead[1][0])}'
                 f'{"".join(member(r[:-1] if len(names) > 1 and r.endswith("s") else r, n) for r, names in rest for n in names)}</ul>'
                 f'<p class="soi-tm-office"><svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7m0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5"/></svg>'
                 f'<span><small>Office</small>{esc(team["office"])}</span></p>')
    covers = [
        ("Islamic Teachings", "Understanding the Quran, Sunnah and the fundamental principles of Islam.", I_READ),
        ("God-Realization", "Reflecting on the Creator, the purpose of life and the signs of God in the universe.", '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a1 1 0 0 1 1 1v1.1a7 7 0 0 1 5.9 5.9H20a1 1 0 1 1 0 2h-1.1a7 7 0 0 1-5.9 5.9V20a1 1 0 1 1-2 0v-1.1A7 7 0 0 1 5.1 13H4a1 1 0 1 1 0-2h1.1A7 7 0 0 1 11 5.1V4a1 1 0 0 1 1-1m0 4a5 5 0 1 0 0 10 5 5 0 0 0 0-10m0 3a2 2 0 1 1 0 4 2 2 0 0 1 0-4"/></svg>'),
        ("Spiritual Development", "Purification of the heart, sincerity, humility and strengthening one’s relationship with God.", '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.4 10.6 20C5.4 15.4 2 12.3 2 8.5 2 5.4 4.4 3 7.5 3c1.7 0 3.4.8 4.5 2.1C13.1 3.8 14.8 3 16.5 3 19.6 3 22 5.4 22 8.5c0 3.8-3.4 6.9-8.6 11.5zM7.5 5C5.5 5 4 6.5 4 8.5c0 2.9 3.1 5.7 7.9 10l.1.1.1-.1c4.8-4.3 7.9-7.1 7.9-10C20 6.5 18.5 5 16.5 5c-1.5 0-3 1-3.6 2.4h-1.9C10.5 6 9 5 7.5 5"/></svg>'),
        ("Global Peace", "Promoting tolerance, forgiveness, peaceful coexistence and harmony among communities.", '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20m7.9 9h-3a15.5 15.5 0 0 0-1.4-6.1A8 8 0 0 1 19.9 11M12 4c.9 1 2.6 3.4 2.9 7H9.1C9.4 7.4 11.1 5 12 4M8.5 4.9A15.5 15.5 0 0 0 7.1 11h-3a8 8 0 0 1 4.4-6.1M4.1 13h3a15.5 15.5 0 0 0 1.4 6.1A8 8 0 0 1 4.1 13M12 20c-.9-1-2.6-3.4-2.9-7h5.8c-.3 3.6-2 6-2.9 7m3.5-.9a15.5 15.5 0 0 0 1.4-6.1h3a8 8 0 0 1-4.4 6.1"/></svg>'),
        ("Personality Development", "Cultivating positive thinking, patience, wisdom and intellectual maturity.", '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a7 7 0 0 0-4 12.7V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.3A7 7 0 0 0 12 2m2.6 11.4-.6.3V16h-4v-2.3l-.6-.3a5 5 0 1 1 5.2 0M9 20h6v2H9z"/></svg>'),
        ("Contemporary Issues", "Exploring modern challenges, science, society and human relationships in the light of Islamic teachings.", '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 3H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2m0 16H4V5h16zM6 7h6v6H6zm8 0h4v2h-4zm0 4h4v2h-4zm-8 4h12v2H6z"/></svg>'),
        ("Life and the Hereafter", "Reflecting on life’s purpose, accountability, death and the eternal life to come.", '<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2c.3 0 .6.2.8.4l2.9 4.2 4.9 1.5a1 1 0 0 1 .5 1.6L18 13.7l.1 5.1a1 1 0 0 1-1.3 1L12 18.1l-4.8 1.7a1 1 0 0 1-1.3-1l.1-5.1L2.9 9.7a1 1 0 0 1 .5-1.6l4.9-1.5 2.9-4.2c.2-.3.5-.4.8-.4m0 2.8-2.3 3.4-3.9 1.2 2.5 3.2-.1 4.1 3.8-1.4 3.8 1.4-.1-4.1 2.5-3.2-3.9-1.2z"/></svg>'),
    ]
    cover_html = "".join(f'<li><span class="soi-cov-ico">{ic}</span><b>{esc(t)}</b><span>{esc(d)}</span></li>' for t, d, ic in covers)
    about = f"""
<section class="soi-wrap soi-sec soi-page-head soi-center"><p class="soi-kicker">About us</p><h1>About Spirit of Islam Magazine</h1></section>
<section class="soi-wrap soi-about3">
  <p class="soi-lede">Spirit of Islam (SOI) is an English-language magazine based on the teachings, writings and intellectual approach of the late Maulana Wahiduddin Khan (1925–2021), a renowned Islamic scholar and founder of the Centre for Peace and Spirituality (CPS International).</p>
  <p>The magazine aims to present the true spirit of Islam in a contemporary, thoughtful and accessible manner, drawing inspiration from the Quran and the Sunnah. It seeks to develop a deeper understanding of religion by encouraging reflection, reason, spirituality and positive thinking.</p>
</section>
<section class="soi-wrap soi-sec soi-covers-sec">
  <h2 class="soi-h">What Does It Cover?</h2>
  <p class="soi-covers-intro">Spirit of Islam covers a wide range of subjects, including:</p>
  <ul class="soi-cover-grid">{cover_html}</ul>
</section>
<section class="soi-wrap soi-sec soi-vision">
  <div class="soi-vision-in">
    <p class="soi-kicker">Our Vision</p>
    <p class="soi-vision-lede">Through its articles and thought-provoking insights, Spirit of Islam seeks to inspire readers to become spiritually awakened, intellectually developed and positive-minded individuals who contribute towards a peaceful and better society.</p>
    <p>The magazine is intended not only for Muslims but also for anyone interested in understanding Islam, spirituality, peace and the purpose of human existence.</p>
  </div>
</section>
<section class="soi-wrap soi-sec soi-explore">
  <p><b>Explore the magazine:</b> <a href="/">www.spiritofislam.co.in</a></p>
  <p>The website provides access to the latest edition as well as the complete archive of previous issues, allowing readers to explore its rich collection of articles and publications.</p>
  <p class="soi-explore-btns"><a class="soi-btn soi-btn-solid" href="/issues/{LATEST['slug']}/">Read the latest issue</a> <a class="soi-btn" href="/archive/">Browse the archive</a></p>
</section>
<section class="soi-wrap soi-sec soi-founder" id="founder">
  <img class="soi-founder-img" src="/assets/brand/maulana.webp" alt="Maulana Wahiduddin Khan" width="568" height="694" loading="lazy">
  <div>
    <p class="soi-kicker">Our founder</p>
    <h2>Maulana Wahiduddin Khan <small>1925–2021</small></h2>
    <p>Maulana Wahiduddin Khan was born in Azamgarh, Uttar Pradesh. Trained in classical Islamic learning, he went on to study modern science and thought on his own, and spent his life showing that faith and reason do not conflict.</p>
    <p>In 1976 he started <i>Al-Risala</i>, an Urdu monthly, and in 2001 he founded the Centre for Peace and Spirituality (CPS International). He wrote more than two hundred books, among them a translation of and commentary on the Quran.</p>
    <p>He received the Padma Bhushan in 2000 and the Padma Vibhushan in 2021, two of India’s highest civilian honours. His central message, that peace is the heart of Islam and that patience and positive thinking can turn every problem into an opportunity, is the message this magazine carries on.</p>
  </div>
</section>
<section class="soi-wrap soi-sec soi-team2" id="team">
  <p class="soi-kicker">The people behind each issue</p>
  <h2>The SOI Team</h2>
  <p class="soi-team2-intro">Spirit of Islam is prepared by a team trained and guided by Maulana Wahiduddin Khan.</p>
  {team_html}
</section>"""
    write("about/index.html", page("About Us – Spirit of Islam", about, "About Spirit of Islam, its founder Maulana Wahiduddin Khan, and the SOI team.", cls="soi-aboutpage", current="about"))
    for old, to in [("about/our-founder", "/about/#founder"), ("about/our-mission", "/about/"), ("about/team", "/about/#team")]:
        write(old + "/index.html", f'<!doctype html><meta charset="utf-8"><title>About Us</title><meta http-equiv="refresh" content="0; url={to}"><link rel="canonical" href="{to}"><a href="{to}">About Us</a>')
    for item, cur_key in [(MENU["contact"], "contact")]:
        w = wp_page(item.get("wp"))
        live = f'https://spiritofislam.co.in/?page_id={item.get("wp")}'
        if not w:
            print("page not copied from the live site yet:", item["label"])
            w = {"html": f'<p>This page is being moved from the current website. <a href="{live}">Read it there</a>.</p>', "form": False}
        if w["form"]:      # our own form: Turnstile + hidden field + time check + rate limit, sent by functions/api/contact.js
            w["html"] = w["html"] + CONTACT_FORM
        write(item["href"].strip("/") + "/index.html", page(f'{item["label"]} – Spirit of Islam',
              f'<section class="soi-wrap soi-sec soi-prose soi-about">{w["html"]}</section>' if not w["form"] else
              f'<section class="soi-wrap soi-sec soi-page-head"><h1>{esc(item["label"])}</h1></section><section class="soi-wrap soi-prose">{w["html"]}</section>', current=cur_key))

    # ---- issues: header, menu and the archive banner, then the magazine
    for k, i in enumerate(issues):
        prev, nxt = (issues[k - 1] if k else None), (issues[k + 1] if k + 1 < len(issues) else None)
        label = f"Issue {i['number']} · {i['period']}" if i["number"] else i["period"]
        nav = ('<nav class="soi-wrap soi-pager" aria-label="Other issues">'
               + (f'<a class="soi-prev" href="/issues/{prev["slug"]}/" rel="prev"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg><span><small>Previous issue</small>{esc(prev["period"])}</span></a>' if prev else "<span></span>")
               + (f'<a class="soi-next" href="/issues/{nxt["slug"]}/" rel="next"><span><small>Next issue</small>{esc(nxt["period"])}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg></a>' if nxt else "<span></span>")
               + "</nav>")
        body = f"""
<div class="soi-auto-banner"><div class="soi-banner-scope"><div class="context-banner">
  <div class="context-badge"><span class="context-badge-dot"></span><span>Spirit of Islam • Bimonthly Periodical</span></div>
  <h2 class="context-title">A Magazine for The Journey of Life</h2>
  <p class="context-desc">A bimonthly periodical dedicated to global peace and spiritual living, presenting the teachings of Maulana Wahiduddin Khan through the lens of reason and modern thought.</p>
  <div class="btn-group">
    <a href="/archive/" class="btn-awwwards-orbit"><span>Browse Full Archive</span><span class="orbit-icon-wrap"><svg class="orbit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg></span></a>
    <a href="/archive/#y{i['year']}" class="btn-awwwards-liquid soi-year-btn"><span>Past issues of {i['year']}</span><svg class="liquid-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg></a>
  </div>
</div></div></div>
<header class="soi-wrap soi-page-head soi-issue-head">
  <p class="soi-kicker">{"Issue " + str(i["number"]) if i["number"] else "Spirit of Islam"}</p>
  <h1>{esc(i["period"])}<span class="sr-only"> – Spirit of Islam</span></h1>
  <p>{len(i["articles"])} articles in this issue. Tap a title to open it.</p>
</header>
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
<section class="soi-wrap soi-searchbox" id="soi-sx">
  <form class="soi-sx-bar" role="search" onsubmit="return false">
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    <label class="sr-only" for="soi-sx-q">Search every article</label>
    <input id="soi-sx-q" type="search" placeholder="Search every article since 2013…" autocomplete="off" enterkeyhint="search">
    <button type="button" class="soi-sx-clear" hidden><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>Clear</button>
  </form>
  <div class="soi-sx-row" data-f="Section"><span class="soi-sx-lbl">Section:</span><div class="soi-sx-chips"></div></div>
  <div class="soi-sx-row" data-f="Year"><span class="soi-sx-lbl">Year:</span><div class="soi-sx-chips"></div></div>
  <p class="soi-sx-status" aria-live="polite"></p>
  <ol class="soi-sx-list"></ol>
  <p class="soi-sx-morewrap"><button type="button" class="soi-btn soi-sx-more" hidden>Show more results</button></p>
</section>
<script>
(function () {{
  var box = document.getElementById('soi-sx'), q = document.getElementById('soi-sx-q'), list = box.querySelector('.soi-sx-list'),
      st = box.querySelector('.soi-sx-status'), clr = box.querySelector('.soi-sx-clear'), more = box.querySelector('.soi-sx-more'),
      pf = null, sel = {{ Section: '', Year: '' }}, res = [], shown = 0, seq = 0, PAGE = 10;
  function esc(t) {{ return String(t).replace(/[&<>"]/g, function (c) {{ return {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }}[c]; }}); }}
  function term() {{ return q.value.trim().replace(/(\\d{{1,3}})\\s*:\\s*(\\d{{1,3}})/g, '$1:$2'); }}
  function chips(name, values) {{
    var row = box.querySelector('[data-f="' + name + '"] .soi-sx-chips');
    row.innerHTML = '<button type="button" data-v="" aria-pressed="true">All</button>' + values.map(function (v) {{ return '<button type="button" data-v="' + esc(v) + '" aria-pressed="false">' + esc(v) + '</button>'; }}).join('');
    row.addEventListener('click', function (e) {{ var b = e.target.closest('button'); if (!b) return; sel[name] = b.dataset.v;
      [].forEach.call(row.children, function (x) {{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }}); run(); }});
  }}
  function filters() {{ var f = {{}}; Object.keys(sel).forEach(function (k) {{ if (sel[k]) f[k] = sel[k]; }}); return f; }}
  function sync() {{
    clr.hidden = !q.value;
    var u = new URL(location.href); if (q.value.trim()) u.searchParams.set('q', q.value.trim()); else u.searchParams.delete('q'); history.replaceState(null, '', u);
  }}
  function run() {{
    sync(); var t = term(), my = ++seq, f = filters();
    if (!t && !Object.keys(f).length) {{ list.innerHTML = ''; st.textContent = ''; more.hidden = true; return; }}
    st.textContent = 'Searching…';
    pf.search(t || null, {{ filters: f }}).then(function (r) {{
      if (my !== seq) return; res = r.results; shown = 0; list.innerHTML = ''; page();
      var n = res.length, bits = [];
      if (t) bits.push('for “' + t + '”'); if (sel.Section) bits.push('in ' + sel.Section); if (sel.Year) bits.push('in ' + sel.Year);
      st.innerHTML = (n ? n.toLocaleString() + (n === 1 ? ' result ' : ' results ') : 'Nothing found ') + esc(bits.join(' ')) +
        ((sel.Section || sel.Year) ? ' · <button type="button" class="soi-sx-reset">Clear all filters</button>' : '');
    }});
  }}
  function page() {{
    var part = res.slice(shown, shown + PAGE); shown += part.length; more.hidden = shown >= res.length;
    Promise.all(part.map(function (r) {{ return r.data(); }})).then(function (ds) {{
      list.insertAdjacentHTML('beforeend', ds.map(function (d) {{
        var m = d.meta || {{}};
        return '<li><a href="' + d.url + '"><span class="soi-sx-iss">' + esc(m.issue || '') + '</span><b>' + esc(m.title || d.url) + '</b><span class="soi-sx-ex">' + d.excerpt + '</span></a></li>';
      }}).join(''));
    }});
  }}
  var timer;
  q.addEventListener('input', function () {{ clearTimeout(timer); timer = setTimeout(run, 220); }});
  clr.addEventListener('click', function () {{ q.value = ''; q.focus(); run(); }});
  more.addEventListener('click', page);
  st.addEventListener('click', function (e) {{ if (!e.target.closest('.soi-sx-reset')) return; sel = {{ Section: '', Year: '' }};
    [].forEach.call(box.querySelectorAll('.soi-sx-chips'), function (row) {{ [].forEach.call(row.children, function (x, k) {{ x.setAttribute('aria-pressed', k ? 'false' : 'true'); }}); }}); run(); }});
  import('/pagefind/pagefind.js').then(function (m) {{ pf = m; return pf.init ? pf.init() : null; }}).then(function () {{ return pf.filters(); }}).then(function (f) {{
    var sec = Object.keys(f.Section || {{}}).sort(function (a, b) {{ return (f.Section[b] || 0) - (f.Section[a] || 0); }});
    var yrs = Object.keys(f.Year || {{}}).sort().reverse();
    chips('Section', sec); chips('Year', yrs);
    var s0 = new URLSearchParams(location.search).get('q'); if (s0) {{ q.value = s0; }} run();
  }});
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
                await idx.add_custom_record(
                    url=f"/issues/{i['slug']}/#soi-{a['id']}", content=content, language="en",
                    meta={"title": a["title"], "issue": label, "section": a["kicker"] or TYPE_LABEL.get(a["type"], "")},
                    filters=filters, sort={"date": i["slug"]})


if __name__ == "__main__":
    build()
