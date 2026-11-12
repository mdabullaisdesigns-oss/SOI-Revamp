#!/usr/bin/env python3
"""
Stage 3 - check.  Compares issues/<slug>/issue.json word by word with a second,
independent reading of the PDF (raw/pdftotext.txt) and writes

  issues/<slug>/check.json   numbers for every article
  issues/<slug>/review.md    what a person should look at before the issue is built

Two questions are answered:
  1. Is every word of every article really in the PDF, in the same order?
     (below 99% -> flagged)
  2. Is every word of the PDF either in an article or on the "left out" list?
     (anything else is listed as UNPLACED - nothing may vanish silently)

Usage: python3 pipeline/check.py <slug>      exit code 1 if anything is flagged
"""
import json, os, re, sys, difflib, collections

THRESHOLD = 99.0


def norm(text):
    text = text.replace("­", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)          # line-end hyphen
    out = []
    for w in text.lower().split():
        w = re.sub(r"[^a-z0-9]", "", w)
        if w:
            out.append(w)
    return out


LIG = re.compile(r"ffi|ffl|ff|fi|fl")


def match(a, b):
    """How many words of a are found, in order, in b.  Returns (hits, matched flags for a, for b)."""
    fa, fb = [False] * len(a), [False] * len(b)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = sm.get_opcodes()
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal" and (i2 - i1 >= min(3, len(a)) or i1 == 0 or i2 == len(a)):
            for k in range(i2 - i1):
                fa[i1 + k] = fb[j1 + k] = True
        elif tag == "replace" and LIG.sub("", "".join(a[i1:i2])) == LIG.sub("", "".join(b[j1:j2])):   # also: a reading that lost its ff/fi ligatures
            for k in range(i1, i2):                              # "w" + "ith"  ==  "with"
                fa[k] = True
            for k in range(j1, j2):
                fb[k] = True
    return sum(fa), fa, fb


def plain(i):
    return "".join(r[1] for r in i["runs"])


