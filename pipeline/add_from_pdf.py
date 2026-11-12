#!/usr/bin/env python3
"""
Gary-audio issues: text that is in the printed magazine but not on the WordPress page is added from the PDF.
issues/<slug>/pdf-extra.json lists the sections:
  [{"pages": [first, last], "title": "CPS Newsletter", "type": "newsletter", "audio": false,
    "mode": "rules" | "blocks"}]
  rules   the section is found by the magazine's typography (structure.py), for issues in the 2013-2024 layout
  blocks  the pages are read block by block, top to bottom (the 2025+ layout)
The section goes into issue.json in page order.  Sections with "audio": false are never narrated.
Run after from_wp.py:  python3 pipeline/add_from_pdf.py <slug>
"""
import json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import structure


def main():
    slug = sys.argv[1]
    base = f"issues/{slug}"
    cfg = base + "/pdf-extra.json"
    if not os.path.exists(cfg):
        return
    issue = json.load(open(base + "/issue.json", encoding="utf-8"))
    pages = json.load(open(base + "/raw/pages.json", encoding="utf-8"))
    log = json.load(open(base + "/raw/wp-log.json", encoding="utf-8"))
    rules = None
    for ft in json.load(open(cfg, encoding="utf-8")):
        if ft.get("mode") == "rules":
            if rules is None:
                tmp = f"issues/_t-{slug}"
                shutil.rmtree(tmp, ignore_errors=True)
                os.makedirs(tmp)
                shutil.copytree(base + "/raw", tmp + "/raw")
                subprocess.run([sys.executable, "pipeline/structure.py", f"_t-{slug}"], capture_output=True)
                rules = json.load(open(tmp + "/issue.json", encoding="utf-8"))["articles"]
                shutil.rmtree(tmp)
            a = next(x for x in rules if x["pages"][0] == ft["pages"][0] and x["pages"][1] <= ft["pages"][1] + 1)
            if not ft.get("audio", True):
                a["audio"] = False
        else:
            ft = dict(ft, links=True, columns=ft.get("columns", 1), short_heads=True,
                      skip=ft.get("skip", r"kindly open the magazine in a\s+pdf reader"))
            a = structure.feature_article(pages, ft)
            for x in ft["_left_out"]:
                log["skipped"].append({"title": x["text"], "why": f"PDF page {x['page']}: note about the PDF / button label (its link is kept)"})
        a["from_pdf"] = True
        have = {x["id"] for x in issue["articles"]}
        if a["id"] in have:
            a["id"] += "-print"
        pos = next((k for k, x in enumerate(issue["articles"]) if x.get("pages") and x["pages"][0] > ft["pages"][0]), len(issue["articles"]))
        issue["articles"].insert(pos, a)
        print(f"{slug}: added “{a['title']}” from PDF pages {ft['pages'][0]}-{ft['pages'][1]} ({a['words']} words, {len(a['items'])} items)")
    for n, a in enumerate(issue["articles"], 1):
        a["n"] = n
    json.dump(issue, open(base + "/issue.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(log, open(base + "/raw/wp-log.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
