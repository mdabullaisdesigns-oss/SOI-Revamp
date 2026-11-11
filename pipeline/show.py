#!/usr/bin/env python3
"""Print an article of issues/<slug>/issue.json item by item (for review).
Usage: python3 pipeline/show.py <slug> <article number or id> [--full]"""
import json, sys
slug, which = sys.argv[1], sys.argv[2]
full = "--full" in sys.argv
for a in json.load(open(f"issues/{slug}/issue.json", encoding="utf-8"))["articles"]:
    if str(a["n"]) == which or a["id"] == which:
        print(f"#{a['n']} {a['title']} | kicker={a['kicker']!r} author={a['author']!r} type={a['type']} pages={a['pages']}")
        for i in a["items"]:
            t = "".join(r[1] for r in i["runs"])
            extra = f" [{i.get('font','')} {i.get('size','')}]" if i["k"] == "other" else ""
            print(f"  {i['k']:<9} p{i['page']:<3}{i['ids'][0]:<8}{extra} {t if full else t[:100]}" + (f"  LINKS{i['links']}" if i.get("links") else ""))
