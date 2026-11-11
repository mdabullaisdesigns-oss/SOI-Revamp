#!/usr/bin/env python3
"""
Stage 2 - structure.  issues/<slug>/raw/pages.json -> issues/<slug>/issue.json

Rebuilds the articles from the magazine's own typography (the magazine has used
the same type system since 2013): 16pt caps = title, 11pt italic = subtitle,
10pt = body, 10pt bold = sub-heading, boxed italic/bold lines = pull quote,
big initial = drop cap, end mark = end of article.

The text itself is never retyped - every word comes from the PDF - so the only
judgement is *which role each block has*.  Anything the rules cannot place is
kept and listed in issues/<slug>/review.md; nothing is dropped silently.
Corrections go in issues/<slug>/overrides.json (see docs/pipeline.md).

Usage: python3 pipeline/structure.py <slug>
"""
import json, os, re, sys, statistics, collections

SMALL = {"a", "an", "the", "and", "or", "but", "nor", "of", "in", "to", "for", "at", "on", "by",
         "with", "from", "as", "into", "vs"}
ACRONYMS = {"CPS", "USA", "UK", "UN", "FAQ", "FAQS", "AI", "TV", "II", "III", "IV", "CE", "BC", "AD", "DNA"}
NON_ARTICLE = re.compile(r"^(CONTENTS|ABOUT THE MAGAZINE|NOTICE|SUBSCRIBE|SPIRIT OF ISLAM)$", re.I)
SECTION_TYPES = [(r"WORD OF GOD", "scripture"), (r"ASK MAULANA|QUESTIONS ANSWERED", "qa"),
                 (r"NEWSLETTER", "newsletter"), (r"CHILDREN", "children")]
END_MARKS = "❑❏□❒"            # the little box that closes an article
SENT_END = re.compile(r"[.?!:;\"”’)\]❑]\s*$")


def fam(f):
    return f.split("+")[-1]


def line_role(l, page_h):
    f, sz, t, y = fam(l["f"]), l["sz"], l["t"].strip(), l["bb"][1]
    if l.get("rot"):
        return "rot"
    if y > page_h - 50 and (re.search(r"Spirit of Islam", t, re.I) or re.fullmatch(r"\d{1,3}", t)) and sz <= 9.5:
        return "footer"
    if sz >= 30 and len(t) <= 2:
        return "dropcap"
    if f.startswith("Wingdings"):
        return "endmark"
    if "nevis" in f:
        if sz >= 13.4 and t.upper() == t:
            return "title"
        if sz >= 11:
            return "pull"
        return "label"
    if f.startswith("GoudyOldStyleT-Bold") and sz <= 10.5 and t.upper() == t and y < 110:
        return "label"
    if f.startswith("OpenSans"):
        bold, ital = "Bold" in f, "Italic" in f
        semi = "Semibold" in f
        if 9.6 <= sz <= 10.6:
            # a heading / quote line is set wholly in that style; a body line may merely contain bold words
            rs = [st for st, tx in (l.get("runs") or []) if tx.strip()]
            all_b, all_i = bool(rs) and all("b" in st for st in rs), bool(rs) and all("i" in st for st in rs)
            if semi and ital and all_i:
                return "pull"
            if bold and ital and all_b and all_i:
                return "signoff"
            if bold and not ital and all_b:
                return "subhead"
            return "body"
        if 10.6 < sz <= 11.5 and ital:
            return "subtitle"
        if 11.5 < sz <= 12.5 and bold and ital:
            return "fillertitle"
        if sz < 9.6 and (re.match(r"^[\(\[]?\d{1,3}\s*:\s*\d", t) or (t.startswith("(") and t.endswith((")", ").")) and len(t.split()) <= 10)):
            return "ref"
        if 8.6 <= sz < 9.6:
            return "small" if bold and not ital else "bio"
        if sz < 8.6:
            return "small"
    return "other"


