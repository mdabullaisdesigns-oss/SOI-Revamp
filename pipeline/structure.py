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
NON_ARTICLE = re.compile(r"^(CONTENTS|ABOUT THE MAGAZINE|NOTICE|SUBSCRIBE|SUBSCRIBE SPIRIT OF ISLAM|SPIRIT ?OF ISLAM)$", re.I)
SECTION_TYPES = [(r"^\s*GLOSSARY\s*$", "glossary"), (r"WORD OF GOD", "scripture"), (r"ASK MAULANA|QUESTIONS ANSWERED", "qa"),
                 (r"NEWSLETTER", "newsletter"), (r"CHILDREN", "children")]
ADVERT = re.compile(r"subscription|cpsglobal\.org|www\.|@|A/c No|Subscribers are requested|ORDERED ONLINE|goodword|ACCESS ONLINE|Buy Online|New Release", re.I)
SECTION_NAMES = re.compile(r"(?i)^(from the .*desk|from maulana.s desk|towards global peace|personal experiences|journey towards god.reali[sz]ation)$")
END_GLYPHS = {"\uf071", "v", "q", "o", "\uf06f", "n", "\uf06e", "\uf0a8"}   # the end-of-article box in Wingdings
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
        if (sz >= 13.4 and t.upper() == t) or (sz >= 15 and y < 110 and len(t.split()) >= 2
                                                and sum(ch.isupper() for ch in t) >= 0.6 * max(1, sum(ch.isalpha() for ch in t))):
            return "title"
        if (sz >= 15 and t.lower() == "subscribe") or (sz >= 11 and t == "Glossary" and y < 110):
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
    return re.sub(r"\b(Part|Vol|Volume) ([IVXivx]{1,4})\b", lambda m: m.group(1) + " " + m.group(2).upper(), " ".join(out))


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
        lines = [l for l in b["lines"] if l["t"].strip()]
        # list bullets are drawn with a symbol font (plus a stray copy of the same letter): not text
        bullets = [l for l in lines if fam(l["f"]).startswith("Wingdings") and l["t"].strip() not in END_GLYPHS]
        if bullets:
            lines = [l for l in lines if l not in bullets and not (
                len(l["t"].strip()) == 1 and any(abs(l["bb"][1] - q["bb"][1]) < 5 and abs(l["bb"][0] - q["bb"][0]) < 12 for q in bullets))]
            for l in lines:
                if any(abs(l["bb"][1] - q["bb"][1]) < 5 and l["bb"][0] > q["bb"][0] for q in bullets) and not l["t"].startswith("\u2022"):
                    l["t"] = "\u2022 " + l["t"]
                    if l.get("runs"):
                        l["runs"] = [["", "\u2022 "]] + l["runs"]
        roles = [forced.get(b["id"]) or line_role(l, page["h"]) for l in lines]
        demoted = {}                                 # line -> length of the bold lead-in that ends in body text
        for li in range(len(lines) - 2, -1, -1):     # bold words that run on into the paragraph are not a heading
            l, nx = lines[li], lines[li + 1]
            if roles[li] not in ("subhead", "signoff") or b["id"] in forced \
                    or not 0 <= nx["bb"][1] - l["bb"][1] <= 1.38 * pitch:
                continue
            mine = next((st for st, tx in (l.get("runs") or []) if tx.strip()), "")
            nrs = [(st, tx) for st, tx in (nx.get("runs") or []) if tx.strip()]
            plain_words = " ".join(tx for st, tx in nrs if "b" not in st)
            if li + 1 in demoted and demoted[li + 1] < 3:
                demoted[li] = demoted[li + 1] + 1    # at most three lines: a longer bold passage is a verse
            elif roles[li + 1] == "body" and nrs and nrs[0][0] == mine and re.search(r"[A-Za-z]{2}", plain_words):
                demoted[li] = 1                      # (bold then only a reference number = end of a verse)
            elif roles[li + 1] == "body" and roles[li] == "subhead" and l["t"].rstrip().endswith(":"):
                demoted[li] = 3
        for li in sorted(demoted):                   # ...but not when the bold passage began even earlier
            if li and li - 1 not in demoted and roles[li - 1] == roles[li] and lines[li]["bb"][1] - lines[li - 1]["bb"][1] <= 1.38 * pitch:
                k = li
                while k in demoted:
                    del demoted[k]
                    k += 1
        for li in demoted:
            roles[li] = "body"
        for l, role in zip(lines, roles):
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


