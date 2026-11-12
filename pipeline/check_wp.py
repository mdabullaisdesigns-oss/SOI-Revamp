#!/usr/bin/env python3
"""
Stage 3 for the WordPress-route (Gary audio) issues.

The page text is the master copy for these issues, so the PDF is used only as a
cross-check:
  1. every article's words are looked up in the PDF (second reading,
     raw/pdftotext.txt) - a low figure means the page and the magazine differ;
  2. every PDF page is checked the other way round - a page of text that is on
     no web article is listed (cover, contents and adverts are expected there);
  3. every article should have a recording on the site, and every recording an
     article.
Writes check.json and review.md.   Usage: python3 pipeline/check_wp.py <slug>
"""
import collections, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check import norm, match

THRESHOLD = 97.0          # the page text was edited by hand after the magazine went to print
EXPECTED = re.compile(r"contents|chatgpt|subscri|bank|cheque|published|printed|goodword|available at|order|www\.|issue \d+", re.I)


def main():
    slug = sys.argv[1]
    base = f"issues/{slug}"
    issue = json.load(open(base + "/issue.json", encoding="utf-8"))
    log = json.load(open(base + "/raw/wp-log.json", encoding="utf-8"))
    audio = json.load(open(base + "/audio-source.json", encoding="utf-8"))
    timed = json.load(open(base + "/audio.json", encoding="utf-8")) if os.path.exists(base + "/audio.json") else {}
    plain = lambda i: "".join(r[1] for r in i["runs"])
    warnings, rows, flagged, left = [], [], [], []
    have_pdf = os.path.exists(base + "/raw/pdftotext.txt")
    if have_pdf:
        pages = [norm(p) for p in open(base + "/raw/pdftotext.txt", encoding="utf-8").read().split("\f")]
        covered = [[False] * len(w) for w in pages]
        grams = collections.defaultdict(set)
        for pn, w in enumerate(pages):
            for k in range(len(w) - 4):
                grams[tuple(w[k:k + 5])].add(pn)
    for a in issue["articles"]:
        text = " ".join(plain(i) for i in a["items"])
        w = norm(text)
        row = {"n": a["n"], "id": a["id"], "title": a["title"], "words": len(w), "audio": a["id"] in audio,
               "match": None, "pages": a["pages"], "missing": []}
        if have_pdf and w:
            votes = collections.Counter(pn for k in range(0, len(w) - 4, 3) for pn in grams.get(tuple(w[k:k + 5]), ()))
            good = sorted(pn for pn, v in votes.items() if v >= max(3, 0.04 * sum(votes.values())))
            if good:
                p0, p1 = good[0], good[-1]
                span = [(p, k) for p in range(p0, p1 + 1) for k in range(len(pages[p]))]
                hits, fa, fb = match(w, [pages[p][k] for p, k in span])
                for (p, k), f in zip(span, fb):
                    if f:
                        covered[p][k] = True
                tw = norm(a["title"] + " " + a.get("kicker", ""))
                for p in range(p0, p1 + 1):                    # the heading words of the article's first page
                    for k, x in enumerate(pages[p]):
                        if x in tw:
                            covered[p][k] = True
                row["match"] = round(100.0 * hits / len(w), 2)
                row["pages"] = a["pages"] = [p0 + 1, p1 + 1]
                miss, run = [], []
                for x, f in zip(w, fa):
                    if not f:
                        run.append(x)
                    elif run:
                        miss.append(" ".join(run)); run = []
                if run:
                    miss.append(" ".join(run))
                row["missing"] = [m for m in miss if len(m.split()) >= 4][:6]
            else:
                row["match"] = 0.0
            if row["match"] < THRESHOLD:
                flagged.append(a["n"])
        rows.append(row)
        if a["id"] not in audio and a["type"] not in ("newsletter",):
            warnings.append(f"no recording on the site for article {a['n']} “{a['title']}”")
        if a["id"] in timed and timed[a["id"]].get("match") is not None and timed[a["id"]]["match"] < 95:
            warnings.append(f"recording does not match the text of article {a['n']} “{a['title']}” ({timed[a['id']]['match']}%)")
    for u in log["audio_unmatched"]:
        warnings.append(f"recording “{u['title']}” belongs to no article")
    if have_pdf:
        for pn, w in enumerate(pages):
            un = [x for x, c in zip(w, covered[pn]) if not c]
            if len(un) >= 40 and len(un) > 0.4 * len(w):
                raw = " ".join(un)
                expected = pn < 4 or pn >= len(pages) - 4 or bool(EXPECTED.search(" ".join(w[:60])))
                left.append({"page": pn + 1, "words": len(un), "of": len(w), "starts": " ".join(un[:14]), "expected": expected})
                if not expected and len(un) > 200:
                    warnings.append(f"PDF page {pn + 1}: {len(un)} words are on no web article (“{' '.join(un[:8])}…”)")
        json.dump(issue, open(base + "/issue.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    else:
        warnings.append("PDF text not available for the cross-check")
    if flagged:
        pass
    tot = sum(r["words"] for r in rows if r["match"] is not None)
    overall = round(sum(r["words"] * r["match"] for r in rows if r["match"] is not None) / tot, 2) if tot else None
    json.dump({"slug": slug, "route": "wp", "articles": rows, "overall_match": overall, "flagged": flagged, "unplaced": [],
               "warnings": warnings, "pdf_pages_not_on_page": left, "left_out": log["skipped"]},
              open(base + "/check.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = [f"# Review – {slug}", "", f"Text from the WordPress page **{log['page_title']}** (id {log['page_id']}). "
          f"**{len(rows)} articles, {sum(r['words'] for r in rows):,} words**; cross-check with `{issue.get('pdf', '')}`: "
          f"**{overall}%** of the page's words are in the PDF (flag below {THRESHOLD:.0f}%).", "",
          "## Articles", "", "| # | PDF pages | Section / kicker | Title | Words | In PDF | Recording |", "|---|---|---|---|---|---|---|"]
    for a, r in zip(issue["articles"], rows):
        pg = "–".join(str(x) for x in dict.fromkeys(r["pages"])) if r["pages"][0] else ""
        rec = ("timed" if a["id"] in timed else "on site, not timed yet") if r["audio"] else "**none**"
        md.append(f"| {r['n']} | {pg} | {a['kicker']} | {a['title']} | {r['words']} | {r['match']}% | {rec} |")
    md += ["", "## Needs a look", ""] + ([f"- {w}" for w in warnings] or ["Nothing."])
    diff = [(r["n"], m) for r in rows for m in r["missing"]]
    if diff:
        md += ["", "## Passages on the web page that the PDF does not have (4+ words)", ""] + [f"- article {n}: {m}" for n, m in diff[:40]]
    md += ["", "## Left out of the e-version", "", "| What | Why | Words |", "|---|---|---|"]
    md += [f"| {s['title'][:70]} | {s['why']} | {s['words']} |" for s in log["skipped"]] or ["| – | nothing | |"]
    if left:
        md += ["", "## PDF pages whose text is not on the web page", "", "| Page | Words not on the page | Starts with | Expected (cover, contents, advert) |", "|---|---|---|---|"]
        md += [f"| {l['page']} | {l['words']} of {l['of']} | {l['starts']} | {'yes' if l['expected'] else '**no**'} |" for l in left]
    if log["case"]:
        md += ["", "## Automatic text adjustments", "", "Drop-cap openings set in capitals, put back to normal case: " + "; ".join(log["case"]) + "."]
    open(base + "/review.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"{slug}: page vs PDF {overall}%  flagged articles: {flagged or 'none'}  warnings: {len(warnings)}")
    sys.exit(1 if flagged or warnings else 0)


if __name__ == "__main__":
    main()
