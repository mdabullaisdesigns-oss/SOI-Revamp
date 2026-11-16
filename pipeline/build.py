#!/usr/bin/env python3
"""
Stage 5 - build.  issues/<slug>/issue.json (+ quiz.json, audio.json) ->
issues/<slug>/SOI-<slug>-complete.html : the one block that goes into a Divi
Code module, built from the approved Issue 133 shell (pipeline/templates/).

Audio: an article gets a player only if issues/<slug>/audio.json lists it
(url, duration, sentence times).  Until then it is built without a player and
every sentence is still wrapped in <span class="ev-s"> so that the narration
step only has to add the timings.

Usage: python3 pipeline/build.py <slug> [--preview]
  --preview also writes preview.html: the block inside a mock Divi page.
"""
import html, json, os, re, sys

T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
ABBR = r"(?:Dr|Mr|Mrs|Ms|Prof|St|Sr|Jr|vs|No|pp|p|vol|Vol|ed|eds|etc|e\.g|i\.e|c|d|b|A\.D|B\.C|a\.m|p\.m|[A-Z])"
SENT_SPLIT = re.compile(r"(?<=[.?!])[\"”’')\]]*\s+(?=[\"“‘'(\[]*[A-Z0-9])")
REF = re.compile(r"\((?:[A-Z][A-Za-z’' -]{2,30},? )?\d{1,3}\s?:\s?\d{1,3}(?:\s?[-–]\s?\d{1,3})?\)")
URL = re.compile(r"(?<![\w@/])((?:https?://|www\.)[\w./~%#?=&+-]*[\w/]|[\w.+-]+@[\w-]+(?:\.[\w-]+)+)")
ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
         'stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>')
CHEV = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
        'stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>')
EXTRA_CSS = """
<style>
/* small additions for archive issues (footnotes, source lines, contact lines) */
.soi-ev .ev-body p.ev-fn { font-size: 0.82rem !important; line-height: 1.6 !important; color: var(--ev-muted) !important; margin: 0 0 0.6em !important; }
.soi-ev .ev-body p.ev-contact { text-align: right; font-size: 0.85rem !important; color: var(--ev-muted) !important; margin-top: -0.6em !important; }
.soi-ev .ev-body p.ev-contact a, .soi-ev .ev-body p a.ev-a { color: var(--ev-primary); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; word-break: break-word; }
.soi-ev blockquote.ev-quote, .soi-ev blockquote.ev-ayah { quotes: none; }
.soi-ev .ev-body, .soi-ev .ev-body p, .soi-ev .ev-note { overflow-wrap: break-word; word-wrap: break-word; }
.soi-ev .ev-body a.ev-a, .soi-ev .ev-body p.ev-fn { overflow-wrap: anywhere; }
</style>
"""


def esc(s):
    return html.escape(s, quote=False)


def linkify(escaped):
    def rep(m):
        t = m.group(1)
        href = "mailto:" + t if "@" in t and not t.startswith(("http", "www")) else (t if t.startswith("http") else "https://" + t)
        return f'<a class="ev-a" href="{href}"' + ('' if href.startswith("mailto:") else ' target="_blank" rel="noopener noreferrer"') + f">{t}</a>"
    return URL.sub(rep, escaped)


def run_html(st, text, links=True):
    h = esc(text)
    if st == "ref":
        # a long source line (book title, author) must be allowed to wrap on a phone; a verse number must not
        wrap = ' style="white-space:normal"' if len(re.sub(r"<[^>]+>", "", h)) > 24 else ""
        return f'<span class="ev-ref"{wrap}>{h.strip()}</span>'
    h = REF.sub(lambda m: f'<span class="ev-ref">{m.group(0)}</span>', h)
    if links:
        h = linkify(h)
    if "b" in st:
        h = f"<strong>{h}</strong>"
    if "i" in st:
        h = f"<em>{h}</em>"
    return h


def plain(runs):
    return "".join(r[1] for r in runs)


def sentences(runs, emphasis=True):
    """Runs -> list of HTML strings, one per sentence."""
    text = plain(runs)
    cuts, last = [], 0
    for m in SENT_SPLIT.finditer(text):
        before = text[last:m.start()]
        if re.search(r"(?:^|[\s(“\"])" + ABBR + r"\.$", before) or len(before.split()) < 2:
            continue                                    # "Dr. Khan", initials, list numbers
        cuts.append((last, m.start(), m.end()))
        last = m.end()
    spans = [(a, b) for a, b, _ in cuts] + [(last, len(text))]
    out, pos = [], 0
    bounds = []
    for st, tx in runs:
        bounds.append((pos, pos + len(tx), st))
        pos += len(tx)
    for a, b in spans:
        parts = []
        for s, e, st in bounds:
            lo, hi = max(a, s), min(b, e)
            if lo < hi:
                parts.append(run_html(st if emphasis else ("ref" if st == "ref" else ""), text[lo:hi]))
        h = "".join(parts).strip()
        if h:
            out.append(h)
    return out