def glossary_items(pages, a, joiner):
    """The glossary is two columns of entries with a hanging indent: read down the left column, then the
    right, one item per entry (term in bold)."""
    items = []
    for page in pages:
        if not a["pages"][0] <= page["n"] <= a["pages"][1]:
            continue
        lines = [dict(l, id=b["id"]) for b in page["blocks"] for l in b["lines"]
                 if l["t"].strip() and 7.4 <= l["sz"] <= 9.6 and l["bb"][1] < page["h"] - 45
                 and not re.search(r"Spirit of Islam\s+Issue", l["t"])]
        if len(lines) < 8:
            return None
        mid = page["w"] / 2
        for col in (0, 1):
            cl = sorted((l for l in lines if (l["bb"][0] >= mid - 8) == bool(col)), key=lambda l: (round(l["bb"][1]), l["bb"][0]))
            if not cl:
                continue
            left = min(l["bb"][0] for l in cl)
            entry = []
            for l in cl + [None]:
                starts = l is not None and l["bb"][0] - left < 3.5 and \
                    ("b" in (l.get("runs") or [["b" if "Bold" in l["f"] else "", ""]])[0][0])
                if l is None or (starts and entry):
                    runs = joiner.join(entry)
                    items.append({"k": "gloss", "runs": runs, "page": page["n"], "ids": list(dict.fromkeys(x["id"] for x in entry))})
                    entry = []
                if l is not None:
                    entry.append(l)
    return items