def title_case(s):
    words = s.split()
    out = []
    for i, w in enumerate(words):
        core = re.sub(r"[^\w’'-]", "", w)
        if core.upper() in ACRONYMS:
            out.append(w.upper())
        elif i and core.lower() in SMALL and not out[-1].endswith(":"):
            out.append(w.lower())
        else:
            out.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
    return " ".join(out)


def slugify(s):
    s = s.lower().replace("’", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


class Joiner:
    """Joins the lines of a paragraph, undoing line-end hyphenation."""

    def __init__(self, pages):
        self.vocab = collections.Counter()
        for p in pages:
            for b in p["blocks"]:
                for l in b["lines"]:
                    for w in re.findall(r"[A-Za-z’'-]+", l["t"][:-1] if l["t"].endswith("-") else l["t"]):
                        self.vocab[w.lower()] += 1
        self.cases = collections.Counter()
        for p in pages:
            for b in p["blocks"]:
                for l in b["lines"]:
                    if l["sz"] <= 10.6 and l["t"].upper() != l["t"]:
                        self.cases.update(re.findall(r"(?<=[a-z,;] )[A-Za-z\u2019']+", l["t"]))
        self.log = []

    def join(self, lines):
        runs = []
        for i, l in enumerate(lines):
            lr = [list(r) for r in l.get("runs") or [["", l["t"]]]]
            lr[0][1] = lr[0][1].lstrip()
            lr[-1][1] = lr[-1][1].rstrip()
            lr = [r for r in lr if r[1]]
            if not lr:
                continue
            sep = " "
            if runs and runs[-1][1].endswith("-"):
                a = re.findall(r"[A-Za-z’']+-$", runs[-1][1])
                b = re.findall(r"^[a-z’']+", lr[0][1])
                if a and b:
                    whole, hyph = (a[0][:-1] + b[0]).lower(), (a[0] + b[0]).lower()
                    if self.vocab[whole] and not self.vocab[hyph]:
                        runs[-1][1] = runs[-1][1][:-1]
                        sep = ""
                    elif self.vocab[hyph] or (self.vocab[a[0][:-1].lower()] and self.vocab[b[0].lower()]):
                        sep = ""
                    else:                                   # unknown either way: keep the hyphen, flag it
                        sep = ""
                        self.log.append(a[0] + b[0])
                else:
                    sep = "" if not re.search(r"\s-$", runs[-1][1]) else " "
            if runs and sep:
                runs[-1][1] += sep
            for st, tx in lr:
                if runs and runs[-1][0] == st:
                    runs[-1][1] += tx
                else:
                    runs.append([st, tx])
        for r in runs:
            r[1] = re.sub(r"\s+", " ", r[1])
        return runs


def plain(runs):
    return "".join(r[1] for r in runs).strip()


def build_units(page, overrides, joiner):
    """Lines of one page -> ordered units (paragraph-level pieces with a role)."""
    units = []
    forced = overrides.get("roles", {})
    for b in page["blocks"]:
        cur = None
        pitch = statistics.median([b["lines"][i + 1]["bb"][1] - b["lines"][i]["bb"][1]
                                   for i in range(len(b["lines"]) - 1)] or [12.5]) or 12.5
        pitch = max(pitch, 9.0)
        for l in b["lines"]:
            if not l["t"].strip():
                continue
            role = forced.get(b["id"]) or line_role(l, page["h"])
            new = cur is None or cur["role"] != role or (l["bb"][1] - cur["lines"][-1]["bb"][1]) > 1.38 * pitch \
                or role in ("dropcap", "endmark")
            if new:
                cur = {"role": role, "lines": [], "page": page["n"], "ids": [b["id"]], "pitch": pitch}
                units.append(cur)
            cur["lines"].append(l)
    for u in units:
        u["y0"] = min(l["bb"][1] for l in u["lines"])
        u["y1"] = max(l["bb"][3] for l in u["lines"])
        u["x0"] = min(l["bb"][0] for l in u["lines"])
        u["x1"] = max(l["bb"][2] for l in u["lines"])
    # a paragraph split over two blocks (text wrapping round a quote box) is one paragraph
    units.sort(key=lambda u: (u["y0"], u["x0"]))
    merged = []
    for u in units:
        m = merged[-1] if merged else None
        if u["role"] == "pull":                      # a boxed quote sits beside body text: look past the paragraphs
            m = next((x for x in reversed(merged[-8:]) if x["role"] == "pull"), None)
        same_flow = m and m["role"] == u["role"] and u["role"] in ("body", "pull", "title", "bio", "other", "small")
        if same_flow and u["role"] in ("pull", "title"):
            gap = u["y0"] - m["y1"]
            open_end = not SENT_END.search(m["lines"][-1]["t"])   # a quote box whose sentence is still running
            close = u["x0"] < m["x1"] and m["x0"] < u["x1"] and \
                (gap < (22 if u["role"] == "title" else 16) or (u["role"] == "pull" and gap < 70 and open_end))
        elif same_flow:
            close = 0 <= u["lines"][0]["bb"][1] - m["lines"][-1]["bb"][1] <= 1.38 * max(m["pitch"], u["pitch"]) \
                and fam(u["lines"][0]["f"]).split("-")[0] == fam(m["lines"][-1]["f"]).split("-")[0]
        else:
            close = False
        if close:
            m["lines"] += u["lines"]
            m["ids"] += [i for i in u["ids"] if i not in m["ids"]]
            m["y1"], m["x0"], m["x1"] = max(m["y1"], u["y1"]), min(m["x0"], u["x0"]), max(m["x1"], u["x1"])
        else:
            merged.append(u)
    for u in merged:
        u["lines"].sort(key=lambda l: (round(l["bb"][1] / 3), l["bb"][0]))
        u["runs"] = joiner.join(u["lines"])
        u["text"] = plain(u["runs"])
        u["links"] = [k["uri"] for k in page["links"]
                      if u["x0"] - 2 <= (k["bb"][0] + k["bb"][2]) / 2 <= u["x1"] + 2
                      and u["y0"] - 2 <= (k["bb"][1] + k["bb"][3]) / 2 <= u["y1"] + 2]
    return merged


def apply_dropcap(letter, runs, log, vocab=None, cases=None):
    text = plain(runs)
    toks = text.split()
    if not toks:
        return runs
    first = toks[0]
    if letter in "“\"‘'":
        glue = ""
    elif first[:1].islower():
        glue = " "                                   # "A" + "careful study"
    elif len(first) == 1 and len(toks) > 1 and toks[1][:1].isupper() and toks[1].isupper():
        glue = " "                                   # "E" + "F SCHUMACHER"
    elif letter in "AI" and vocab is not None and not vocab[(letter + re.sub(r"\W", "", first)).lower()] \
            and vocab[re.sub(r"\W", "", first).lower()]:
        glue = " "                                   # "A" + "NUMBER of" (but "A" + "LL" stays "All")
    else:
        glue = ""                                    # "W" + "ITH an area"
    runs = [list(r) for r in runs]
    runs[0][1] = letter + glue + runs[0][1]
    # the magazine sets the first word(s) in capitals after a drop cap: back to normal case
    text = plain(runs)
    m = re.match(r"^((?:[“\"‘']?[A-Z][A-Z’'.,-]*\s+)*(?:[“\"‘']?[A-Z][A-Z’'.,-]*))", text)
    if m:
        lead = m.group(1)
        def recase(n, w):
            core = re.sub(r"\W", "", w)
            if len(core) <= 1 or core in ACRONYMS:
                return w
            cap = re.sub(r"[A-Z]+", lambda g: g.group(0)[:1] + g.group(0)[1:].lower(), w, count=1)
            # after the first word, use whichever spelling the issue itself uses most (Quran / age)
            if n and cases is not None and cases[core.lower()] > cases[core.capitalize()]:
                return cap[:1].lower() + cap[1:] if cap[:1].isalpha() else cap.lower()
            return cap
        fixed = " ".join(recase(n, w) for n, w in enumerate(lead.split(" ")))
        if fixed != lead:
            log.append(f"{lead!r} -> {fixed!r}")
            n, out = len(lead), []
            for st, tx in runs:
                take = min(n, len(tx))
                if take:
                    out.append([st, fixed[len(lead) - n:len(lead) - n + take] + tx[take:]])
                    n -= take
                else:
                    out.append([st, tx])
            runs = out
    return runs


def main():
    slug = sys.argv[1]
    base = os.path.join("issues", slug)
    pages = json.load(open(os.path.join(base, "raw", "pages.json"), encoding="utf-8"))
    ov_path = os.path.join(base, "overrides.json")
    ov = json.load(open(ov_path, encoding="utf-8")) if os.path.exists(ov_path) else {}
    joiner = Joiner(pages)
    skip_pages = {1: "cover"}
    skip_pages.update({int(k): v for k, v in ov.get("skip_pages", {}).items()})
    breaks = set(ov.get("end_before", []))

    articles, skipped, lead_log = [], [], []
    cur, ended, dropcap, last_p_page = None, False, None, None

    def skip(u, why):
        if u["role"] in ("footer", "rot"):
            return
        skipped.append({"page": u["page"], "ids": u["ids"], "role": u["role"], "why": why,
                        "words": len(u["text"].split()), "text": u["text"]})

    def art_type(a):
        names = a.get("section", "") + " " + a["title_raw"] + " " + a.get("kicker", "")
        return next((t for rx, t in SECTION_TYPES if re.search(rx, names, re.I)), "article")

    def only_bio(a):
        return all(i["k"] == "bio" for i in a["items"])

    def add(kind, u, **extra):
        item = {"k": kind, "runs": u["runs"], "page": u["page"], "ids": u["ids"]}
        if u.get("links"):
            item["links"] = u["links"]
        item.update(extra)
        cur["items"].append(item)
        return item

    for page in pages:
        units = build_units(page, ov, joiner)
        if page["n"] in skip_pages:
            for u in units:
                skip(u, skip_pages[page["n"]])
            if cur:
                cur, ended = None, False
            continue
        titles = [u for u in units if u["role"] == "title"]
        top_title = titles and titles[0]["y0"] < 110
        # an article that has ended does not continue onto the next page
        first_real = next((u for u in units if u["role"] not in ("footer", "rot")), None)
        if cur and ended and not titles:
            if first_real and first_real["role"] == "fillertitle" and not cur.get("skip"):
                pass                                 # e.g. the "In Focus" page that follows the editorial
            else:
                cur, ended = None, False
        page_has_body = any(u["role"] == "body" for u in units)
        if cur and not titles and not page_has_body:
            cur, ended = None, False                 # advert / notice page with no article text
        pending_kicker = None
        for ui, u in enumerate(units):
            role = u["role"]
            if any(i in breaks for i in u["ids"]):
                cur, ended = None, False
            if role in ("footer", "rot"):
                continue
            if role == "title":
                text = re.sub(r"\s+", " ", u["text"]).strip()
                if NON_ARTICLE.match(text):
                    cur, ended = {"skip": text, "items": []}, False
                    skip(u, "non-article page: " + text.title())
                    continue
                first_on_page = u is titles[0]
                fresh = cur and not cur.get("skip") and only_bio(cur) and cur["page"] == page["n"] and not cur.get("kicker_from_title")
                if not first_on_page and fresh and cur["title_raw"]:
                    # second big heading on the page: the first was the section name
                    cur["kicker"] = title_case(cur["title_raw"])
                    cur["section"] = cur["title_raw"]
                    cur["title_raw"], cur["title"] = text, title_case(text)
                    cur["kicker_from_title"] = True
                    continue
                cur = {"title_raw": text, "title": title_case(text), "kicker": pending_kicker or "",
                       "author": "", "page": page["n"], "pages": [page["n"], page["n"]], "items": []}
                pending_kicker = None
                articles.append(cur)
                ended, dropcap = False, None
                continue
            if role == "label" and u["y0"] < 110 and (not cur or cur.get("skip") or only_bio(cur) or top_title):
                if cur and not cur.get("skip") and cur["page"] == page["n"] and only_bio(cur):
                    cur["kicker"] = title_case(u["text"])
                else:
                    pending_kicker = title_case(u["text"])
                continue
            if cur is None or cur.get("skip"):
                skip(u, "outside any article" if cur is None else "non-article page: " + cur["skip"].title())
                continue
            cur["pages"][1] = page["n"]
            if role == "subtitle" and not any(i["k"] in ("p", "quote") for i in cur["items"]):
                if cur.get("kicker_from_title") or cur["kicker"]:
                    cur["subtitle"] = u["text"]
                else:
                    cur["kicker"] = u["text"]
                continue
            if role == "dropcap":
                dropcap = u["text"].strip()
                continue
            if role == "endmark":
                ended = True
                continue
            if ended and role not in ("fillertitle",) and not cur.get("filler_open"):
                if role in ("body", "bio") and cur["items"] and cur["items"][-1]["k"] in ("signoff", "contact") \
                        and len(u["text"].split()) <= 16:
                    add("contact", u)
                elif role == "body" and len(u["text"].split()) < 25 and re.search(r"@|www\.|https?:|\d{5}", u["text"]):
                    skip(u, "after the end of the article (notice or advert)")
                elif role == "body":
                    cur["filler_open"] = True
                    add("filler_p", u)
                elif role == "pull":
                    add("pull", u)
                elif role == "other" and len(u["text"].split()) >= 6 and not re.search(r"@|www\.|https?:|subscri", u["text"], re.I):
                    add("thought", u, source="quote panel after the article")
                elif role == "signoff" and len(u["text"].split()) <= 8:
                    add("signoff", u)
                    name = re.split(r"\s+\S*@", u["text"])[0].strip(" -\u2013\u2014")
                    if not cur["author"] and "@" not in name and 1 < len(name.split()) <= 5:
                        cur["author"] = name
                else:
                    skip(u, "after the end of the article (notice or advert)")
                continue
            if role == "fillertitle":
                cur["filler_open"] = True
                add("filler_h", u)
                continue
            if cur.get("filler_open"):
                add("filler_p" if role == "body" else "filler_sig" if role == "signoff" else "other", u,
                    font=fam(u["lines"][0]["f"]), size=u["lines"][0]["sz"])
                continue
            if role == "body":
                runs = u["runs"]
                if dropcap:
                    runs = apply_dropcap(dropcap, runs, lead_log, joiner.vocab, joiner.cases)
                    dropcap = None
                if runs and runs[-1][1].rstrip()[-1:] in END_MARKS:
                    runs[-1][1] = runs[-1][1].rstrip()[:-1].rstrip()
                    ended = True
                elif runs and re.search(r"[.?!\u201d\u2019\")\]]\s+o$", plain(runs)):
                    runs[-1][1] = re.sub(r"\s+o\s*$", "", runs[-1][1])   # the end box prints as a lone "o"
                    if not runs[-1][1] and len(runs) > 1:
                        runs = runs[:-1]
                        runs[-1][1] = runs[-1][1].rstrip()
                    ended = True
                u["runs"] = [r for r in runs if r[1]]
                txt = plain(u["runs"])
                if not txt:
                    continue
                tail = cur["items"][-1] if cur["items"] else None
                if tail and tail["k"] in ("ayah", "qh") and tail["ids"][-1] == u["ids"][0] and not SENT_END.search(plain(tail["runs"])):
                    tail["runs"][-1][1] += " "       # last line of a verse / question that carries its reference
                    tail["runs"] += u["runs"]
                    if tail["page"] != page["n"]:
                        tail["page_to"] = page["n"]
                    continue
                prev = next((i for i in reversed(cur["items"]) if i["k"] in ("p", "quote", "h", "qh")), None)
                if prev and prev["k"] in ("p", "quote") and prev["page"] != page["n"] and last_p_page != page["n"] \
                        and art_type(cur) not in ("newsletter", "children") \
                        and (not SENT_END.search(plain(prev["runs"])) or txt[:1].islower()) and not prev.get("closed"):
                    if prev["runs"][-1][1].endswith("-") and txt[:1].islower():
                        prev["runs"][-1][1] = prev["runs"][-1][1]
                    else:
                        prev["runs"][-1][1] += " "
                    prev["runs"] += u["runs"]
                    prev["ids"] += u["ids"]
                    prev["page_to"] = page["n"]
                else:
                    kind = "quote" if all("i" in r[0] for r in u["runs"] if r[1].strip()) and len(txt.split()) > 3 else "p"
                    add(kind, u)
                last_p_page = page["n"]
            elif role == "subhead":
                add("qh" if re.search(SECTION_TYPES[1][0], cur.get("section", cur["title_raw"]), re.I) and u["text"].rstrip().endswith("?") else "h", u)
            elif role == "pull":
                add("pull", u)
            elif role == "bio":
                add("small" if any(i["k"] in ("p", "quote") for i in cur["items"]) else "bio", u)
            elif role == "signoff" and art_type(cur) == "qa":
                add("qh", u)
            elif role == "signoff" and art_type(cur) == "scripture":
                prev = cur["items"][-1] if cur["items"] else None
                if prev and prev["k"] == "ayah" and not SENT_END.search(plain(prev["runs"])):
                    prev["runs"][-1][1] += " "
                    prev["runs"] += u["runs"]
                    prev["ids"] += u["ids"]
                    if prev["page"] != page["n"]:
                        prev["page_to"] = page["n"]
                else:
                    add("ayah", u)
            elif role == "signoff" and (art_type(cur) in ("children", "newsletter") or ("@" not in u["text"] and len(u["text"].split()) > 6)):
                add("quote" if len(u["text"].split()) > 12 else "h", u)
            elif role == "signoff":
                add("signoff", u)
                name = re.split(r"\s+\S+@|\s+[\w.-]+\s*@", u["text"])[0].strip(" -–—")
                if not cur["author"] and 1 < len(name.split()) <= 5 and "@" not in name:
                    cur["author"] = name
            elif role == "ref":
                prev = cur["items"][-1] if cur["items"] else None
                if prev and prev["k"] in ("quote", "p", "ayah", "lead"):
                    prev["runs"].append(["ref", " " + u["text"]])
                else:
                    add("p", u)
            elif role in ("small", "bio") and cur["items"] and cur["items"][-1]["ids"][-1] == u["ids"][0] \
                    and cur["items"][-1]["k"] in ("ayah", "quote", "p", "qh") and not SENT_END.search(plain(cur["items"][-1]["runs"])):
                cur["items"][-1]["runs"][-1][1] += " "
                cur["items"][-1]["runs"] += u["runs"]
            elif role == "small":
                add("footnote" if re.match(r"^\d+[.)]?\s", u["text"]) or u["y0"] > page["h"] - 120 else "small", u)
            elif role == "thought":
                add("thought", u)
            elif role.startswith("skip"):
                skip(u, role.partition(":")[2] or "left out by override")
            else:
                add("other", u, font=fam(u["lines"][0]["f"]), size=u["lines"][0]["sz"])
            if ended and role == "body":
                pass

    # ---- finish every article -------------------------------------------------
    out, seen = [], collections.Counter()
    for a in articles:
        if not a["items"]:
            skipped.append({"page": a["page"], "ids": [], "role": "title", "why": "heading with no text under it",
                            "words": 0, "text": a["title_raw"]})
            continue
        sec = a.get("section", a["title_raw"])
        a["type"] = art_type(a)
        body = [i for i in a["items"] if i["k"] in ("p", "quote")]
        if body and sum(i["k"] == "quote" for i in body) > 0.6 * len(body):
            for i in body:
                i["k"] = "p"                         # an article set wholly in italics is still body text
        for i in a["items"]:
            if i["k"] in ("p", "bio", "quote") and re.search(r"remedy for ignorance", plain(i["runs"]), re.I):
                i["k"] = "qa_intro"
        if a["type"] == "scripture":
            for i in a["items"]:
                if re.search(r"^In the name of God", plain(i["runs"])):
                    i["k"] = "bismillah"
                    break
                if i["k"] in ("h", "ayah"):
                    break
                i["k"] = "intro"
            for i in a["items"]:
                if i["k"] in ("p", "quote") and re.search(r"^In the name of God", plain(i["runs"])) and len(plain(i["runs"]).split()) < 14:
                    i["k"] = "bismillah"
        merged = []
        for i in a["items"]:                         # two halves of one small-print block
            m = merged[-1] if merged else None
            if m and {m["k"], i["k"]} <= {"bio", "small", "intro"} and m["ids"][-1] == i["ids"][0]:
                m["runs"][-1][1] += " "
                m["runs"] += i["runs"]
            else:
                merged.append(i)
        a["items"] = merged
        first = next((i for i in a["items"] if i["k"] in ("p", "quote")), None)
        if first and first["k"] == "quote" and a["type"] == "article":
            first["k"] = "lead"                      # italic standfirst that opens the article
        pulls = [i for i in a["items"] if i["k"] == "pull"]
        if pulls and a["type"] == "article" and not any(i["k"] == "thought" for i in a["items"]):
            last = pulls[-1]
            a["items"].remove(last)
            last["k"] = "thought"                   # the last boxed quote closes the article
            pos = next((n for n, i in enumerate(a["items"]) if i["k"] in ("filler_h", "filler_p") or i.get("after_end")), len(a["items"]))
            a["items"].insert(pos, last)
        for k, v in ov.get("articles", {}).get(slugify(a["title"]), {}).items():
            a[k] = v
        aid = slugify(a["title"])
        seen[aid] += 1
        a["id"] = aid if seen[aid] == 1 else f"{aid}-{seen[aid]}"
        a["words"] = sum(len(plain(i["runs"]).split()) for i in a["items"])
        for k in ("filler_open", "kicker_from_title", "page"):
            a.pop(k, None)
        out.append(a)
    for n, a in enumerate(out, 1):
        a["n"] = n
    for old, new in ov.get("text_fixes", []):
        for a in out:
            for i in a["items"]:
                for r in i["runs"]:
                    r[1] = r[1].replace(old, new)

    meta = json.load(open(os.path.join(base, "raw", "meta.json")))
    issue = {"slug": slug, "pdf": meta["pdf"], "pages": meta["pages"], **ov.get("issue", {}), "articles": out}
    json.dump(issue, open(os.path.join(base, "issue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"skipped": skipped, "lead_in": lead_log, "hyphen_unsure": sorted(set(joiner.log))},
              open(os.path.join(base, "raw", "structure-log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if "--quiet" in sys.argv:
        return
    print(f"{slug}: {len(out)} articles, {sum(a['words'] for a in out)} words; "
          f"{len(skipped)} pieces outside articles ({sum(s['words'] for s in skipped)} words)")
    for a in out:
        kinds = collections.Counter(i["k"] for i in a["items"])
        k = " ".join(f"{k}{v}" for k, v in kinds.items())
        print(f" {a['n']:>2} p{a['pages'][0]}-{a['pages'][1]} [{a['type'][:4]}] {a['kicker'][:28]!r} | {a['title'][:38]!r} "
              f"{a['author'][:18]!r} {a['words']}w  {k}")


if __name__ == "__main__":
    main()
