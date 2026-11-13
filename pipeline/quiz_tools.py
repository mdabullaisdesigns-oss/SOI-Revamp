"""Quiz helpers.

  python3 pipeline/quiz_tools.py digest <slug> [<slug> ...]   passages to write questions from (10 per issue)
  python3 pipeline/quiz_tools.py full <slug> [<slug> ...]     the full text of ten articles per issue, to write questions from
  python3 pipeline/quiz_tools.py compile <file.txt>            questions written as text -> issues/<slug>/quiz.json

Text format (the right answer is written first; the order shown to readers is shuffled here):
  ## 2014-03
  @ article-id
  Q question
  * right answer :: why
  - wrong answer :: why not      (three of these; the note may be left out)
  R what the article says
"""
import json, os, random, re, sys

SKIP = re.compile(r"newsletter|children|glossary|cps-|subscription|contents|letters", re.I)


def words(a):
    return " ".join(re.sub(r"\s+", " ", "".join(r[1] for r in i["runs"])).strip() for i in a["items"] if i["k"] in ("p", "qh", "ayah", "commentary")).split()


def picks(issue):
    ok = [a for a in issue["articles"] if a.get("audio") is not False and not SKIP.search(a["id"]) and len(words(a)) >= 120]
    out = []
    if len(ok) >= 10:
        step = len(ok) / 10
        out = [(ok[int(k * step)], 0) for k in range(10)]
    else:
        out = [(a, 0) for a in ok]
        for a in sorted(ok, key=lambda a: -len(words(a))):
            if len(out) >= 10:
                break
            out.append((a, 1))
        out.sort(key=lambda x: (x[0]["n"], x[1]))
    return out


def digest(slugs):
    for slug in slugs:
        issue = json.load(open(f"issues/{slug}/issue.json", encoding="utf-8"))
        print(f"## {slug}")
        for a, part in picks(issue):
            w = words(a)
            start = 0 if part == 0 else len(w) // 2
            print(f"@ {a['id']}{' (second passage)' if part else ''} | {a['title']}\n  {' '.join(w[start:start + 48])}")


def picks_full(issue, lo=200, hi=1000):
    """Ten articles spread through the issue, each short enough to be read in full; long ones give way to a neighbour."""
    ok = [a for a in issue["articles"] if a.get("audio") is not False and not SKIP.search(a["id"]) and a["id"] != "welcome"
          and len(words(a)) >= 120]
    fit = [a for a in ok if lo <= len(words(a)) <= hi]
    rest = sorted((a for a in ok if a not in fit), key=lambda a: abs(len(words(a)) - 600))
    pool = sorted(fit + rest[:max(0, 10 - len(fit))], key=lambda a: a["n"])
    if len(pool) > 10:
        step = len(pool) / 10
        out = [pool[int(k * step)] for k in range(10)]
    else:
        out = pool[:]
    return sorted(out, key=lambda a: a["n"])


def full(slugs):
    for slug in slugs:
        issue = json.load(open(f"issues/{slug}/issue.json", encoding="utf-8"))
        print(f"## {slug}")
        for a in picks_full(issue):
            print(f"@ {a['id']} | {a['title']}\n{' '.join(words(a))}")


_foot = {}


def printed(slug, pdf_page):
    """The page number printed in the magazine's footer for a PDF page."""
    if not pdf_page:
        return None
    if slug not in _foot:
        _foot[slug] = {}
        raw = f"issues/{slug}/raw/pages.json"
        for pg in (json.load(open(raw, encoding="utf-8")) if os.path.exists(raw) else []):
            for b in pg["blocks"]:
                for l in b["lines"]:
                    m = re.match(r"^(\d{1,3})\s+Spirit of Islam\s+Issue", l["t"].strip()) or \
                        re.match(r"^Spirit of Islam\s+Issue.*?\s(\d{1,3})$", l["t"].strip())
                    if m and l["bb"][1] > pg["h"] - 70:
                        _foot[slug][pg["n"]] = int(m.group(1))
    f = _foot[slug]
    if pdf_page in f:
        return f[pdf_page]
    near = min(f, key=lambda n: abs(n - pdf_page), default=None)     # pages without a footer: same offset as the nearest
    return pdf_page + (f[near] - near) if near else pdf_page


def compile_(path):
    cur, issues = None, {}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        tag, rest = line[0], line[1:].strip()
        if line.startswith("## "):
            cur = issues.setdefault(line[3:].strip(), [])
        elif tag == "@":
            cur.append({"link": rest.split()[0], "opts": []})
        elif tag == "Q":
            cur[-1]["q"] = rest
        elif tag in "*-":
            o, _, why = rest.partition(" :: ")
            cur[-1]["opts"].append([o.strip(), why.strip(), tag == "*"])
        elif tag == "R":
            cur[-1]["rationale"] = rest
        else:
            sys.exit(f"cannot read line: {line[:80]}")
    bad = 0
    for slug, qs in issues.items():
        issue = json.load(open(f"issues/{slug}/issue.json", encoding="utf-8"))
        arts = {a["id"]: a for a in issue["articles"]}
        out, errs = [], []
        if len(qs) != 10:
            errs.append(f"{len(qs)} questions")
        for n, q in enumerate(qs):
            a = arts.get(q["link"])
            if not a:
                errs.append(f"unknown article {q['link']}"); continue
            if len(q["opts"]) != 4 or sum(o[2] for o in q["opts"]) != 1 or not q.get("q") or not q.get("rationale") \
                    or any(not o[0] for o in q["opts"]) or not next((o[1] for o in q["opts"] if o[2]), "") or len({o[0].lower() for o in q["opts"]}) != 4:
                errs.append(f"question {n + 1} is incomplete"); continue
            right = next(o[0] for o in q["opts"] if o[2]).rstrip(".")
            for o in q["opts"]:                      # a wrong answer written without a note points to the right one
                if not o[2] and not o[1]:
                    o[1] = f"Not quite. The article says: {right}."
            opts = q["opts"][:]
            random.Random(f"{slug}-{n}").shuffle(opts)
            page = printed(slug, (a.get("pages") or [None])[0])
            out.append({"article": a["title"], "page": page, "link": a["id"], "q": q["q"],
                        "options": [[o[0], o[1]] for o in opts], "answer": [o[2] for o in opts].index(True),
                        "rationale": q["rationale"]})
        if errs:
            bad += 1
            print(f"{slug}: NOT written – " + "; ".join(errs))
        else:
            json.dump({"questions": out}, open(f"issues/{slug}/quiz.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(issues) - bad} quizzes written, {bad} with problems")


if __name__ == "__main__":
    {"digest": digest, "full": full}[sys.argv[1]](sys.argv[2:]) if sys.argv[1] in ("digest", "full") else compile_(sys.argv[2])