def feature_article(pages, ft):
    """An article made from every text block of pages ft["pages"] = [first, last], in reading order
    (headings across the page, then left column, then right column).  Nothing on those pages is left out
    except the running footer."""
    items, title = [], ft.get("title")
    fixes = ft.get("replace", {})
    left_out = ft.setdefault("_left_out", [])
    one_col = ft.get("columns") == 1
    for page in pages:
        if not ft["pages"][0] <= page["n"] <= ft["pages"][1]:
            continue
        mid = page["w"] / 2
        lines = []
        for b in page["blocks"]:
            for l in b["lines"]:
                t = l["t"].strip()
                if not t or re.match(r"^\d+\s+Spirit of Islam\s+Issue", t, re.I) or re.match(r"^Spirit of Islam\s+Issue.*\d+$", t, re.I) \
                        or (re.fullmatch(r"\d{1,3}", t) and l["bb"][1] > page["h"] - 60):
                    continue
                if ft.get("skip") and re.search(ft["skip"], t, re.I):
                    left_out.append({"page": page["n"], "text": t})
                    continue
                lines.append({"id": b["id"], "t": t, "sz": l["sz"], "f": l["f"], "x": l["bb"][0], "y": l["bb"][1], "x1": l["bb"][2], "y1": l["bb"][3]})
        heads = []
        for y in sorted(l["y"] for l in lines if 15 <= l["sz"] < 30):
            if not heads or y > heads[-1] + 30:      # a heading of two lines is one heading
                heads.append(y)
        bold_blocks = collections.defaultdict(list)
        for l in lines:
            bold_blocks[l["id"]].append("Bold" in l["f"])
        blockcol = {}
        caps = [l for l in lines if l["sz"] >= 30]                     # drop capitals
        lines = [l for l in lines if l["sz"] < 30]
        for l in lines:
            l["band"] = sum(1 for y in heads if y <= l["y"] + 1)
            wide = 15 <= l["sz"] < 30 or (l["x"] < mid - 40 and l["x1"] > mid + 40)
            l["col"] = -1 if 15 <= l["sz"] < 30 else (0 if wide or l["x"] < mid - 8 else 1)
            if l["sz"] < 11.5:                       # a block that wraps round a picture stays in the column it starts in
                l["col"] = blockcol.setdefault(l["id"], l["col"])
            if one_col:
                l["col"] = 0
        if one_col:                                  # single column: top to bottom; a block is read whole from where it starts
            top = {}
            for l in lines:
                top[l["id"]] = min(top.get(l["id"], 1e9), l["y"])
            lines.sort(key=lambda l: (l["band"], round(top[l["id"]] / 8), l["id"] if l["sz"] >= 8.6 else "~", round(l["y"]), l["x"]))
        else:
            lines.sort(key=lambda l: (l["band"], l["col"], round(l["y"]), l["x"]))
        groups = []
        for l in lines:
            g = groups[-1] if groups else None
            cls = "h" if l["sz"] >= 15 else "h2" if l["sz"] >= 11.5 else "cap" if l["sz"] < 8.6 or "Cond" in l["f"] else "src" if "Obl" in l["f"] else "q" if "Italic" in l["f"] else "b" if all(bold_blocks[l["id"]]) else "p"
            if g and g["cls"] == cls and g["col"] == l["col"] and g["band"] == l["band"] and \
                    (g["id"] == l["id"] or cls == "h") and 0 <= l["y"] - g["y"] < (3.6 if g["id"] == l["id"] else 2.2) * l["sz"]:
                g["t"] += ("" if g["t"].endswith("\u00ad") else " ") + l["t"]
                g["y"] = l["y"]; g["ids"].append(l["id"])
                g["bb"] = [min(g["bb"][0], l["x"]), min(g["bb"][1], l["y"]), max(g["bb"][2], l["x1"]), max(g["bb"][3], l["y1"])]
            else:
                groups.append({"cls": cls, "col": l["col"], "band": l["band"], "id": l["id"], "ids": [l["id"]], "t": l["t"], "y": l["y"], "y0": l["y"], "x": l["x"],
                               "bb": [l["x"], l["y"], l["x1"], l["y1"]], "links": []})
        for lk in page.get("links", []) if ft.get("links") else []:      # each link goes to the text it sits on, else the nearest
            cx, cy = (lk["bb"][0] + lk["bb"][2]) / 2, (lk["bb"][1] + lk["bb"][3]) / 2
            def dist(g):
                dx = max(g["bb"][0] - cx, 0, cx - g["bb"][2]); dy = max(g["bb"][1] - cy, 0, cy - g["bb"][3])
                return dx * 0.3 + dy
            if groups:
                tgt = min(groups, key=dist)
                if lk["uri"] not in tgt["links"]:
                    tgt["links"].append(lk["uri"])
        if one_col:                                  # a heading or sentence set as two text boxes is still one
            merged = []
            for g in groups:
                m = merged[-1] if merged else None
                close = m and (m["band"] == g["band"] or g["cls"] == "h") and 0 < g["y0"] - m["y"] < (34 if g["cls"] == "h" else 1.7 * 12) \
                    and not re.search(r"[.?!:;”\"]$", m["t"])
                if close and m["cls"] == g["cls"] and (g["cls"] in ("h", "h2", "b") or (g["cls"] == "p" and re.match(r"[a-z]", g["t"]) and len(m["t"].split()) < 30)):
                    m["t"] += " " + g["t"]; m["y"] = g["y"]; m["ids"] += g["ids"]; m["links"] += g["links"]
                    m["bb"] = [min(m["bb"][0], g["bb"][0]), min(m["bb"][1], g["bb"][1]), max(m["bb"][2], g["bb"][2]), max(m["bb"][3], g["bb"][3])]
                else:
                    merged.append(g)
            groups = merged
        for c in caps:                                # put each drop capital back on the paragraph beside it
            near = [g for g in groups if g["cls"] == "p" and -6 <= g["y0"] - c["y"] <= 16 and g["x"] >= c["x"] - 4]
            if near:
                tgt = min(near, key=lambda g: abs(g["x"] - c["x"]))
                tgt["t"] = c["t"] + (tgt["t"][0].lower() + tgt["t"][1:] if re.match(r"[A-Z] ", tgt["t"]) else tgt["t"])
                tgt["ids"].insert(0, c["id"])
        for k, g in enumerate(groups):                # ...or was read as the last letter of the heading above it
            if g["cls"] == "p" and re.match(r"[a-z]", g["t"]):
                hd = next((h for h in reversed(groups[:k]) if h["cls"] in ("h", "h2")), None)
                if hd and re.search(r" [A-Z]$", hd["t"]):
                    g["t"] = hd["t"][-1] + g["t"]; hd["t"] = hd["t"][:-2]
        for g in groups:
            t = re.sub(r"\s+", " ", g["t"].replace("\u00ad ", "").replace("\u00ad", "")).strip()
            for a, b in fixes.items():
                t = t.replace(a, b)
            if not t:
                continue
            ids = list(dict.fromkeys(g["ids"]))
            if g["cls"] == "h" and title is None:
                title = t
                continue
            if g["cls"] == "h" and re.sub(r"\W", "", t).lower() == re.sub(r"\W", "", title).lower():
                continue                             # the section name again at the top of the page
            label = bool(re.fullmatch(r"(?i)(click here|scan or click the button|click|here|kindle|website|kindle website)[.:]?", t))
            if ft.get("links") and label and items:  # a button label: its link goes on the line it belongs to
                items[-1].setdefault("links", [])
                items[-1]["links"] += [u for u in g["links"] if u not in items[-1]["links"]]
                items[-1]["ids"] += ids
                left_out.append({"page": page["n"], "text": t})
                continue
            if ft.get("short_heads") and re.match(r"[~–—-]\s*\w", t) and len(t.split()) <= 10:
                g["cls"] = "src"                     # a signature line
            if ft.get("short_heads") and g["cls"] in ("p", "b") and not g["links"] and len(t.split()) <= 16 \
                    and (not re.search(r"[.,;:]$", t)) and not t.startswith("•"):
                g["cls"] = "h2"
            if ft.get("short_heads") and re.match(r"(https?://|www\.)\S+", t):
                g["cls"] = "p"                       # a web address on its own line
            if ft.get("short_heads") and re.match(r"(?i)report by ", t) and len(t.split()) <= 10:
                g["cls"] = "src"
            if ft.get("short_heads") and g["cls"] in ("h", "h2") and len(t.split()) > 16:
                g["cls"] = "hq"                      # many lines of display type: a boxed quotation
            if g["cls"] == "h2" and len(t.split()) > (16 if ft.get("short_heads") else 9):
                g["cls"] = "p"
            if g["cls"] == "b":
                g["cls"] = "h" if len(t.split()) <= 6 else "pb"
            kind = {"h": "h", "h2": "h", "hq": "pull", "cap": "small", "src": "small", "p": "p", "pb": "p", "q": "quote"}[g["cls"]]
            if g["cls"] == "h" and len(t.split()) > 14:
                kind = "pull"                        # a long line in display type is a boxed quotation, not a heading
            prev = items[-1] if items else None
            if kind == "small" and prev and prev.get("labels") and prev["page"] == page["n"] and g["cls"] == "cap" and len(t.split()) <= 3:
                prev["runs"][0][1] += " · " + t; prev["ids"] += ids
                continue
            back = next((x for x in reversed(items) if x["k"] in ("p", "h")), None)
            if kind == "p" and g["cls"] == "p" and back and back["k"] == "p" and back["page"] == page["n"] and not back.get("bold") \
                    and not re.search(r"[.?!:;”\"’)]$", plain(back["runs"])) and not t.startswith("•"):
                back["runs"][0][1] += ("" if back["runs"][0][1].endswith("-") and t[:1].islower() and False else " ") + t
                back["ids"] += ids                   # the paragraph carries on in the next column or round a picture
                continue
            items.append({"k": kind, "runs": [["b" if g["cls"] == "pb" else "", t]], "page": page["n"], "ids": ids})
            if g["links"]:
                items[-1]["links"] = list(g["links"])
            if g["cls"] == "pb":
                items[-1]["bold"] = True
            if g["cls"] == "cap" and len(t.split()) <= 3:
                items[-1]["labels"] = True           # one-word picture labels are gathered into one line
    a = {"title_raw": title, "title": title, "kicker": ft.get("kicker", ""), "author": "", "pages": list(ft["pages"]),
         "items": items, "type": ft.get("type", "article"), "id": slugify(title), "feature": True}
    if not ft.get("audio", False):
        a["audio"] = False
    a["words"] = sum(len(plain(i["runs"]).split()) for i in items)
    return a


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
                under_section = cur and not cur.get("skip") and cur.get("items") is not None and only_bio(cur) \
                    and cur.get("page") == page["n"] and u is not titles[0]
                if NON_ARTICLE.match(text) and not under_section:   # ("Spirit of Islam" can also be an editorial's own title)
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
        if a["pages"][0] >= len(pages) - 1 and sum(len(plain(i["runs"]).split()) for i in a["items"]) < 60:
            for x in [{"runs": [["", a["title_raw"]]], "page": a["pages"][0], "ids": []}] + a["items"]:
                t = plain(x["runs"])
                skipped.append({"page": x["page"], "ids": x["ids"], "role": "other", "why": "back cover", "words": len(t.split()), "text": t})
            continue
        sec = a.get("section", a["title_raw"])
        a["type"] = art_type(a)
        # advert / notice boxes printed in the space after an article (BOOKS · VIDEOS · cpsglobal.org/…,
        # subscription and bank details, "now access online"): not part of the article -> the left-out list
        keep, k = [], 0
        its = a["items"]
        while k < len(its):
            if its[k]["k"] in ("filler_p", "filler_sig", "other") and (k == 0 or its[k - 1]["k"] not in ("filler_h",)) \
                    and any(x["k"] in ("thought", "filler_h", "filler_p", "filler_sig", "signoff", "contact", "other") or x is its[k] for x in its[max(0, k - 1):k + 1]):
                j = k
                while j < len(its) and its[j]["k"] in ("filler_p", "filler_sig", "other") and its[j]["page"] == its[k]["page"]:
                    j += 1
                text = " ".join(plain(x["runs"]) for x in its[k:j])
                in_tail = all(x["k"] in ("filler_p", "filler_sig", "other", "filler_h", "thought", "signoff", "contact", "small", "footnote") for x in its[k:])
                if in_tail and ADVERT.search(text) and any(x["k"] == "other" for x in its[k:j]):
                    for x in its[k:j]:
                        t = plain(x["runs"])
                        skipped.append({"page": x["page"], "ids": x["ids"], "role": "other", "why": "advert or notice box after the article",
                                        "words": len(t.split()), "text": t})
                    k = j
                    continue
            keep.append(its[k])
            k += 1
        a["items"] = keep
        # blocks set in a face outside the magazine's usual type system: place the clear cases
        its, keep = a["items"], []
        for k, x in enumerate(its):
            if x["k"] != "other":
                keep.append(x); continue
            t = plain(x["runs"]).strip()
            font, size, nw = x.get("font", ""), x.get("size") or 0, len(t.split())
            prev = keep[-1] if keep else None
            heavy = bool(re.search(r"Bold|Black|Impact|Semibold", font)) or (re.sub(r"[^A-Za-z]", "", t).isupper() and nw >= 2)
            if re.fullmatch(r"[-\u2013\u2014_'\u2019.o\s]*|[A-Z]( [A-Z])?", t) or size < 6:
                skipped.append({"page": x["page"], "ids": x["ids"], "role": "other", "words": nw, "text": t,
                                "why": "decoration or small print inside a picture"})
            elif prev is not None and prev["k"] in ("pull", "quote") and prev.get("font") == font and prev["page"] == x["page"] and "Italic" in font:
                prev["runs"][-1][1] = prev["runs"][-1][1].rstrip() + " "
                prev["runs"] += x["runs"]                  # the next line of the same large italic quote
            elif size <= 9.2 and nw <= 6 and (re.search(r"\d\s*:\s*\d", t) or t.isupper()):
                x["k"] = "small"; keep.append(x)             # a source line under a quotation
            elif heavy and 9.5 <= size <= 12.5 and nw > 12 and "Bold" in font and prev is not None and prev["k"] in ("p", "h"):
                x["k"] = "p"; x["runs"] = [["b" if "b" not in r[0] else r[0], r[1]] for r in x["runs"]]; keep.append(x)
            elif "Italic" in font and size >= 10.8 and nw >= 3 and not ADVERT.search(t):
                x["k"] = "pull"; keep.append(x)
            elif heavy and 9.5 <= size <= 14.5 and nw <= 12 and not ADVERT.search(t) and not re.search(r"https?:", t) \
                    and (prev is None or prev["k"] in ("p", "h", "bio", "lead", "small", "quote", "pull", "intro")):
                x["k"] = "h"; keep.append(x)
            else:
                keep.append(x)
        a["items"] = keep
        body = [i for i in a["items"] if i["k"] in ("p", "quote")]
        if body and sum(i["k"] == "quote" for i in body) > 0.6 * len(body):
            for i in body:
                i["k"] = "p"                         # an article set wholly in italics is still body text
        for n, i in enumerate(a["items"]):           # the recurring Q&A opening -> "Before we begin" box
            if i["k"] in ("p", "bio", "quote", "qh") and re.search(r"remedy for ignorance", plain(i["runs"]), re.I):
                i["k"] = "qa_intro"
                nxt = a["items"][n + 1] if n + 1 < len(a["items"]) else None
                if nxt and "spirit of enquiry" not in plain(i["runs"]).lower() \
                        and re.match(r"\s*The spirit of enquiry", plain(nxt["runs"])):
                    i["runs"][-1][1] = i["runs"][-1][1].rstrip() + " "   # saying and its explanation are one passage
                    i["runs"] += nxt["runs"]
                    i["ids"] += nxt["ids"]
                    a["items"].pop(n + 1)
                break
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
        if a["type"] == "glossary":
            g = glossary_items(pages, a, joiner)
            if g:
                used = {x for i in g for x in i["ids"]}
                rest_items = [i for i in a["items"] if not set(i["ids"]) & used]   # a filler box on the same page stays
                a["items"], a["audio"] = g + rest_items, False
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
        if a.get("kicker") and SECTION_NAMES.match(a["title"].strip()) and not SECTION_NAMES.match(a["kicker"].strip()):
            a["title"], a["kicker"] = a["kicker"], a["title"]
            a["section"] = a.get("section") or a["title_raw"]
        aid = slugify(a["title"])
        seen[aid] += 1
        a["id"] = aid if seen[aid] == 1 else f"{aid}-{seen[aid]}"
        a["words"] = sum(len(plain(i["runs"]).split()) for i in a["items"])
        for k in ("filler_open", "kicker_from_title", "page"):
            a.pop(k, None)
        out.append(a)
    # a feature set in its own brochure typography (overrides.json "features"): built straight from the page blocks
    for ft in ov.get("features", []):
        fa = feature_article(pages, ft)
        skipped[:] = [x for x in skipped if not ft["pages"][0] <= x["page"] <= ft["pages"][1]]
        pos = next((k for k, a in enumerate(out) if a["pages"][0] > ft["pages"][0]), len(out))
        out.insert(pos, fa)
    for n, a in enumerate(out, 1):
        a["n"] = n
    def undouble(text):
        """'A B A B C D C D' -> 'A B C D': a boxed quote whose every line is in the PDF twice (shadow copy)."""
        w, out_w, k0 = text.split(), [], 0
        while k0 < len(w):
            for k in range(min(12, (len(w) - k0) // 2), 1, -1):
                if w[k0:k0 + k] == w[k0 + k:k0 + 2 * k]:
                    out_w += w[k0:k0 + k]; k0 += 2 * k
                    break
            else:
                return None
        return " ".join(out_w)
    for a in out:
        for i in a["items"]:
            if i["k"] in ("pull", "thought") and len(plain(i["runs"]).split()) >= 6:
                u = undouble(plain(i["runs"]))
                if u:
                    i["runs"] = [[i["runs"][0][0], u]]
    for a in out:                                    # overrides.json "join_items": [[first block id, next block id, kind?]]
        for j in ov.get("join_items", []):
            k = next((n for n, i in enumerate(a["items"]) if i["ids"][:1] == [j[0]]), None)
            if k is not None and k + 1 < len(a["items"]) and j[1] in a["items"][k + 1]["ids"]:
                nx = a["items"].pop(k + 1)
                a["items"][k]["runs"][-1][1] = a["items"][k]["runs"][-1][1].rstrip() + " "
                a["items"][k]["runs"] += nx["runs"]; a["items"][k]["ids"] += nx["ids"]
                if len(j) > 2:
                    a["items"][k]["k"] = j[2]
    for rp in ov.get("replace_items", []):           # {"article": id, "remove": [block ids], "items": [{k, text|runs, page, links?}]}
        a = next(x for x in out if x.get("id") == rp["article"])
        idx = [n for n, i in enumerate(a["items"]) if i["ids"] and i["ids"][0] in rp["remove"]]
        if idx:
            new_items = [{"k": x["k"], "runs": x.get("runs") or [["", x["text"]]], "page": x["page"], "ids": list(rp["remove"]) if n == 0 else [],
                          **({"links": x["links"]} if x.get("links") else {})} for n, x in enumerate(rp["items"])]
            a["items"] = [i for n, i in enumerate(a["items"]) if n not in idx]
            a["items"][idx[0]:idx[0]] = new_items
    for a in out:                                    # hand corrections: overrides.json "item_kinds" {block id: kind}
        for i in a["items"]:
            k = next((ov.get("item_kinds", {})[x] for x in i["ids"] if x in ov.get("item_kinds", {})), None)
            if k:
                i["k"] = k
    for add in ov.get("add_items", []):              # text the rules missed: {"article": id, "after": block id, "k":, "text":, "page":}
        a = next(x for x in out if slugify(x["title"]) == add["article"] or x.get("id") == add["article"])
        pos = next((n + 1 for n, i in enumerate(a["items"]) if add.get("after") in i["ids"]), len(a["items"]))
        a["items"].insert(pos, {"k": add["k"], "runs": [["", add["text"]]], "page": add["page"], "ids": add.get("ids", [])})
    for old, new in ov.get("text_fixes", []):
        for a in out:
            for i in a["items"]:
                for r in i["runs"]:
                    r[1] = r[1].replace(old, new)

    # a few PDFs space out their fi/ff/fl ligatures ("sacrifi ce", "diff erent"): rejoin, but only where the
    # second reading of the PDF has the joined word and never has the two pieces side by side
    second = os.path.join(base, "raw", "pdftotext.txt")
    if os.path.exists(second):
        low = re.sub(r"\s+", " ", open(second, encoding="utf-8").read().lower())
        vocab2 = set(re.findall(r"[a-z]+", low))
        fixed = collections.Counter()
        text_all = " ".join(plain(i["runs"]) for a in out for i in a["items"])
        spaced = len(re.findall(r"\b[A-Za-z]*(?:ffi|ff|fi|fl) (?:er|ce|cult|ort|ect|rst|rm|nd|ne|ll|ve|eld|ower|ering)[a-z]*\b", text_all))
        if spaced >= 15:                                 # this PDF spaces its ligatures throughout: use the archive's vocabulary
            import glob
            wc = collections.Counter()
            for fpath in glob.glob(os.path.join("issues", "*", "raw", "pdftotext.txt")):
                if os.path.dirname(os.path.dirname(fpath)) != base:
                    wc.update(set(re.findall(r"[a-z]+", open(fpath, encoding="utf-8").read().lower())))
            vocab2 |= {w for w, n in wc.items() if n >= 3}

        def lig(m):
            joined, pair = (m.group(1) + m.group(2)).lower(), (m.group(1) + " " + m.group(2)).lower()
            if (joined in vocab2 and (pair not in low or spaced >= 15)) or (spaced >= 15 and m.group(1).lower() not in vocab2):
                fixed[m.group(1) + m.group(2)] += 1
                return m.group(1) + m.group(2)
            return m.group(0)
        for a in out:
            for key in ("title", "kicker"):
                a[key] = re.sub(r"\b([A-Za-z]*(?:ffi|ffl|ff|fi|fl|Fi|Fl)) ([a-z]+)\b", lig, a.get(key, ""))
            for i in a["items"]:
                for r in i["runs"]:
                    r[1] = re.sub(r"\b([A-Za-z]*(?:ffi|ffl|ff|fi|fl|Fi|Fl)) ([a-z]+)\b", lig, r[1])
            a["words"] = sum(len(plain(i["runs"]).split()) for i in a["items"])
    else:
        fixed = {}

    meta = json.load(open(os.path.join(base, "raw", "meta.json")))
    # issue number and period, read from the running footer ("Spirit of Islam Issue 66 June 2018")
    ident = {}
    months = "January February March April May June July August September October November December".split()
    for p in pages[2:12]:
        for b in p["blocks"]:
            for l in b["lines"]:
                m = re.search(r"Spirit of Islam\s+(?:Vol\s+\d+\s+)?Issue\s+(\d+)\s+([A-Za-z]+(?:\s*[-\u2013]\s*[A-Za-z]+){0,2})\s+(\d{4})", l["t"])
                if m and not ident:
                    names = [next((x for x in months if x.lower().startswith(w.lower()[:3])), w) for w in re.split(r"\s*[-\u2013]\s*", m.group(2))]
                    ident = {"number": int(m.group(1)), "period": "\u2013".join(names) + " " + m.group(3),
                             "period_short": ("\u2013".join(n[:3] for n in names) if len(names) > 1 else names[0]) + " " + m.group(3)}
                    ident["label"] = f"Issue {ident['number']} \u00b7 {ident['period']}"
    issue = {"slug": slug, "pdf": meta["pdf"], "pages": meta["pages"], **ident, **ov.get("issue", {}), "articles": out}
    json.dump(issue, open(os.path.join(base, "issue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"skipped": skipped, "lead_in": lead_log, "hyphen_unsure": sorted(set(joiner.log)), "ligatures_rejoined": sum(fixed.values())},
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