def spans(runs, times=None, emphasis=True):
    out = []
    for s in sentences(runs, emphasis):
        t = f' data-t="{times.pop(0)}"' if times else ""
        out.append(f'<span class="ev-s"{t}>{s}</span>')
    return " ".join(out)


def first_para(runs, times):
    """Opening paragraph with a drop cap; a leading quotation mark stays small."""
    text = plain(runs)
    if text[:1] in "“\"‘'" and len(text) > 2:
        q, letter = text[0], text[1]
        rest = [list(r) for r in runs]
        rest[0][1] = rest[0][1][2:]
        inner = spans(rest, times)
        dc = (f'<span class="ev-dc" aria-hidden="true"><span class="ev-dc-q">{esc(q)}</span>'
              f'<span class="ev-dc-l">{esc(letter)}</span></span><span class="sr-only">{esc(q + letter)}</span>')
        inner = inner.replace(">", ">" + dc, 1)
        return f'<p class="ev-first-q">{inner}</p>'
    return f'<p class="ev-first">{spans(runs, times)}</p>'


def link_buttons(links, text):
    out = []
    for u in dict.fromkeys(l.strip() for l in links):
        bare = re.sub(r"^(https?://(www\.)?|mailto:)", "", u).rstrip("/")
        if bare and bare.split("/")[0] in text and (u.startswith("mailto:") or URL.search(text)):
            continue                                    # already a link inside the paragraph
        label = "Email" if u.startswith("mailto:") else re.sub(r"^www\.", "", bare.split("/")[0]) or "Open link"
        out.append(f'<a class="ev-link" href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{esc(label)}{ARROW}</a>')
    return ("<p>" + "".join(out) + "</p>") if out else ""


MAIL_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16v12H4z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M4.5 6.5 12 13l7.5-6.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>'


def contact_pills(text):
    """The editor's contact line ("editor@... Follow Maulana at speakingtree.in (The Times of India)")
    as tidy buttons. Every word of the line stays visible; anything else falls back to plain text."""
    m = re.fullmatch(r"((?:\S+@\s?\S+\.\w+\s*)+)(Follow\s+(?:Maulana|him)\s+at\s+(?:https?://)?(?:www\.)?([\w.-]+\.\w+)/?(?:\s*\((?:The\s+)?Times\s+of\s+India\))?)?\s*", text)
    if not m:
        return None
    out = []
    for mail in re.findall(r"\S+@\s?\S+\.\w+", m.group(1)):
        out.append(f'<a class="ev-sign-pill" href="mailto:{html.escape(mail.replace(" ", ""))}">{MAIL_ICON}<span>{esc(mail)}</span></a>')
    if m.group(2):
        label = re.sub(r"(?:https?://)?(?:www\.)?([\w.-]+\.\w+)/?", r"\1", m.group(2))
        out.append(f'<a class="ev-sign-pill" href="https://www.{html.escape(m.group(3))}/" target="_blank" rel="noopener noreferrer"><span>{esc(label)}</span>{ARROW}</a>')
    return f'<p class="ev-sign-links">{"".join(out)}</p>'


def author_from_bio(text):
    m = re.match(r"^((?:Prof\.?|Dr\.?|Maulana|Mr\.?|Ms\.?)\s+[A-Z][\w’'-]+(?:\s+[A-Z][\w’'-]+){0,2})", text)
    return m.group(1) if m else ""


