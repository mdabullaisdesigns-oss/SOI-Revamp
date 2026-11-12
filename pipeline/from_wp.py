#!/usr/bin/env python3
"""
Stage 2 for the Gary-audio issues (Sep-Oct 2024 -> Sep-Oct 2026): the article
text is taken from the WordPress issue page (sources/pages/<id>.json, a copy
made by the "Fetch site pages" workflow), not from the PDF, because that text
is what the existing audio was read from.

  issues/<slug>/issue.json         same shape as the PDF route, so build.py is shared
  issues/<slug>/audio-source.json  which MP3 on the site belongs to which article
  issues/<slug>/raw/wp-log.json    what was left out and why (-> review.md)
  issues/<slug>/route.txt          "wp"

Each article is one Divi accordion item; each recording is one Divi audio module
with the same title.  The "We asked ChatGPT…" item is never included.

Usage: python3 pipeline/from_wp.py <slug> <page id> <issue number> [<pdf file name>]
"""
import html, json, os, re, sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structure import title_case, slugify, SECTION_TYPES, ACRONYMS

MONTHS = "January February March April May June July August September October November December".split()
# accordion titles that are the name of a regular section; the article's own title is the centred line under it
SECTIONS = re.compile(r"^(FROM THE .*DESK|FROM MAULANA.S DESK|PERSONAL EXPERIENCES|JOURNEY TOWARDS GOD.REALI[SZ]ATION|"
                      r"TOWARDS GLOBAL PEACE|ARTICLES WRITTEN BY CPS MEMBERS|FROM THE SPIRITUAL TREE|EXPERIENCES OF CPS MEMBERS)\s*$", re.I)
DECOR = re.compile(r"^[\s❈✦*_\-–—•.]*$")
ATTR = lambda a, k: (re.search(k + r"=[”″\"“]([^”″\"]*)", a) or [None, None])[1]


class Blocks(HTMLParser):
    """HTML of one accordion item -> list of blocks {runs, center, bq, li, links} and "hr" markers."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.cur, self.style, self.bq, self.href = [], None, [], 0, None

    def open(self, center=False, li=False):
        self.close()
        self.cur = {"runs": [], "center": center, "bq": self.bq > 0, "li": li, "links": []}

    def close(self):
        if self.cur is not None:
            runs = []
            for st, tx in self.cur["runs"]:
                tx = re.sub(r"\s+", " ", tx.replace("\xa0", " "))
                if runs and runs[-1][0] == st:
                    runs[-1][1] += tx
                elif tx:
                    runs.append([st, tx])
            text = re.sub(r"\s+", " ", "".join(r[1] for r in runs)).strip()
            if text:
                runs[0][1] = runs[0][1].lstrip()
                runs[-1][1] = runs[-1][1].rstrip()
                for r in runs:
                    r[1] = re.sub(r" {2,}", " ", r[1])
                self.cur["runs"] = [r for r in runs if r[1]]
                self.out.append(self.cur)
        self.cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            self.open(center="center" in (a.get("style") or ""))
            if tag != "p":
                self.style.append("b")
        elif tag == "li":
            self.open(li=True)
        elif tag == "blockquote":
            self.close(); self.bq += 1
        elif tag == "hr":
            self.close(); self.out.append("hr")
        elif tag == "br":
            self.handle_data(" ")
        elif tag in ("b", "strong"):
            self.style.append("b")
        elif tag in ("i", "em"):
            self.style.append("i")
        elif tag == "a" and a.get("href"):
            self.href = a["href"]

    def handle_endtag(self, tag):
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "h5", "h6"):
            if tag.startswith("h") and "b" in self.style:
                self.style.remove("b")
            self.close()
        elif tag == "blockquote":
            self.close(); self.bq = max(0, self.bq - 1)
        elif tag in ("b", "strong") and "b" in self.style:
            self.style.remove("b")
        elif tag in ("i", "em") and "i" in self.style:
            self.style.remove("i")
        elif tag == "a":
            self.href = None

    def handle_data(self, data):
        if not data.strip() and self.cur is None:
            return
        if self.cur is None:
            self.open()
        st = ("b" if "b" in self.style else "") + ("i" if "i" in self.style else "")
        self.cur["runs"].append([st, data])
        if self.href and self.href not in self.cur["links"] and data.strip():
            self.cur["links"].append(self.href)


def plain(runs):
    return "".join(r[1] for r in runs)


def all_style(b, ch):
    return all(ch in st for st, tx in b["runs"] if re.search(r"\w", tx))


def fix_opening(runs):
    """'AMERICAN writer…' / 'D elhi…' : the magazine's drop-cap opening, put back to normal case."""
    t = plain(runs)
    m = re.match(r"^([“\"‘']?[A-Z]) ([a-z])", t)                 # drop cap letter pasted with a space
    if m and m.group(1)[-1] not in "AI":
        runs[0][1] = runs[0][1].replace(m.group(1) + " ", m.group(1), 1) if runs[0][1].startswith(m.group(1) + " ") else runs[0][1]
        if len(runs) > 1 and runs[0][1].strip() == m.group(1):
            runs[0][1] = m.group(1)
        t = plain(runs)
    m = re.match(r"^([“\"‘']?)((?:[A-Z][A-Z’'-]+[,]? ?){1,4})(?=[a-z(“\"‘0-9]|$)", t)
    if m and m.group(2).strip(" ,").upper() not in ACRONYMS and len(m.group(2).strip()) > 1:
        words = m.group(2)
        fixed = " ".join(w if w.strip(",").upper() in ACRONYMS else (w[:1] + w[1:].lower()) for w in words.split(" "))
        if runs[0][1].startswith(m.group(1) + words):
            runs[0][1] = m.group(1) + fixed + runs[0][1][len(m.group(1) + words):]
            return words.strip(), fixed.strip()
    return None


