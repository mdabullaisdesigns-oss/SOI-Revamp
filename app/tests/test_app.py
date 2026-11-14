#!/usr/bin/env python3
"""Browser test of app/www (the files packed in the app): links, offline reading, saved issues, search.
The website (app-config.json: remote) is answered from dist/, and switched off to imitate "no internet".
    python3 site/build_site.py && python3 app/build_app.py && python3 app/tests/test_app.py
Does NOT test the native parts (lock-screen controls, background audio) – those need a real phone."""
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
        br = await p.chromium.launch(); ctx = await br.new_context(viewport={'width': 390, 'height': 800})
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
        await pg.goto(B + '/index.html'); await pg.wait_for_timeout(500)
        ok('home loads, Saved link added', await pg.locator('.soi-nav .soi-app-navlink').count() == 1)
        ok('no Google Fonts requests', not [u for u in ext if 'fonts.g' in u], str(ext[:2]))
        ok('body font packed in the app', await pg.evaluate("document.fonts.load('16px \"Plus Jakarta Sans\"').then(f=>f.length>0)"))
        await pg.click('a.soi-latest'); await pg.wait_for_load_state()
        ok('latest issue opens from inside the app', f'/issues/{PACKED[-1]}/index.html' in pg.url and await pg.locator('.soi-ev .ev-item').count() > 5, pg.url)
        ok('quiz present', await pg.locator('#soi-quiz').count() == 1)
        await pg.click('.soi-nav a[href="/archive/"]'); await pg.wait_for_load_state()
        ok('archive via link', pg.url.endswith('/archive/index.html'), pg.url)
        await pg.click('a.soi-card[href="/issues/2013-01/"]'); await pg.wait_for_selector('.soi-ev .ev-item', timeout=8000)
        ok('old issue fetched once and shown', 'reader.html?issue=2013-01' in pg.url, pg.url)
        h0 = await pg.evaluate("document.querySelectorAll('.soi-ev .ev-item')[2].getBoundingClientRect().height")
        await pg.evaluate("document.querySelectorAll('.soi-ev .ev-item')[2].querySelector('.ev-tab').click()"); await pg.wait_for_timeout(900)
        h1 = await pg.evaluate("document.querySelectorAll('.soi-ev .ev-item')[2].getBoundingClientRect().height")
        ok('  its tabs work', h1 > h0 + 100, f'{h0}->{h1}')
        ok('  Saved link + app styles on fetched page', await pg.locator('.soi-app-navlink').count() == 1 and await pg.evaluate("document.documentElement.classList.contains('soi-app')"))
        st['online'] = False
        await pg.goto(B + '/index.html'); await pg.goto(B + '/reader.html?issue=2013-01'); await pg.wait_for_selector('.soi-ev .ev-item', timeout=8000)
        ok('OFFLINE: saved issue opens', True)
        aid = await pg.evaluate("document.querySelectorAll('.soi-ev .ev-item')[3].id")
        await pg.goto(B + '/index.html'); await pg.goto(B + '/reader.html?issue=2013-01#' + aid); await pg.wait_for_selector('.soi-ev .ev-item'); await pg.wait_for_timeout(1500)
        ok('OFFLINE: link to one article opens that article', await pg.evaluate("(id)=>document.getElementById(id).querySelector('.ev-panel').getBoundingClientRect().height>100", aid), aid)
        await pg.goto(B + '/reader.html?issue=2014-05'); await pg.wait_for_timeout(1500)
        t = await pg.inner_text('#soi-app-reader')
        ok('OFFLINE: unsaved issue gives a clear message', 'not on your phone yet' in t, t[:60])
        await pg.goto(B + '/search/index.html'); await pg.wait_for_selector('.pagefind-ui__search-input'); await pg.fill('.pagefind-ui__search-input', 'patience'); await pg.wait_for_selector('.pagefind-ui__result-link', timeout=10000)
        href = await pg.get_attribute('.pagefind-ui__result-link', 'href')
        r = await pg.evaluate("(h)=>window.soiApp.route(h)", href)
        ok('OFFLINE: search works and results open in the app', '/issues/' in href and ('reader.html?issue=' in r or 'index.html#' in r), f'{href} -> {r}')
        await pg.goto(B + '/quotes/index.html'); await pg.wait_for_timeout(800)
        ok('OFFLINE: quotes page', await pg.locator('.soi-q').count() > 3)
        st['online'] = True
        await pg.goto(B + '/saved.html'); await pg.wait_for_selector('.soi-app-row'); await pg.wait_for_timeout(500)
        s = await pg.inner_text('.soi-app-stat'); ok('saved page lists every issue', await pg.locator('.soi-app-row').count() == N and s.startswith(f'{len(PACKED)+1} of {N}'), s)
        await pg.click('.soi-app-row[data-slug="2020-03"] .soi-app-get'); await pg.wait_for_selector('.soi-app-row[data-slug="2020-03"] .soi-app-rm')
        ok('save one issue', (await pg.inner_text('.soi-app-stat')).startswith(f'{len(PACKED)+2} of'))
        await pg.click('.soi-app-row[data-slug="2020-03"] .soi-app-rm'); await pg.wait_for_selector('.soi-app-row[data-slug="2020-03"] .soi-app-get'); ok('remove one issue', True)
        t0 = time.time(); await pg.click('.soi-app-all'); await pg.wait_for_function("document.querySelector('.soi-app-all').hidden", timeout=180000)
        s = await pg.inner_text('.soi-app-stat'); ok('save all issues', s.startswith(f'{N} of {N}'), s); print('   (%.0fs)' % (time.time() - t0))
        bad = []
        for w in (320, 390, 768, 1280):
            await pg.set_viewport_size({'width': w, 'height': 800})
            for u in ('/saved.html', '/index.html', f'/issues/{PACKED[-1]}/index.html', '/reader.html?issue=2019-01'):
                await pg.goto(B + u); await pg.wait_for_timeout(700)
                sw = await pg.evaluate("document.documentElement.scrollWidth")
                if sw > w: bad.append((w, u, sw))
        ok('no sideways scroll 320–1280 on 4 pages', not bad, str(bad))
        shots = os.environ.get('SOI_SHOTS')
        if shots:
            for w in (320, 390):
                await pg.set_viewport_size({'width': w, 'height': 760}); await pg.goto(B + '/saved.html'); await pg.wait_for_selector('.soi-app-row'); await pg.wait_for_timeout(400); await pg.screenshot(path=f'{shots}/saved{w}.png')
        await pg.goto(B + f'/issues/{PACKED[-2]}/index.html')
        ok('player audio goes through the app (for lock-screen controls)', await pg.evaluate("window.Audio.soi===true"))
        ok('no script errors', not errs, str(errs[:3]))
        await br.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '-d', ROOT + '/app/www'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try: asyncio.run(main())
finally: srv.terminate()
print(sum(1 for r in res if r[1]), 'of', len(res), 'passed'); sys.exit(0 if all(r[1] for r in res) else 1)