def render_article(a, audio, photo, player_tpl):
    au = audio.get(a["id"])
    times = list(au["times"]) if au and au.get("times") else None
    items = a["items"]
    body, tail_notes, thought, first_done = [], [], [], False
    section_note = "About this section" if a["type"] in ("qa", "newsletter", "children") else "About the author"
    author = a.get("author", "")
    title_span = f'<span class="ev-s"{" data-t=" + chr(34) + str(times.pop(0)) + chr(34) if times else ""}>{esc(a["title"])}</span>'

    n = 0
    while n < len(items):
        i = items[n]
        k, runs = i["k"], i["runs"]
        text = plain(runs).strip()
        extra = link_buttons(i.get("links", []), text) if i.get("links") else ""
        if k == "p":
            if not first_done and a["type"] in ("article", "qa") and not any(x["k"] == "qh" for x in items[:n]) \
                    and a["type"] == "article" and len(text.split()) > 12:
                body.append(first_para(runs, times))
            else:
                body.append(f"<p>{spans(runs, times)}</p>")
            first_done = True
        elif k == "lead":
            body.append(f'<p class="ev-lead">{spans(runs, times, emphasis=False)}</p>')
        elif k == "h":
            body.append(f'<h3 class="ev-h">{spans(runs, times, emphasis=False)}</h3>')
        elif k == "qh":
            # one wrapper: the heading is a flex row, so bare sentence spans would sit side by side as columns
            body.append(f'<h3 class="ev-qh"><span>{spans(runs, times, emphasis=False)}</span></h3>')
        elif k in ("quote", "ayah"):
            body.append(f'<blockquote class="ev-ayah">{spans(runs, times, emphasis=False)}</blockquote>')
        elif k == "bismillah":
            body.append(f'<p class="ev-bismillah">{spans(runs, times, emphasis=False)}</p>')
        elif k == "pull":
            body.append(f'<blockquote class="ev-quote">{esc(text)}</blockquote>')
        elif k == "thought":
            thought.append(f'<blockquote class="ev-thought"><p>{spans(runs, times, emphasis=False)}</p></blockquote>')
        elif k == "bio":
            author = author or author_from_bio(text)
            note = (f'<aside class="ev-note"><span class="ev-note-label">{section_note}</span>'
                    f'<p>{linkify(esc(text))}</p></aside>')
            if re.search(r"editor.?in.?chief|chief editor", a.get("kicker", "") + " " + a.get("section", ""), re.I):
                body.insert(0, note.replace(f">{section_note}<", ">About the Editor-in-Chief<"))   # as in the magazine: introduced before the article
            else:
                (body if a["type"] != "article" else tail_notes).append(note)
        elif k == "intro":
            paras = [f"<p>{spans(runs, times)}</p>"]
            while n + 1 < len(items) and items[n + 1]["k"] == "intro":
                n += 1
                paras.append(f"<p><em>{esc(plain(items[n]['runs']).strip())}</em></p>")
            body.append('<aside class="ev-note"><span class="ev-note-label">From the scriptures</span>' + "".join(paras) + "</aside>")
        elif k == "qa_intro":
            m = re.match(r"^[“\"]?(The remedy for ignorance is asking questions\.?)[”\"]?\s*\(?([^)]{0,40}?)\)?\s+(The spirit of.*)$", text, re.S)
            if m:
                body.append('<aside class="ev-intro" aria-label="About this section"><span class="ev-intro-tag">'
                            '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0 10 5 5 10 0 5z"/></svg>Before we begin</span>'
                            f'<p class="ev-intro-saying">“{spans([["", m.group(1)]], times)}”</p>'
                            f'<p class="ev-intro-who">— {esc(m.group(2).strip() or "Prophet Muhammad")}</p>'
                            f'<p class="ev-intro-text">{spans([["", m.group(3)]], times)}</p></aside>')
            else:
                body.append(f'<aside class="ev-intro" aria-label="About this section"><p class="ev-intro-text">{spans(runs, times)}</p></aside>')
        elif k == "signoff":
            name = re.split(r"\s+\S*@", text)[0].strip()
            rest = text[len(name):].strip()
            nxt = items[n + 1] if n + 1 < len(items) else None
            pills = contact_pills(rest) if rest else None
            if not rest and nxt and nxt["k"] == "contact":
                pills = contact_pills(plain(nxt["runs"]).strip())
                if pills:
                    n += 1; extra = ""                  # the contact line is shown as buttons inside the sign-off
            if pills:
                body.append(f'<div class="ev-sign"><p class="ev-byline">{esc(name)}</p>{pills}</div>')
            else:
                body.append(f'<p class="ev-byline">{esc(name)}</p>')
                if rest:
                    body.append(f'<p class="ev-contact">{linkify(esc(rest))}</p>')
        elif k == "contact":
            pills = contact_pills(text)
            if pills:
                body.append(f'<div class="ev-sign">{pills}</div>'); extra = ""
            else:
                body.append(f'<p class="ev-contact">{linkify(esc(text))}</p>')
        elif k == "gloss":                               # glossary entry: term in bold, then its meaning
            body.append(f'<p class="ev-fn">{run_inline(runs)}</p>')
        elif k in ("footnote", "small"):
            body.append(f'<p class="ev-fn">{linkify(esc(text))}</p>')
        elif k == "filler_h":
            label, paras, sig = text, [], ""
            while n + 1 < len(items) and items[n + 1]["k"] in ("filler_p", "filler_sig", "other"):
                n += 1
                if items[n]["k"] == "filler_sig":
                    sig = plain(items[n]["runs"]).strip(" -–—")
                else:
                    paras.append(items[n]["runs"])
            if re.fullmatch(r"in focus", label.strip(), re.I) and sig and paras:
                quote = paras.pop()
                tail_notes.append('<aside class="ev-note"><span class="ev-note-label">In Focus</span>'
                                  + "".join(f"<p>{run_inline(p)}</p>" for p in paras)
                                  + f'<div class="ev-note-person"><img decoding="async" src="{photo}" alt="Maulana Wahiduddin Khan" width="64" height="64">'
                                  f'<p class="ev-note-quote">{esc(plain(quote).strip())}<span>{esc(sig)}</span></p></div></aside>')
            else:
                tail_notes.append(f'<aside class="ev-note"><span class="ev-note-label">{esc(label)}</span>'
                                  + "".join(f"<p>{run_inline(p)}</p>" for p in paras)
                                  + (f'<p class="ev-note-quote"><span>{esc(sig)}</span></p>' if sig else "") + "</aside>")
        elif k == "filler_p":
            tail_notes.append(f'<aside class="ev-note"><p>{run_inline(runs)}</p></aside>')
        else:                                           # unclassified: keep it visible, never drop
            body.append(f'<aside class="ev-note"><p>{run_inline(runs)}</p></aside>')
        if extra:
            body.append(extra)
        n += 1

    words = a["words"]
    meta = [f"<span>{esc(x)}</span>" for x in ([author] if author else [])]
    if a["type"] == "scripture" and not author:
        meta.append("<span>Translation and commentary by Maulana Wahiduddin Khan</span>")
    meta.append(f"<span>{max(1, round(words / 200))} min read</span>")
    meta_html = "<span>·</span>".join(meta)
    player = ""
    if au:
        player = '<div class="ev-pl-spot">' + player_tpl.replace("{{DURATION}}", str(au["duration"])) \
            .replace("{{AUDIO_URL}}", au["url"]).replace("{{AUDIO_FILE}}", os.path.basename(au["url"])) + "</div>"
    kicker = a.get("kicker") or {"qa": "Questions and Answers", "scripture": "From the Scriptures",
                                 "newsletter": "News from CPS International", "children": "Children’s Corner"}.get(a["type"], "Spirit of Islam")
    parts = body + tail_notes + thought[:1]
    if thought:
        parts.append('<div class="ev-end" aria-hidden="true"><i></i><i></i><i></i></div>')
    return f"""  <!-- ===================== {a['n']:02d} · {a['title']} ===================== -->
  <section class="ev-item" id="soi-{a['id']}" data-audio="" data-audio-status="{'ready' if au else 'none' if a.get('audio') is False else 'pending'}" role="listitem">
    <button class="ev-tab" type="button" aria-expanded="false">
      <span class="ev-num">{a['n']:02d}</span>
      <span class="ev-tab-text">
        <span class="ev-kicker">{esc(kicker)}</span>
        <span class="ev-tab-title">{title_span}</span>
      </span>
      <span class="ev-chev">{CHEV}</span>
    </button>
    <div class="ev-panel"><div class="ev-panel-inner"><div class="ev-content">
      <div class="ev-meta">{meta_html}</div>
      {player}
      <div class="ev-body">
        {chr(10).join('        ' + p for p in parts).strip()}
      </div>
    </div></div></div>
  </section>
"""