def convert(title_attr, body, n, log):
    T = re.sub(r"\s+", " ", title_attr).strip()
    p = Blocks(); p.feed(body); p.close()
    blocks = [b for b in p.out if b == "hr" or not DECOR.match(plain(b["runs"]))]
    # header: centred capital lines (and an author note above a rule) before the text starts
    head, bios, k = [], [], 0
    while k < len(blocks):
        b = blocks[k]
        if b == "hr":
            k += 1; continue
        t = plain(b["runs"]).strip()
        letters = re.sub(r"[^A-Za-z]", "", t)
        capsline = letters and letters.isupper() and len(t.split()) <= 14 and not b["bq"]
        if capsline and (b["center"] or all_style(b, "b")) and len(head) < 2:
            head.append(t); k += 1; continue
        if not head and not bios and "hr" in blocks[k + 1:k + 4] and not b["bq"] and len(t.split()) > 12 \
                and re.search(r"\b(is an? |can be reached|is the |author|editor)", t):
            bios.append(b); k += 1; continue
        break
    body_blocks = [b for b in blocks[k:] if b != "hr"]
    head = [h for h in head if slugify(h) != slugify(T)]
    if SECTIONS.match(T) and head:
        kicker, title_raw = T, head[0]
    else:
        title_raw, kicker = T, (head[0] if head else "")
    extra_head = head[1:]
    a = {"title_raw": title_raw, "title": title_case(title_raw), "kicker": title_case(kicker) if kicker else "",
         "author": "", "pages": [0, 0], "items": [], "wp_title": T}
    names = T + " " + title_raw + " " + kicker
    a["type"] = next((t for rx, t in SECTION_TYPES if re.search(rx.replace("CHILDREN", "CHILDREN.S CORNER"), names, re.I)), "article")
    items = a["items"]

    def add(kind, b, **extra):
        items.append({"k": kind, "runs": b["runs"], "page": 0, "ids": [f"a{n}b{len(items) + 1}"],
                      **({"links": b["links"]} if b.get("links") else {}), **extra})

    if body_blocks and re.match(r"^By\s+[A-Z]", plain(body_blocks[0]["runs"]).strip()) and len(plain(body_blocks[0]["runs"]).split()) <= 8:
        a["author"] = re.sub(r"^By\s+", "", plain(body_blocks.pop(0)["runs"]).strip())
        a["byline"] = "By " + a["author"]
    for h in extra_head:
        add("h", {"runs": [["b", title_case(h)]]})
    for b in bios:
        add("bio", b)
    last_text = max((i for i, b in enumerate(body_blocks) if not b["bq"]), default=-1)
    seen_body = False
    for i, b in enumerate(body_blocks):
        t = plain(b["runs"]).strip()
        nwords = len(t.split())
        if b["bq"]:
            add("thought" if i > last_text and not any(x["k"] == "thought" for x in items) else "pull", b)
        elif re.search(r"remedy for ignorance", t, re.I) and a["type"] == "qa":
            add("qa_intro", b)
        elif items and items[-1]["k"] == "qa_intro" and re.match(r"The spirit of enquiry", t) \
                and "spirit of enquiry" not in plain(items[-1]["runs"]).lower():
            items[-1]["runs"][-1][1] += " "
            items[-1]["runs"] += b["runs"]
        elif a["type"] == "scripture" and not seen_body and not all_style(b, "b") and not all_style(b, "i") \
                and not any(x["k"] in ("ayah", "h") for x in items):
            add("intro", b)                              # "The Quran is the book of God…" / "Translated…"
        elif all_style(b, "b") and (a["type"] == "scripture" and nwords > 8):
            add("bismillah" if re.match(r"In the name of God", t) and nwords < 14 else "ayah", b); seen_body = True
        elif all_style(b, "b") and nwords <= 30 and a["type"] == "qa" and t.endswith("?"):
            add("qh", b); seen_body = True
        elif all_style(b, "b") and nwords <= 14 and not re.search(r"[.,;]$", t):
            add("h", b)
        elif b["center"] and nwords <= 14 and re.sub(r"[^A-Za-z]", "", t).isupper():
            add("h", {**b, "runs": [["b", title_case(t)]]})
        elif all_style(b, "i") and t.startswith("(") and nwords < 40:
            add("small", b)
        elif all_style(b, "i") and (b["center"] or a["type"] == "scripture"):
            add("ayah" if a["type"] == "scripture" else "quote", b); seen_body = True
        else:
            if b["li"]:
                b["runs"].insert(0, ["", "• "])
            if not seen_body and a["type"] in ("article", "qa"):
                fx = fix_opening(b["runs"])
                if fx:
                    log["case"].append(f"{fx[0]!r} -> {fx[1]!r}")
            add("p", b); seen_body = True
    a["id"] = slugify(a["title"])
    a["words"] = sum(len(plain(i["runs"]).split()) for i in items)
    return a


