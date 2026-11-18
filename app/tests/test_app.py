#!/usr/bin/env python3
"""Browser test of app/www (the files packed in the app): tabs, links, offline reading, Continue where you
left, saved issues/articles, search, and no sideways scroll. The website (app-config.json: remote) is answered
from dist/ and switched off to imitate "no internet".
    python3 site/build_site.py && python3 app/build_app.py && python3 app/tests/test_app.py
Does NOT test the native parts (lock-screen controls, background audio, share sheet) – those need a real phone."""
import asyncio, json, os, subprocess, sys, time
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REMOTE = json.load(open(ROOT + '/app/app-config.json'))['remote'].rstrip('/')
N = len(json.load(open(ROOT + '/dist/issues.json'))['issues'])
PACKED = json.load(open(ROOT + '/app/www/assets/app-config.json'))['bundled']
B = 'http://localhost:8765'; res = []
def ok(name, c, info=''):
    res.append((name, bool(c))); print('PASS' if c else 'FAIL', name, info if not c else '')
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(); ctx = await br.new_context(viewport={'width': 390, 'height': 844})
        st = {'online': True}; ext = []; errs = []
        async def handle(route):
            u = route.request.url
            if u.startswith(B): return await route.continue_()
            ext.append(u)
            if not st['online'] or not u.startswith(REMOTE): return await route.abort()
            path = u[len(REMOTE):].split('?')[0]
            f = ROOT + '/dist' + path + ('index.html' if path.endswith('/') else '')
            if os.path.exists(f):
                await route.fulfill(body=open(f, 'rb').read(), content_type='text/html' if f.endswith('html') else 'application/json', headers={'Access-Control-Allow-Origin': '*'})
            else: await route.fulfill(status=404, body='no')
        await ctx.route('**/*', handle)
        pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B + '/index.html'); await pg.wait_for_selector('.soi-app-issue'); await pg.wait_for_timeout(600)
        ok('home: four tabs, Home current', await pg.locator('#soi-app-tabs a').count() == 4 and await pg.inner_text('#soi-app-tabs a[aria-current]') == 'Home')
        ok('home: latest issue cover with Read / Listen / Save', await pg.locator('.soi-app-issue').count() == 3 and await pg.locator('.soi-app-issue >> nth=0 >> .soi-app-b-listen').count() == 1)
        ok('home: cover picture loads', await pg.evaluate("(()=>{const i=document.querySelector('.soi-app-issue img');return !!i&&i.complete&&i.naturalWidth>300})()"))
        ok('home: In this issue lists 4 articles', await pg.locator('#soi-app-arts a').count() == 5)
        ok('home: quote of the day', len(await pg.inner_text('.soi-app-quote-t')) > 20)
        ok('no Google Fonts requests', not [u for u in ext if 'fonts.g' in u], str(ext[:2]))
        ok('website header and menu hidden in the app', await pg.evaluate("!document.querySelector('.soi-hdr')||getComputedStyle(document.querySelector('.soi-hdr')).display==='none'"))
        await pg.click('.soi-app-issue >> nth=0 >> .soi-app-b-read'); await pg.wait_for_selector('.soi-ev .ev-item')
        ok('latest issue opens from inside the app, with app bar and no tabs', f'/issues/{PACKED[-1]}/index.html' in pg.url and await pg.locator('#soi-app-bar').count() == 1 and await pg.locator('#soi-app-tabs').count() == 0, pg.url)
        ok('  header/menu not shown, quiz present', await pg.evaluate("getComputedStyle(document.querySelector('.soi-menubar')).display==='none'") and await pg.locator('#soi-quiz').count() == 1)
        ok('  Save and Share on every article', await pg.locator('.soi-ev .soi-acts').count() == await pg.locator('.soi-ev .ev-item .ev-meta').count() > 5)
        # an older issue: fetched once, then offline
        await pg.goto(B + '/archive/index.html'); await pg.wait_for_selector('a.soi-icard-link')
        await pg.click('a.soi-icard-link[href="/issues/2018-06/"]'); await pg.wait_for_selector('.soi-ev .ev-item', timeout=8000)
        ok('old issue fetched once and shown', 'reader.html' in pg.url and 'issue=2018-06' in pg.url, pg.url)
        await pg.evaluate("document.querySelectorAll('.soi-ev .ev-item')[2].querySelector('.ev-tab').click()"); await pg.wait_for_timeout(900)
        await pg.mouse.wheel(0, 900); await pg.wait_for_timeout(1700); await pg.mouse.wheel(0, 250); await pg.wait_for_timeout(1700)
        y0 = await pg.evaluate('scrollY'); aid = await pg.evaluate("document.querySelectorAll('.soi-ev .ev-item')[2].id")
        await pg.evaluate("document.querySelector('.soi-ev .ev-item.is-open .soi-act-save').click()")
        prog = json.loads(await pg.evaluate("localStorage.getItem('soiProgress')") or '{}')
        ok('reading place remembered (article + position)', prog.get('slug') == '2018-06' and 'soi-' + prog.get('id', '') == aid and prog.get('frac', 0) > 0, str(prog))
        st['online'] = False
        await pg.goto(B + '/index.html'); await pg.wait_for_selector('.soi-app-cont')
        ok('OFFLINE home: Continue where you left card', prog.get('title', '~') in await pg.inner_text('.soi-app-cont'))
        await pg.click('.soi-app-cont'); await pg.wait_for_selector('.soi-ev .ev-item'); await pg.wait_for_timeout(1800)
        y1 = await pg.evaluate('scrollY'); op = await pg.evaluate("(document.querySelector('.soi-ev .ev-item.is-open')||{}).id")
        ok('OFFLINE: resumes the same article at the same place', op == aid and abs(y1 - y0) < 260, f'{op} {y0}->{y1}')
        await pg.evaluate("localStorage.setItem('soiProgress', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('soiProgress')),{t:192,dur:400})))")
        await pg.goto(B + '/index.html'); await pg.wait_for_selector('.soi-app-cont')
        ok('  audio time shown on the card', 'paused at 3:12' in await pg.inner_text('.soi-app-cont'))
        await pg.goto(B + '/reader.html?issue=2014-05'); await pg.wait_for_timeout(1500)
        ok('OFFLINE: unsaved issue gives a clear message', 'not on your phone yet' in await pg.inner_text('#soi-app-reader'))
        await pg.goto(B + '/search.html'); await pg.fill('#soi-app-q', 'patience'); await pg.wait_for_selector('.soi-app-res', timeout=10000)
        href = await pg.get_attribute('.soi-app-res', 'href'); r = await pg.evaluate("(h)=>window.soiApp.route(h)", href)
        ok('OFFLINE: search works and results open in the app', '/issues/' in href and ('reader.html' in r or 'index.html#' in r), f'{href} -> {r}')
        await pg.fill('#soi-app-q', '51 : 56'); await pg.wait_for_timeout(1200)
        ok('OFFLINE: search by Quran reference', await pg.locator('.soi-app-res').count() > 3 and '51:56' in await pg.inner_text('#soi-app-results'))
        await pg.goto(B + '/quotes/index.html'); await pg.wait_for_selector('#soi-q-list button[data-act="save"]'); await pg.click('#soi-q-list button[data-act="save"] >> nth=1')
        ok('OFFLINE: quotes page, save a quote', await pg.evaluate("JSON.parse(localStorage.getItem('soiSavedQuotes')).length") == 1)
        st['online'] = True
        await pg.goto(B + '/saved.html'); await pg.wait_for_selector('.soi-app-si'); await pg.wait_for_timeout(500)
        s = await pg.inner_text('.soi-app-savedhead'); ok('saved: packed + opened issues, offline badges', await pg.locator('.soi-app-si').count() == len(PACKED) + 1 and f'{len(PACKED)+1} downloaded' in s, s)
        await pg.click('[data-seg="articles"]'); ok('saved: the saved article', await pg.locator('.soi-app-cards a').count() == 1)
        await pg.click('[data-seg="quotes"]'); ok('saved: the saved quote', await pg.locator('.soi-app-quotes a').count() == 1)
        await pg.click('[data-seg="issues"]'); await pg.wait_for_selector('#soi-app-all'); t0 = time.time(); await pg.click('#soi-app-all')
        await pg.wait_for_function("!document.getElementById('soi-app-all')", timeout=180000); await pg.wait_for_timeout(400)
        ok('saved: Save all', await pg.locator('.soi-app-si').count() == N, str(await pg.locator('.soi-app-si').count())); print('   (%.0fs)' % (time.time() - t0))
        await pg.click('.soi-app-rm >> nth=0'); await pg.wait_for_timeout(600); ok('saved: remove one issue', await pg.locator('.soi-app-si').count() == N - 1)
        await pg.goto(B + '/profile.html'); await pg.wait_for_selector('.soi-app-rank')
        ok('profile: sample data marked as sample', await pg.locator('.soi-app-sample').count() >= 1 and await pg.locator('.soi-app-cal span').count() == 14)
        await pg.click('.soi-app-rank'); await pg.wait_for_selector('#soi-app-board > div')
        a = await pg.inner_text('#soi-app-board'); await pg.click('[data-b="All time"]'); b = await pg.inner_text('#soi-app-board')
        ok('gems: leaderboard switches This week / All time, marked sample and proposed', a != b and await pg.locator('.soi-app-sample').count() == 1 and 'PROPOSED' in await pg.inner_text('.soi-app-earn'))
        bad = []
        pages = ('/index.html', '/search.html', '/saved.html', '/profile.html', '/gems.html', f'/issues/{PACKED[-1]}/index.html', '/reader.html?issue=2019-01', '/archive/index.html', '/quotes/index.html')
        for w in (320, 390, 768, 1280):
            await pg.set_viewport_size({'width': w, 'height': 800})
            for u in pages:
                await pg.goto(B + u); await pg.wait_for_timeout(700)
                sw = await pg.evaluate("document.documentElement.scrollWidth")
                if sw > w: bad.append((w, u, sw))
        ok(f'no sideways scroll 320–1280 on {len(pages)} pages', not bad, str(bad))
        await pg.goto(B + f'/issues/{PACKED[-2]}/index.html')
        ok('player audio goes through the app (for lock-screen controls)', await pg.evaluate("window.Audio.soi===true"))
        ok('no script errors', not errs, str(errs[:3]))
        await br.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '-d', ROOT + '/app/www'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try: asyncio.run(main())
finally: srv.terminate()
print(sum(1 for r in res if r[1]), 'of', len(res), 'passed'); sys.exit(0 if all(r[1] for r in res) else 1)