def run_inline(runs):
    return "".join(run_html(st, tx) for st, tx in runs).strip()


def main():
    slug = sys.argv[1]
    base = os.path.join("issues", slug)
    issue = json.load(open(os.path.join(base, "issue.json"), encoding="utf-8"))
    load = lambda name, default: json.load(open(os.path.join(base, name), encoding="utf-8")) if os.path.exists(os.path.join(base, name)) else default
    quiz = load("quiz.json", {"questions": []})
    audio = load("audio.json", {})
    # a recording that does not match the article's text is not offered: the article waits for a new narration
    audio = {k: v for k, v in audio.items() if "times" in v and not v.get("flag") and not v.get("error")}
    shell = open(os.path.join(T, "issue-shell.html"), encoding="utf-8").read()
    player_tpl = open(os.path.join(T, "player.html"), encoding="utf-8").read()
    photo = open(os.path.join(T, "infocus-photo.txt"), encoding="utf-8").read().strip()

    number, period = issue.get("number"), issue.get("period", slug)
    short = f"Issue {number} · {issue.get('period_short', period)}" if number else period
    long_ = f"Spirit of Islam, Issue {number} ({issue.get('period_short', period)})" if number else f"Spirit of Islam, {period}"
    ids = {a["id"] for a in issue["articles"]}
    for q in quiz["questions"]:
        q["link"] = "soi-" + q["link"].removeprefix("soi-")
        if q["link"][4:] not in ids:
            sys.exit(f"quiz question points to unknown article: {q['link']}")
    arts = "".join(render_article(a, audio, photo, player_tpl) for a in issue["articles"])
    n_audio = sum(1 for a in issue["articles"] if a["id"] in audio)
    header = (f"<!-- ===== SPIRIT OF ISLAM · {short.upper()} · COMPLETE SECTION =====\n"
              f"     E-version ({len(issue['articles'])} articles, {n_audio} with read-along audio) + Readers' Reflection Quiz + go-to-top.\n"
              f"     Paste the whole file into ONE Divi \"Code\" module (Regular section, single column).\n"
              f"     Built by pipeline/build.py from {issue['pdf']}.\n-->")
    out = shell.replace("{{HEADER_COMMENT}}", header).replace("{{ARTICLES}}", arts.rstrip() + "\n" + EXTRA_CSS.strip()) \
        .replace("{{ISSUE_SHORT_JS}}", json.dumps(short, ensure_ascii=False)) \
        .replace("{{ISSUE_SHORT}}", esc(short)) \
        .replace("{{ISSUE_LONG_JS}}", json.dumps(long_, ensure_ascii=False)) \
        .replace("{{SALUTE_JS}}", json.dumps(f" · {('Issue ' + str(number)) if number else period} reflection complete", ensure_ascii=False)) \
        .replace("{{QUESTIONS}}", json.dumps(quiz["questions"], ensure_ascii=False, indent=2))
    # EXTRA_CSS must sit outside the list wrapper
    out = out.replace(EXTRA_CSS.strip() + "\n</div>", "</div>\n" + EXTRA_CSS.strip(), 1)
    if not quiz["questions"]:
        a, b = out.index("<!-- ===== READERS' REFLECTION QUIZ"), out.index("</script>", out.index('<section id="soi-quiz"')) + 9
        out = out[:a] + "<!-- quiz pending: issues/%s/quiz.json not written yet -->" % slug + out[b:]
    assert "{{" not in out, re.findall(r"\{\{\w+\}\}", out)
    name = f"SOI-{slug}-complete.html"
    open(os.path.join(base, name), "w", encoding="utf-8").write(out)
    print(f"{slug}: {name}  {len(out) // 1024} KB, {len(issue['articles'])} articles, {n_audio} with audio, "
          f"{len(quiz['questions'])} quiz questions")
    if "--preview" in sys.argv:
        page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(short)} – preview</title>
