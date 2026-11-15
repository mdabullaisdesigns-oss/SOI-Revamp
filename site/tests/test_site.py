#!/usr/bin/env python3
"""Browser test of the built website (dist/) against the approved redesign.
    python3 site/build_site.py && python3 site/tests/test_site.py"""
import asyncio, html, json, os, re, subprocess, sys, time
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ISS = json.load(open(ROOT + '/dist/issues.json'))['issues']; LATEST = ISS[-1]
B = 'http://localhost:8764'; res = []
def ok(name, c, info=''):
    res.append((name, bool(c))); print('PASS' if c else 'FAIL', name, info if not c else '')
def words(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(); ctx = await br.new_context(viewport={'width': 1440, 'height': 900}); errs = []
        await ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(B) else r.abort())
        pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(B + '/'); await pg.wait_for_timeout(800)
        ok('header: pigeon, logo, slogan on the gradient with the world map', await pg.locator('.soi-hdr img').count() == 3 and 'World-map.svg' in await pg.evaluate("getComputedStyle(document.querySelector('.soi-hdr')).backgroundImage")
           and await pg.evaluate("[...document.querySelectorAll('.soi-hdr img')].every(i=>i.complete&&i.naturalWidth>0)"))
        items = [re.sub(r'\s*▾', '', t).strip() for t in await pg.locator('.soi-menu-list > li > a, .soi-menu-list > li > .soi-menu-top').all_inner_texts()]
        ok('menu items as approved', items == ['Home', 'Archives', 'Quotes', 'About Us', 'Contact Us'], str(items))
        ok('menu: gold bar across the full width, joined to the header, Search / Saved / Sign in on the right', await pg.evaluate("(()=>{const b=document.querySelector('.soi-menubar'),h=document.querySelector('.soi-hdr');return getComputedStyle(b).backgroundColor==='rgb(212, 204, 115)'&&b.offsetWidth===document.documentElement.clientWidth&&Math.abs(b.getBoundingClientRect().top-h.getBoundingClientRect().bottom)<1})()")
           and await pg.locator('.soi-menu-right a').count() == 3)
        # welcome note, word for word against the live home page
        live = open(ROOT + '/sources/site/home.html', encoding='utf-8').read()
        a = live.find('Dear Readers'); lw = words(live[a:live.find('Team Spirit of Islam', a) + 20])
        mine = words(await pg.inner_html('.soi-welcome-text')); mine = re.sub(r'^(.*?:) ', r'\1 ', mine)
        norm = lambda s: re.sub(r'\b\d\. ', '', re.sub(r'\s+', ' ', s.replace(' ,', ',').replace(' :', ':'))).strip()
        ok('welcome note is word for word the live text', norm(lw) == norm(mine), '\n' + norm(lw)[:300] + '\n' + norm(mine)[:300])
        ok('welcome heading', 'Welcome to Spirit of Islam' in await pg.inner_text('.soi-welcome h1') and 'A Magazine for the Journey of Life' in await pg.inner_text('.soi-welcome-sub'))
        heads = await pg.locator('main h2.soi-h, .soi-getapp h2').all_inner_texts()
        ok('home sections in the approved order', [h.split('\n')[0] for h in heads][:4] == ['Our latest issue', 'Latest issues', 'New here? Start with these', 'Read by topic'] and len(heads) == 5, str(heads))
        ok('latest issue hero + Continue + Quote of the day', f"ISSUE {LATEST['number']}" in (await pg.inner_text('.soi-hero-over')).upper() and len(await pg.inner_text('.soi-qotd-text')) > 20 and await pg.locator('#soi-continue').count() == 1)
        ok('latest issues row: 6 covers', await pg.locator('.soi-home .soi-covers-6 .soi-icard .soi-cover > img').count() == 6)
        ok('footer: credit, CPS social links, Ask AI, no copyright line', 'Md Abullais' in await pg.inner_text('.soi-credit') and await pg.locator('.soi-credit-click').count() == 1 and await pg.locator('.soi-soc a').count() >= 6 and await pg.locator('.soi-ask-ai a.soi-ai').count() == 5 and '©' not in await pg.inner_text('.soi-foot2'))
        # Archives menu
        await pg.hover('.soi-has-mega > .soi-menu-top'); await pg.wait_for_selector('.soi-mega-covers a'); await pg.wait_for_timeout(500)
        ok('Archives menu: every year on the left, covers on the right', await pg.locator('.soi-mega-years button').count() == len({i['year'] for i in ISS}) and await pg.locator('.soi-mega-covers a').count() == len([i for i in ISS if i['year'] == LATEST['year']]))
        await pg.hover('.soi-mega-years button[data-y="2018"]'); await pg.wait_for_timeout(1200)
        ok('  hovering a year shows that year\'s covers', await pg.locator('.soi-mega-covers a').count() == 12 and await pg.evaluate("[...document.querySelectorAll('.soi-mega-covers img')].every(i=>i.complete&&i.naturalWidth>0)"))
        await pg.mouse.move(700, 880)
        ok('About Us is one link, no drop-down', await pg.locator('.soi-menu-list > li:nth-child(4) > a[href="/about/"]').count() == 1 and await pg.locator('.soi-menu-list > li:nth-child(4) .soi-sub').count() == 0)
        await pg.mouse.wheel(0, 1500); await pg.wait_for_timeout(300)
        ok('menu bar stays on screen when scrolling (sticky)', await pg.evaluate("document.querySelector('.soi-menu').getBoundingClientRect().top") < 40)
        # every issue has a cover file; archive shows them
        missing = [i['slug'] for i in ISS if not os.path.exists(ROOT + f"/dist/assets/covers/{i['slug']}.webp")]
        ok(f'cover picture for all {len(ISS)} issues', not missing, str(missing))
        await pg.goto(B + '/archive/'); ok('archive: a cover card for every issue', await pg.locator('.soi-icard .soi-cover > img').count() == len(ISS))
        await pg.click('.soi-view [data-view=list]'); ok('archive: list view', await pg.evaluate("document.querySelector('.soi-arch').dataset.view==='list'") and await pg.locator('.soi-icard-more').first.is_visible())
        # issue page
        await pg.goto(B + '/issues/2019-03/'); await pg.wait_for_selector('.soi-ev .ev-item')
        order = await pg.evaluate("['.soi-hdr','.soi-menubar','.soi-auto-banner','.soi-ev'].map(s=>document.querySelector(s).getBoundingClientRect().top+scrollY)")
        ok('issue page: header, menu, archive banner, then the magazine', order == sorted(order) and 'The Journey of Life' in await pg.inner_text('.soi-auto-banner'), str(order))
        ok('issue page: Save / Share on articles, quiz present', await pg.locator('.soi-ev .soi-acts').count() > 5 and await pg.locator('#soi-quiz').count() == 1)
        await pg.evaluate("document.querySelectorAll('.soi-ev .ev-item')[3].querySelector('.ev-tab').click()"); await pg.wait_for_timeout(900)
        await pg.mouse.wheel(0, 700); await pg.wait_for_timeout(1700); await pg.mouse.wheel(0, 200); await pg.wait_for_timeout(1700)
        await pg.evaluate("document.querySelector('.soi-ev .ev-item.is-open .soi-act-save').click()")
        await pg.goto(B + '/'); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#soi-continue'); ok('home: Continue reading shows the article just read', 'CONTINUE READING' in t.upper() and 'Resume' in t, t[:80])
        await pg.click('.soi-cont-go'); await pg.wait_for_selector('.soi-ev .ev-item.is-open', timeout=5000); ok('  Resume opens that article', 'resume=1' in pg.url)
        await pg.goto(B + '/saved/'); ok('saved page lists the saved article', await pg.locator('#soi-saved-web .soi-saved-row').count() >= 2)
        for u, t in (('/about/', 'Maulana Wahiduddin Khan'), ('/about/', 'The SOI Team'), ('/contact/', 'Contact Us'), ('/signin/', 'Sign in'), ('/search/', 'Search'), ('/quotes/', 'Words to carry with you')):
            await pg.goto(B + u); ok(f'page {u}', t in await pg.inner_text('main'))
        # phones
        m = await ctx.new_page(); await m.set_viewport_size({'width': 390, 'height': 800}); m.on('pageerror', lambda e: errs.append(str(e)))
        await m.goto(B + '/'); await m.click('.soi-menu-toggle'); await m.click('.soi-has-mega > .soi-menu-top'); await m.wait_for_selector('.soi-mega-years button')
        ok('phone: menu opens, Archives lists the years', await m.locator('.soi-mega-years button').count() >= 14 and await m.locator('.soi-menu-list').is_visible())
        bad = []
        pages = ('/', '/archive/', '/issues/' + LATEST['slug'] + '/', '/issues/2013-01/', '/about/', '/quotes/', '/search/', '/saved/', '/contact/')
        for w in (320, 360, 390, 768, 981, 1100, 1280):
            await m.set_viewport_size({'width': w, 'height': 800})
            for u in pages:
                await m.goto(B + u); await m.wait_for_timeout(350)
                sw = await m.evaluate("document.documentElement.scrollWidth")
                if sw > w: bad.append((w, u, sw))
            if w < 981:
                await m.goto(B + '/'); await m.click('.soi-menu-toggle'); await m.wait_for_timeout(200)
                sw = await m.evaluate("document.documentElement.scrollWidth")
                if sw > w: bad.append((w, 'menu open', sw))
        ok(f'no sideways scroll 320–1280 on {len(pages)} pages', not bad, str(bad))
        ok('no script errors', not errs, str(errs[:3]))
        await br.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8764', '-d', ROOT + '/dist'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try: asyncio.run(main())
finally: srv.terminate()
print(sum(1 for r in res if r[1]), 'of', len(res), 'passed'); sys.exit(0 if all(r[1] for r in res) else 1)