def main():
    slug = sys.argv[1]
    base = os.path.join("issues", slug)
    issue = json.load(open(os.path.join(base, "issue.json"), encoding="utf-8"))
    log = json.load(open(os.path.join(base, "raw", "structure-log.json"), encoding="utf-8"))
    pdf_pages = open(os.path.join(base, "raw", "pdftotext.txt"), encoding="utf-8").read().split("\f")
    pdf_words = [norm(p) for p in pdf_pages]
    covered = [[False] * len(w) for w in pdf_words]

    def find(text, p0, p1):
        a = norm(text)
        if not a:
            return 0, 0, []
        span = [(p, k) for p in range(p0 - 1, min(p1, len(pdf_words))) for k in range(len(pdf_words[p]))]
        b = [pdf_words[p][k] for p, k in span]
        hits, fa, fb = match(a, b)
        for (p, k), f in zip(span, fb):
            if f:
                covered[p][k] = True
        return hits, len(a), [w for w, f in zip(a, fa) if not f]

    rows, flagged = [], []
    for a in issue["articles"]:
        hits = total = 0
        missing = []
        for i in a["items"]:
            h, t, miss = find(plain(i), i["page"], i.get("page_to", i["page"]))
            if miss and i["k"] in ("pull", "thought"):
                # boxed quotes sit beside the body text, so the second reading interleaves their lines:
                # for these, every word must be on the page, in any order
                bag = collections.Counter(w for p in range(i["page"] - 1, i.get("page_to", i["page"])) for w in pdf_words[p])
                need = collections.Counter(norm(plain(i)))
                h = sum(min(n, bag[w]) for w, n in need.items())
                miss = [w for w, n in need.items() if bag[w] < n]
            if miss and i["k"] not in ("pull", "thought"):
                # text that wraps round a picture or a box is read in a different order by the second reading:
                # words still unconfirmed are looked for among the page's words that nothing else has claimed
                pgs = range(i["page"] - 1, min(i.get("page_to", i["page"]), len(pdf_words)))
                free = collections.Counter(LIG.sub("", pdf_words[p][k]) for p in pgs for k in range(len(pdf_words[p])) if not covered[p][k])
                still = []
                for w in miss:
                    key = LIG.sub("", w)
                    if free[key] > 0:
                        free[key] -= 1; h += 1
                        for p in pgs:
                            k = next((k for k in range(len(pdf_words[p])) if not covered[p][k] and LIG.sub("", pdf_words[p][k]) == key), None)
                            if k is not None:
                                covered[p][k] = True; break
                    else:
                        still.append(w)
                miss = still
            hits, total = hits + h, total + t
            if miss:
                missing.append({"item": i["ids"][0], "kind": i["k"], "words": miss[:12]})
        for extra in (a["title"], a.get("kicker", ""), a.get("subtitle", ""), a.get("section", "")):
            find(extra, a["pages"][0], a["pages"][0])
        pct = round(100.0 * hits / total, 2) if total else 0.0
        rows.append({"n": a["n"], "id": a["id"], "title": a["title"], "pages": a["pages"], "words": total,
                     "match": pct, "missing": missing})
        if pct < THRESHOLD:
            flagged.append(a["n"])
    by_page = collections.OrderedDict()               # everything left out of a page, matched as one piece
    for s in log["skipped"]:
        by_page.setdefault(s["page"], []).append(s["text"])
    moved = {}
    for pg, texts in by_page.items():
        text = " ".join(texts)
        want = norm(text)
        got = len(set(want) & set(pdf_words[pg - 1])) if pg <= len(pdf_words) else 0
        if want and got < 0.7 * len(set(want)):       # cover pages can sit in a different order in the second reading
            best = max(range(len(pdf_words)), key=lambda p: len(set(want) & set(pdf_words[p])))
            moved[pg] = best + 1
        for t in texts:
            find(t, moved.get(pg, pg), moved.get(pg, pg))

    page_text = collections.defaultdict(str)
    for a in issue["articles"]:
        for i in a["items"]:
            for pg in range(i["page"], i.get("page_to", i["page"]) + 1):
                page_text[pg] += " " + " ".join(norm(plain(i)))
    for s in log["skipped"]:
        page_text[s["page"]] += " " + " ".join(norm(s["text"]))
        if s["page"] in moved:
            page_text[moved[s["page"]]] += " " + " ".join(norm(s["text"]))
    # cover spreads repeat the facing page's text outside the visible page area
    all_text = " ".join(page_text.values())
    # words of the PDF that are in no article and not on the left-out list
    unplaced, frontback = [], []
    article_pages = {p for a in issue["articles"] for p in range(a["pages"][0], a["pages"][1] + 1)}
    for p, (words, cov) in enumerate(zip(pdf_words, covered), 1):
        k = 0
        while k < len(words):
            if not cov[k]:
                j = k
                while j < len(words) and not cov[j]:
                    j += 1
                run = words[k:j]
                footer = (len(run) <= 15 and "issue" in run and ({"islam", "vol"} & set(run))) or \
                    set(run) <= {"towards", "global", "peace", "spiritual", "living", "spirit", "of", "islam"}
                # boxed quotes carry a shadow copy of their text in the PDF: a repeat of placed text is not new text
                repeat = " ".join(run) in page_text.get(p, "") or " ".join(run[1:-1]) in all_text
                if not repeat and not footer:
                    # the same, when the running footer is caught in the run or the quote's lines are interleaved
                    core = re.sub(r"(\d+ )?spirit of islam (vol \d+ )?issue \d+ [a-z]+ \d{4}( \d+)?", " ", " ".join(run))
                    core = re.sub(r"^(o )+|( o)+$", "", re.sub(r"\s+", " ", core).strip()).split()
                    grams = [" ".join(core[g:g + 4]) for g in range(max(1, len(core) - 3))]
                    boxed = collections.Counter(w for a in issue["articles"] for i in a["items"]
                                                if i["k"] in ("pull", "thought") and i["page"] <= p <= i.get("page_to", i["page"])
                                                for w in norm(plain(i)))
                    repeat = len(core) < 5 or sum(g in all_text for g in grams) >= 0.8 * len(grams) \
                        or sum(min(n, boxed[w]) for w, n in collections.Counter(core).items()) >= 0.9 * len(core)
                if len(run) >= 5 and not footer and not repeat:
                    (unplaced if p in article_pages else frontback).append(
                        {"page": p, "words": len(run), "text": " ".join(run[:30])})
                k = j
            else:
                k += 1
    # skipped pieces are stored with only their first 160 characters, so long ones show up here: drop those
    real_unplaced = unplaced

    total_words = sum(r["words"] for r in rows)
    overall = round(sum(r["match"] * r["words"] for r in rows) / max(total_words, 1), 2)
    check = {"slug": slug, "articles": rows, "overall_match": overall, "flagged": flagged,
             "unplaced": real_unplaced, "pdf_words": sum(len(w) for w in pdf_words), "article_words": total_words}
    json.dump(check, open(os.path.join(base, "check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---------------- review.md ----------------
    L = [f"# Review – {issue.get('label', slug)}", "",
         f"PDF `{issue['pdf']}`, {issue['pages']} pages. **{len(rows)} articles, {total_words:,} words, "
         f"word match {overall}%** (second reading of the PDF; flag below {THRESHOLD:.0f}%).", ""]
    L += ["## Articles", "", "| # | Pages | Section / kicker | Title | Words | Match |", "|---|---|---|---|---|---|"]
    for a, r in zip(issue["articles"], rows):
        flag = " ⚠" if r["match"] < THRESHOLD else ""
        pg = f"{a['pages'][0]}–{a['pages'][1]}" if a["pages"][0] != a["pages"][1] else str(a["pages"][0])
        L.append(f"| {a['n']} | {pg} | {a.get('kicker','')} | {a['title']} | {r['words']} | {r['match']}%{flag} |")
    miss = [(r["n"], m) for r in rows for m in r["missing"]]
    if miss:
        L += ["", "## Words the second reading did not confirm", "",
              "Usually a drop cap, a hyphen or a reference number; a long list means a real difference.", ""]
        for n, m in miss:
            L.append(f"- article {n}, `{m['item']}` ({m['kind']}): {' '.join(m['words'])}")
    L += ["", "## Left out of the e-version – please confirm", "",
          "Nothing here is in any article tab. Say if any of it should be included.", "",
          "| Page | Why | Words | Starts with |", "|---|---|---|---|"]
    grp = collections.OrderedDict()
    for s in log["skipped"]:
        g = grp.setdefault((s["page"], s["why"]), [0, ""])
        g[0] += s["words"]
        g[1] = g[1] or s["text"][:70].replace("|", "/")
    for (page, why), (w, t) in grp.items():
        L.append(f"| {page} | {why} | {w} | {t} |")
    L += ["", "## Text of the PDF that is in no article and not on the list above", ""]
    L += [f"- page {u['page']}, {u['words']} words: {u['text']}" for u in real_unplaced] or ["None."]
    if frontback:
        L += ["", "On cover, contents and advert pages (not part of any article) the second reading also saw:", ""]
        L += [f"- page {u['page']}, {u['words']} words: {u['text'][:140]}" for u in frontback]
    odd = [(a["n"], i) for a in issue["articles"] for i in a["items"] if i["k"] in ("other", "small")]
    if odd:
        L += ["", "## Pieces the rules could not classify (kept, shown as a small note)", ""]
        L += [f"- article {n}, page {i['page']}: {plain(i)[:110]}" for n, i in odd]
    L += ["", "## Automatic text adjustments", "",
          "Drop-cap openings set in capitals, put back to normal case: " + ("; ".join(log["lead_in"]) or "none") + ".", "",
          "Line-end hyphens the vocabulary could not settle (hyphen kept): " + (", ".join(log["hyphen_unsure"]) or "none") + "."]
    open(os.path.join(base, "review.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"{slug}: overall match {overall}%  flagged articles: {flagged or 'none'}  unplaced runs: {len(real_unplaced)}")
    sys.exit(1 if flagged or real_unplaced else 0)


if __name__ == "__main__":
    main()
