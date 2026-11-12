#!/usr/bin/env python3
"""
Runs stages 2-6 for many issues and writes one line per issue to
inventory/batch-status.csv (the only thing a person needs to read: the rows
whose "result" is not "ok").

Usage: python3 pipeline/batch.py [--only slug,slug] [--no-test] [--jobs N]
An issue is taken through the PDF route if issues/<slug>/raw/pages.json exists
and issues/<slug>/route.txt does not say "wp" or "skip".
"""
import concurrent.futures as cf, csv, json, os, re, subprocess, sys

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))


def run(*a, timeout=900):
    try:
        r = subprocess.run([PY, os.path.join(HERE, a[0]), *a[1:]], capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    except subprocess.TimeoutExpired:
        return 99, ["timeout"]


def route(slug):
    p = f"issues/{slug}/route.txt"
    return open(p).read().split()[0] if os.path.exists(p) else "pdf"


def one(slug, test=True):
    row = {"slug": slug, "route": route(slug), "result": "ok", "problems": []}
    if row["route"] == "pdf":
        rc, out = run("structure.py", slug)
        if rc:
            row["result"] = "FAIL"; row["problems"].append("structure: " + out[0][:160]); return row
        rc, out = run("check.py", slug)
    else:
        g = next((l.split() for l in open("sources/gary-issues.txt", encoding="utf-8") if l.split()[:1] == [slug]), None)
        if g:
            run("from_wp.py", *g)                    # the page text again, then what the page lacks from the PDF
            run("add_from_pdf.py", slug)
        run("narrate.py", "prepare", slug)
        if os.path.isdir(f"issues/{slug}/audio-raw"):
            run("align.py", slug)                        # timings + match for the recordings that exist
        rc, out = run("check_wp.py", slug)
    try:
        c = json.load(open(f"issues/{slug}/check.json"))
        i = json.load(open(f"issues/{slug}/issue.json"))
        row.update(articles=len(i["articles"]), words=sum(a["words"] for a in i["articles"]), match=c.get("overall_match"),
                   label=i.get("label", ""), pdf=i.get("pdf", ""))
        row["renarrate"] = []
        if c.get("flagged") and row["route"] == "pdf":   # Gary issues: the web text is used as it is (decided),
            row["problems"].append(f"{len(c['flagged'])} article(s) below 99% word match")   # so an edited article is not a fault
        if c.get("unplaced"):
            row["problems"].append(f"{len(c['unplaced'])} run(s) of PDF text in no article and not listed")
        for w in c.get("warnings", []):
            # a recording that does not match, or is missing: decided - the article waits for a new Gary narration
            (row["renarrate"] if re.match(r"(recording of|no recording)", w) else row["problems"]).append(w)
        # sanity of the structure itself (the word match cannot see a title in the wrong place)
        if not i.get("number"):
            row["problems"].append("issue number / period not found in the running footer")
        if len(i["articles"]) < 8:
            row["problems"].append(f"only {len(i['articles'])} articles")
        for a in i["articles"]:
            if a["words"] < 120 and all(x["k"] in ("bio", "small", "h", "other") for x in a["items"]):
                row["problems"].append(f"article {a['n']} “{a['title']}” has a heading and an author note but no text")
            elif a["words"] < 60:
                row["problems"].append(f"article {a['n']} “{a['title']}” has only {a['words']} words")
            elif a["words"] > 6000 and a["words"] / max(1, a["pages"][1] - a["pages"][0] + 1) > 520:
                row["problems"].append(f"article {a['n']} “{a['title']}” has {a['words']} words (two articles joined?)")
        # a lot of running text left out of the middle of the magazine deserves a second look
        lg = f"issues/{slug}/raw/structure-log.json"
        if os.path.exists(lg) and row["route"] == "pdf":
            per = {}
            for sk in json.load(open(lg))["skipped"]:
                if 5 <= sk["page"] <= i["pages"] - 4 and sk.get("role") in ("body", "dropcap", None) or (5 <= sk["page"] <= i["pages"] - 4 and sk["why"].startswith(("non-article", "outside"))):
                    per.setdefault(sk["page"], []).append(sk)
            for pg, sks in sorted(per.items()):
                text = " ".join(x["text"] for x in sks)
                n = sum(x["words"] for x in sks)
                if n > 180 and not re.search(r"(?i)subscri|contents|cpsglobal\.org/|goodword|A/c|available at|bookstore|book ?shop|price|order", text):
                    row["problems"].append(f"page {pg}: {n} words left out as “{sks[0]['why']}” (“{text[:50]}…”)")
        others = sum(1 for a in i["articles"] for x in a["items"] if x["k"] == "other")
        if others:
            row["problems"].append(f"{others} block(s) the rules could not classify (shown as notes)")
    except Exception as e:
        row["result"] = "FAIL"; row["problems"].append(f"check: {out[0][:120]} {e}"); return row
    rc, out = run("narrate.py", "prepare", slug)
    if rc:
        row["problems"].append("narration prep: " + out[0][:120])
    else:
        n = json.load(open(f"issues/{slug}/narration.json"))
        row["chars"] = n.get("chars")
    rc, out = run("build.py", slug, "--preview")
    if rc:
        row["result"] = "FAIL"; row["problems"].append("build: " + out[0][:160]); return row
    row["quiz"] = "yes" if os.path.exists(f"issues/{slug}/quiz.json") else "pending"
    row["audio"] = "yes" if os.path.exists(f"issues/{slug}/audio.json") else "pending"
    if test:
        quick = ["--quick"] if "--quick" in sys.argv else []
        rc, out = run("test_page.py", slug, *quick)
        if rc:
            rc, out = run("test_page.py", slug, *quick)  # once more: a slow machine can miss a scroll
        if rc:
            row["problems"].append("browser test: " + out[0][:200])
    if row["problems"]:
        row["result"] = "CHECK"
    return row


if __name__ == "__main__":
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    slugs = sorted(s for s in os.listdir("issues") if os.path.exists(f"issues/{s}/raw/pages.json") or route(s) == "wp")
    slugs = [s for s in slugs if route(s) != "skip"]
    if arg("--only"):
        slugs = [s for s in slugs if s in arg("--only").split(",")]
    test = "--no-test" not in sys.argv
    rows = []
    with cf.ThreadPoolExecutor(int(arg("--jobs", "4"))) as ex:
        for r in ex.map(lambda s: one(s, test), slugs):
            rows.append(r)
            print(f"{r['slug']:<9} {r['result']:<5} {r.get('articles', ''):>3} art {r.get('match', '')}%  {'; '.join(r['problems'])}", flush=True)
    old = {}
    if arg("--only") and os.path.exists("inventory/batch-status.csv"):
        old = {r["slug"]: r for r in csv.DictReader(open("inventory/batch-status.csv", encoding="utf-8"))}
    for r in rows:
        r["problems"] = "; ".join(r["problems"])
        r["renarrate"] = "; ".join(r.get("renarrate", []))
        old[r["slug"]] = r
    cols = ["slug", "label", "route", "pdf", "articles", "words", "match", "chars", "quiz", "audio", "result", "problems", "renarrate"]
    with open("inventory/batch-status.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader()
        for s in sorted(old):
            w.writerow(old[s])
    bad = [r for r in old.values() if r["result"] != "ok"]
    print(f"\n{len(old)} issues: {len(old) - len(bad)} ok, {len(bad)} need a look")