def main():
    slug, pid, number = sys.argv[1], sys.argv[2], int(sys.argv[3])
    pdf = sys.argv[4] if len(sys.argv) > 4 else ""
    page = json.load(open(f"sources/pages/{pid}.json", encoding="utf-8"))
    c = html.unescape(page["content"]["rendered"])
    c = c.replace("&nbsp;", " ")
    log = {"page_id": int(pid), "page_title": html.unescape(page["title"]["rendered"]), "skipped": [], "case": [], "audio_unmatched": []}
    arts, used = [], {}
    for m in re.finditer(r"\[et_pb_accordion_item([^\]]*)\](.*?)\[/et_pb_accordion_item\]", c, re.S):
        title = ATTR(m.group(1), "title") or ""
        words = len(re.sub(r"<[^>]+>", " ", m.group(2)).split())
        if re.search(r"CHATGPT", title, re.I):
            log["skipped"].append({"title": title, "why": "promotional ChatGPT page (never included)", "words": words})
            continue
        a = convert(title, m.group(2), len(arts) + 1, log)
        if not a["items"]:
            log["skipped"].append({"title": title, "why": "accordion item with no text", "words": 0})
            continue
        base = a["id"] or f"article-{len(arts) + 1}"
        used[base] = used.get(base, 0) + 1
        a["id"] = base if used[base] == 1 else f"{base}-{used[base]}"
        a["n"] = len(arts) + 1
        arts.append(a)
    # audio modules: matched to the articles by their title
    audio, by_title = {}, {}
    for a in arts:
        by_title.setdefault(slugify(a["wp_title"]), []).append(a)
    for m in re.finditer(r"\[et_pb_audio([^\]]*)\]", c):
        t, url = ATTR(m.group(1), "title") or "", ATTR(m.group(1), "audio") or ""
        cands = by_title.get(slugify(t), [])
        a = next((x for x in cands if x["id"] not in audio), None)
        if re.search(r"CHATGPT|CHAT-GPT", t + url, re.I):
            log["skipped"].append({"title": t, "why": "audio of the promotional ChatGPT page (never included)", "words": 0, "url": url})
        elif a and url:
            audio[a["id"]] = {"url": url, "wp_title": t}
        else:
            log["audio_unmatched"].append({"title": t, "url": url})
    # a recording whose title is only close to the article's ("NEW YEAR'S MESSAGE" / "…FOR 2026")
    for u in list(log["audio_unmatched"]):
        want = set(slugify(u["title"]).split("-")) - {"the", "of", "a", "and", "for", "to", "in"}
        best = max((x for x in arts if x["id"] not in audio), default=None,
                   key=lambda x: len(want & set(slugify(x["wp_title"] + " " + x["title"]).split("-"))))
        if best and want and len(want & set(slugify(best["wp_title"] + " " + best["title"]).split("-"))) >= max(2, 0.6 * len(want)) and u["url"]:
            audio[best["id"]] = {"url": u["url"], "wp_title": u["title"], "matched": "by similar title"}
            log["audio_unmatched"].remove(u)
    mnames = [w for w in re.findall(r"[A-Za-z]+", log["page_title"]) if any(mn.lower().startswith(w.lower()[:3]) for mn in MONTHS) and w.upper() != "ISSUE"]
    full = [next(mn for mn in MONTHS if mn.lower().startswith(w.lower()[:3])) for w in mnames]
    year = re.search(r"20\d\d", log["page_title"]).group(0)
    issue = {"slug": slug, "pdf": pdf, "pages": 0, "source": f"WordPress page {pid} ({log['page_title']})", "page_id": int(pid),
             "number": number, "period": "–".join(full) + " " + year,
             "period_short": "–".join(n[:3] for n in full) + " " + year, "articles": arts}
    issue["label"] = f"Issue {number} · {issue['period']}"
    base = f"issues/{slug}"
    os.makedirs(base + "/raw", exist_ok=True)
    json.dump(issue, open(base + "/issue.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(audio, open(base + "/audio-source.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(log, open(base + "/raw/wp-log.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(base + "/route.txt", "w").write(f"wp {pid} {number} {pdf}\n")
    print(f"{slug}: {len(arts)} articles, {sum(a['words'] for a in arts)} words, {len(audio)} with a recording on the site, "
          f"{len(arts) - len(audio)} without, {len(log['audio_unmatched'])} recordings unmatched")
    for a in arts:
        kinds = {}
        for i in a["items"]:
            kinds[i["k"]] = kinds.get(i["k"], 0) + 1
        print(f" {a['n']:>2} [{a['type'][:4]}] {a['kicker']!r} | {a['title']!r} {a['words']}w {'AUDIO' if a['id'] in audio else '-----'}  "
              + " ".join(f"{k}{v}" for k, v in kinds.items()))


if __name__ == "__main__":
    main()