<style>body{{margin:0;background:#EEEEE5;font-family:sans-serif}}#main-header{{position:fixed;top:0;left:0;right:0;height:60px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.15);z-index:999;display:flex;align-items:center;padding:0 20px;font-weight:700;color:#204E60}}
#page-container{{padding-top:60px}}.et_pb_section{{padding:54px 0;background:#fff}}.et_pb_row{{width:80%;max-width:1080px;margin:auto;padding:27px 0}}
.mock-banner{{max-width:880px;margin:16px auto;padding:28px;border-radius:18px;background:#EEEEE5;border:1px solid #D7D8CA;text-align:center;color:#204E60;font-weight:700}}
footer{{background:#173A48;color:#EEEEE5;padding:60px 20px;text-align:center}}</style></head>
<body><div id="main-header">Spirit of Islam – mock Divi page</div><div id="page-container"><div id="et-main-area">
<div class="mock-banner">A Magazine for The Journey of Life · {esc(short)}</div>
<div class="et_pb_section"><div class="et_pb_row"><div class="et_pb_column"><div class="et_pb_module et_pb_code"><div class="et_pb_code_inner">
{out}
</div></div></div></div></div></div><footer>Footer</footer></div></body></html>"""
        open(os.path.join(base, "preview.html"), "w", encoding="utf-8").write(page)


if __name__ == "__main__":
    main()
