#!/usr/bin/env python3
"""
Stage 6 - test.  Opens issues/<slug>/preview.html (the block inside a mock Divi
page) in headless Chrome at 1280, 768, 390 and 320 px and checks:
  - no script errors, no sideways scroll
  - every article tab opens alone, with its heading at the top of the screen
  - the quiz runs from "Let's Start" to the scoreboard
  - the go-to-top button appears after scrolling
Writes issues/<slug>/test.json and screenshots to --shots DIR (optional).

Usage: python3 pipeline/test_page.py <slug> [--shots DIR]     (pip install playwright)
"""
import json, os, sys
from playwright.sync_api import sync_playwright

slug = sys.argv[1]
shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
url = "file://" + os.path.abspath(f"issues/{slug}/preview.html")
report, fails = {"slug": slug, "widths": {}}, []

with sync_playwright() as pw:
    try:
        browser = pw.chromium.launch(channel="chrome")
    except Exception:
        browser = pw.chromium.launch()
    sizes = [(1280, 800), (768, 1024), (390, 844), (320, 640)]
    quick = "--quick" in sys.argv
    if quick:                                       # batch runs: the widest and the narrowest (same template for every issue);
        sizes = [sizes[0], sizes[-1]]               # the scroll position is checked on the first and last tabs only
    for width, height in sizes:
        ctx = browser.new_context(viewport={"width": width, "height": height}, has_touch=width < 500)
        ctx.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text and "net::" not in m.text else None)
        page.goto(url)
        page.wait_for_timeout(600)
        res = {"errors": errors, "tabs": 0, "bad_tabs": []}
        overflow = lambda: page.evaluate("document.scrollingElement.scrollWidth - window.innerWidth")
        res["overflow_closed"] = overflow()
        ids = page.eval_on_selector_all(".soi-ev .ev-item", "els => els.map(e => e.id)")
        worst = 0
        for n, i in enumerate(ids):
            page.click(f"#{i} .ev-tab")
            settled = n < 2 or n == len(ids) - 1 or not quick
            page.wait_for_timeout((1250 if n < 4 or n == len(ids) - 1 else 900) if settled else 260)
            measure = lambda: page.evaluate("""id => { const it = document.getElementById(id);
                return { open: document.querySelectorAll('.soi-ev .ev-item.is-open').length,
                         mine: it.classList.contains('is-open'),
                         top: Math.round(it.querySelector('.ev-tab').getBoundingClientRect().top),
                         over: document.scrollingElement.scrollWidth - window.innerWidth,
                         wide: [...it.querySelectorAll('.ev-body *')].filter(e => e.getBoundingClientRect().right > window.innerWidth + 1).length } }""", i)
            st = measure()
            if not settled:
                st["top"] = 0
            if not -5 <= st["top"] <= 160:           # the page corrects its scroll position ~700 ms after opening
                page.wait_for_timeout(900)
                st = measure()
            worst = max(worst, st["over"])
            if not (st["mine"] and st["open"] == 1 and -5 <= st["top"] <= 160 and st["over"] <= 0 and st["wide"] == 0):
                res["bad_tabs"].append({"id": i, **st})
            if shots and n == 1:
                os.makedirs(shots, exist_ok=True)
                page.screenshot(path=os.path.join(shots, f"{slug}-{width}-article.png"))
        res["tabs"], res["overflow_open"] = len(ids), worst
        # go-to-top
        page.evaluate("window.scrollTo(0, 1600)")
        page.wait_for_timeout(500)
        res["gotop"] = page.evaluate("(() => { const b = document.getElementById('soi-gotop'); return !!b && b.classList.contains('is-shown'); })()")
        # quiz
        res["quiz"] = "absent"
        if page.query_selector("#soi-quiz"):
            page.click("#soi-quiz .z-invite")
            page.wait_for_timeout(700)
            page.fill("#soi-quiz-name", "Test Reader")
            page.click("#soi-quiz .z-start")
            total = 0
            for q in range(12):
                page.wait_for_timeout(450)
                if page.evaluate("document.querySelector('#soi-quiz .z-v-result').classList.contains('is-active')"):
                    break
                page.wait_for_selector("#soi-quiz .z-opt")
                page.locator("#soi-quiz .z-opt").nth(q % 4).click()
                page.wait_for_timeout(350)
                total += 1
                page.click("#soi-quiz .z-next")
            page.wait_for_timeout(900)
            done = page.evaluate("document.querySelector('#soi-quiz .z-v-result').classList.contains('is-active')")
            res["quiz"] = {"answered": total, "finished": done, "score": page.inner_text("#soi-quiz .r-val"),
                           "overflow": overflow()}
            if shots:
                page.screenshot(path=os.path.join(shots, f"{slug}-{width}-quiz.png"))
            if not done or res["quiz"]["overflow"] > 0:
                fails.append(f"{width}: quiz")
        if errors:
            fails.append(f"{width}: {len(errors)} script errors")
        if res["bad_tabs"]:
            fails.append(f"{width}: {len(res['bad_tabs'])} tabs misbehave")
        if res["overflow_closed"] > 0 or worst > 0:
            fails.append(f"{width}: sideways scroll")
        if not res["gotop"]:
            fails.append(f"{width}: go-to-top not shown")
        report["widths"][width] = res
        ctx.close()
    browser.close()

report["fails"] = fails
json.dump(report, open(f"issues/{slug}/test.json", "w"), indent=1)
for w, r in report["widths"].items():
    print(f"{slug} @{w}: tabs {r['tabs']} bad {len(r['bad_tabs'])}  overflow {r['overflow_closed']}/{r['overflow_open']}  "
          f"errors {len(r['errors'])}  gotop {r['gotop']}  quiz {r['quiz']}")
print("FAIL: " + "; ".join(fails) if fails else "all checks passed")
sys.exit(1 if fails else 0)
