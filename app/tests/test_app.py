#!/usr/bin/env python3
"""Browser test of app/www (the files packed in the app), on a phone-sized screen.
Covers: tabs and screens, reading view, Continue reading (article, place, audio time), the mini player that keeps
playing across screens, offline issues with their audio (progress, storage used, playing with no internet),
search, saved items, sample data, dark mode, large text, screen-reader names, tap-target sizes, no sideways scroll.
The website (app-config.json: remote) is answered from dist/ and audio with a generated sound file.
    python3 site/build_site.py && python3 app/build_app.py && python3 app/tests/test_app.py
NOT tested here (needs a real phone): lock-screen controls, playing with the screen locked, the share sheet,
haptics, the status bar and the splash screen."""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import B, ROOT, serve, route_all
ISS = json.load(open(ROOT + '/dist/issues.json'))['issues']; N = len(ISS); LATEST = ISS[-1]
PACKED = json.load(open(ROOT + '/app/www/assets/app-config.json'))['bundled']
OLD = '2018-07'                                   # an issue that is not packed in the app and has audio
res = []
def ok(name, c, info=''):
    res.append((name, bool(c))); print('PASS' if c else 'FAIL', name, '' if c else info)

NAMES = """() => [...document.querySelectorAll('a[href], button, input, [role=tab]')].filter(e => e.offsetParent !== null && getComputedStyle(e).visibility !== 'hidden' && !e.closest('#soi-app-read-body'))
  .filter(e => !((e.getAttribute('aria-label') || '').trim() || (e.textContent || '').trim() || e.getAttribute('aria-labelledby') || e.placeholder)).map(e => e.outerHTML.slice(0, 90))"""
SMALL = """() => [...document.querySelectorAll('a[href], button')].filter(e => e.offsetParent !== null && getComputedStyle(e).visibility !== 'hidden' && !e.closest('#soi-app-read-body') && !e.closest('.soi-app-res') && !e.closest('figcaption') && !e.closest('.soi-app-quote-src') && !e.classList.contains('soi-app-skip'))
  .map(e => [e, e.getBoundingClientRect()]).filter(x => x[1].width > 0 && (x[1].height < 43.5 || x[1].width < 43.5) && !(x[0].closest('.soi-app-irow-t') || x[0].closest('.soi-app-hrow')))
  .map(x => Math.round(x[1].width) + 'x' + Math.round(x[1].height) + ' ' + x[0].outerHTML.slice(0, 70))"""

async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = await br.new_context(viewport={'width': 375, 'height': 812}, reduced_motion='no-preference' if os.environ.get('SOI_MOTION') else 'reduce')
        st = {'online': True}; ext = []; errs = []
        await route_all(ctx, st, ext)
        pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        go = lambda s: pg.goto(B + '/index.html' + s)
        J = pg.evaluate
        async def tab(t): await pg.click(f'#soi-app-tabs [data-tab="{t}"]'); await pg.wait_for_timeout(250)

        # ---------- home ----------
        await go(''); await pg.wait_for_selector('.soi-app-hero img'); await pg.wait_for_timeout(500)
        ok('one page, four tabs, Home current', await pg.locator('#soi-app-tabs a').count() == 4 and (await pg.inner_text('#soi-app-tabs a[aria-current="page"]')).strip() == 'Home')
        ok('home: latest issue with Read / Listen / Save', f"ISSUE {LATEST['number']}" in (await pg.inner_text('.soi-app-hero')).upper() and await pg.locator('.soi-app-hero-btns a').count() == 2 and await pg.locator('.soi-app-hero [data-save]').count() == 1)
        ok('home: the three newest covers', await pg.locator('#soi-app-newest a img').count() == 3 and await J("[...document.querySelectorAll('#soi-app-newest img')].every(i => i.complete && i.naturalWidth > 200)"))
        ok('home: no Continue card before anything is read', await pg.locator('.soi-app-cont').count() == 0)
        ok('home: tutorial placeholders without photos', await pg.locator('.soi-app-guide').count() >= 3 and await pg.locator('.soi-app-guide img').count() == 0 and 'coming soon' in (await pg.inner_text('#soi-app-guides')).lower())
        ok('home: quote of the day', len(await pg.inner_text('#soi-app-qotd blockquote')) > 20)
        ok('nothing fetched from outside except the issue list', all(u.endswith('/issues.json') for u in ext), str(ext[:3]))
        ok('fonts packed in the app', await J("Promise.all([document.fonts.load('700 20px \"Cita Pro\"'), document.fonts.load('16px \"Plus Jakarta Sans\"')]).then(r => r.every(f => f.length > 0))"))
        ok('safe areas: page allows drawing under the notch, bars pad for it', 'viewport-fit=cover' in await J("document.querySelector('meta[name=viewport]').content") and 'safe-area-inset-bottom' in open(ROOT + '/app/www/assets/app.css').read())

        # ---------- reading view (an issue packed in the app) ----------
        await pg.click('.soi-app-hero-btns a >> nth=0'); await pg.wait_for_selector('.soi-ev .ev-item'); await pg.wait_for_timeout(500)
        ok('reading view: full screen with a slim bar (back, issue, share)', await pg.locator('#soi-app-read-nav [data-back]').is_visible() and await pg.locator('#soi-app-read-nav [data-share]').is_visible()
           and f"Issue {LATEST['number']}" in await pg.inner_text('#soi-app-read-title') and not await pg.locator('#soi-app-tabs').is_visible())
        ok('  the whole magazine: articles, Save / Share on each, quiz', await pg.locator('.soi-ev .ev-item').count() == LATEST['articles'] and await pg.locator('.soi-ev .soi-acts').count() == await pg.locator('.soi-ev .ev-item .ev-meta').count() > 5 and await pg.locator('#soi-quiz').count() == 1)
        await pg.click('#soi-app-read-nav [data-back]'); await pg.wait_for_timeout(300)
        ok('  Back returns to Home with the tabs', await J("document.body.dataset.screen") == 'home' and await pg.locator('#soi-app-tabs').is_visible())

        # ---------- an older issue: fetched once, audio, mini player ----------
        await pg.click('.soi-app-hrow a'); await pg.wait_for_selector('.soi-app-grid3 a')
        await pg.click('[data-year="2018"]'); await pg.click(f'.soi-app-grid3 a[href="/issues/{OLD}/"]'); await pg.wait_for_selector('.soi-ev .ev-item', timeout=10000)
        ok('older issue fetched once and shown', await J("document.body.dataset.screen") == 'read' and await J(f"window.soiApp.offline.hasText('{OLD}')"))
        await J("document.querySelectorAll('.soi-ev .ev-item')[1].querySelector('.ev-tab').click()"); await pg.wait_for_timeout(1200)
        aid = await J("document.querySelectorAll('.soi-ev .ev-item')[1].id")
        await pg.mouse.wheel(0, 700); await pg.wait_for_timeout(1500); await pg.mouse.wheel(0, 250); await pg.wait_for_timeout(1500)
        await pg.click('.soi-ev .ev-item.is-open .soi-act-save')
        await pg.click('.soi-ev .ev-item.is-open .ev-pl-play'); await pg.wait_for_timeout(2600)
        s1 = await J("window.soiApp.player.state()")
        ok('audio plays in the reading view', s1 and s1['playing'] and s1['t'] > 1, str(s1))
        y0 = await J('scrollY')
        ok('  mini player stays hidden while reading that article', not await pg.locator('#soi-app-mini').is_visible())
        await pg.click('#soi-app-read-nav [data-back]'); await pg.wait_for_selector('#soi-app-mini:not([hidden])'); await pg.wait_for_timeout(300)
        await tab('home'); await pg.wait_for_timeout(1300)
        s2 = await J("window.soiApp.player.state()")
        ok('mini player: audio keeps playing on Home', await pg.locator('#soi-app-mini').is_visible() and s2['playing'] and s2['t'] > s1['t'] + 1 and s2['title'] in await pg.inner_text('#soi-app-mini'), str(s2))
        await tab('search'); await tab('saved'); await tab('profile'); await pg.wait_for_timeout(900)
        s3 = await J("window.soiApp.player.state()")
        ok('  and across Search, Saved and Profile', s3['playing'] and s3['t'] > s2['t'] + 1 and await pg.locator('#soi-app-mini').is_visible())
        ok('  the hidden reading view does not scroll the screen you are on', await J('scrollY') < 5)
        await pg.click('#soi-app-mini [data-mini="toggle"]'); await pg.wait_for_timeout(400)
        s4 = await J("window.soiApp.player.state()")
        ok('  pause from the mini player', not s4['playing'] and await pg.get_attribute('#soi-app-mini [data-mini="toggle"]', 'aria-label') == 'Play')
        await pg.click('#soi-app-mini .soi-app-mini-open'); await pg.wait_for_timeout(1300)
        ok('  tapping it reopens the article', await J("document.body.dataset.screen") == 'read' and await J("(document.querySelector('.soi-ev .ev-item.is-open')||{}).id") == aid)
        prog = json.loads(await J("localStorage.getItem('soiProgress')") or '{}')
        ok('reading place remembered: article, position, audio time', prog.get('slug') == OLD and 'soi-' + prog.get('id', '') == aid and prog.get('t', 0) >= 3 and prog.get('frac', 0) > 0, str(prog))

        # ---------- Continue reading, with no internet, after closing the app ----------
        st['online'] = False
        await go(''); await pg.wait_for_selector('.soi-app-cont')
        t = await pg.inner_text('.soi-app-cont')
        ok('OFFLINE home: Continue reading card with the audio time', prog['title'] in t and 'paused at' in t, t)
        await pg.click('.soi-app-cont'); await pg.wait_for_selector('.soi-ev .ev-item.is-open'); await pg.wait_for_timeout(1900)
        op = await J("(document.querySelector('.soi-ev .ev-item.is-open')||{}).id"); off = await J("Math.round(-document.querySelector('.soi-ev .ev-item.is-open').getBoundingClientRect().top)")
        ok('OFFLINE: resumes the same article at the same place', op == aid and abs(off - prog['off']) < 80, f'{op} place {prog["off"]} -> {off}')
        st['online'] = True
        await pg.click('.soi-ev .ev-item.is-open .ev-pl-play'); await pg.wait_for_timeout(1500)
        s5 = await J("window.soiApp.player.state()")
        ok('  and the audio continues from where it was paused', s5 and prog['t'] - 1 <= s5['t'] <= prog['t'] + 6, f"{prog['t']} -> {s5 and s5['t']}")
        await J("window.soiApp.player.stop()")

        # ---------- offline: the issue together with its audio ----------
        st['audio_delay'] = 0.3
        await pg.click('#soi-app-read-head [data-offline]'); await pg.wait_for_selector('#soi-app-sheet.is-on')
        ok('Save for offline offers the audio', 'Text and audio' in await pg.inner_text('#soi-app-sheet'))
        await pg.click('#soi-app-sheet button.is-main')
        await pg.wait_for_function(f"!!window.soiApp.offline.job('{OLD}')", timeout=5000)
        await pg.click('#soi-app-read-nav [data-back]'); await tab('saved'); await pg.wait_for_selector(f'.soi-app-irow [data-slug="{OLD}"]')
        row = pg.locator('.soi-app-irow', has=pg.locator(f'[data-slug="{OLD}"]'))
        seen = ''
        for _ in range(40):
            seen = await row.inner_text()
            if 'Saving audio' in seen: break
            await pg.wait_for_timeout(100)
        ok('Saved shows the download progress', 'Saving audio' in seen and await row.locator('[role=progressbar]').count() == 1, seen)
        await pg.wait_for_function(f"window.soiApp.offline.hasAudio('{OLD}')", timeout=90000); await pg.wait_for_timeout(500)
        st['audio_delay'] = 0
        used = await J("window.soiApp.offline.used()"); n_audio = [i for i in ISS if i['slug'] == OLD][0]['audio']
        ok('  all recordings saved, storage used is shown', used['audio'] > 1e6 and 'Text and audio' in await row.inner_text() and 'Audio' in await pg.inner_text('.soi-app-storage') and (await J(f"window.soiApp.offline.index()['{OLD}'].have")) == n_audio, str(used))
        st['online'] = False; n_before = len(ext)
        await go(f'?s=read&issue={OLD}'); await pg.wait_for_selector('.soi-ev .ev-item')
        await J("document.querySelectorAll('.soi-ev .ev-item')[2].querySelector('.ev-tab').click()"); await pg.wait_for_timeout(1200)
        await pg.click('.soi-ev .ev-item.is-open .ev-pl-play'); await pg.wait_for_timeout(2200)
        s6 = await J("window.soiApp.player.state()")
        ok('OFFLINE: saved audio plays with no internet', s6 and s6['playing'] and s6['t'] > 1 and not [u for u in ext[n_before:] if '/media/' in u or u.endswith('.mp3')], str(s6))
        await J("window.soiApp.player.stop()")
        await go('?s=read&issue=2014-05'); await pg.wait_for_selector('.soi-app-empty')
        ok('OFFLINE: an issue that was never opened gives a clear message', 'not on your phone yet' in await pg.inner_text('#soi-app-read-state'))

        # ---------- search ----------
        await go('?s=search'); await pg.fill('#soi-app-q', 'patience'); await pg.wait_for_selector('.soi-app-res', timeout=10000)
        href = await pg.get_attribute('.soi-app-res', 'href')
        ok('OFFLINE: search works', '/issues/' in href and await pg.locator('.soi-app-res').count() > 5)
        await pg.fill('#soi-app-q', '51 : 56'); await pg.wait_for_timeout(1200)
        ok('OFFLINE: search by Quran reference', await pg.locator('.soi-app-res').count() > 3 and '51:56' in await pg.inner_text('#soi-app-results'))
        st['online'] = True
        await pg.click('.soi-app-res >> nth=0'); await pg.wait_for_selector('.soi-ev .ev-item.is-open', timeout=10000)
        ok('  a result opens that article in the reading view', await J("document.body.dataset.screen") == 'read')
        await pg.go_back(); await pg.wait_for_timeout(400)
        ok('  Back returns to the results', await J("document.body.dataset.screen") == 'search' and await pg.locator('.soi-app-res').count() > 3)

        # ---------- saved ----------
        await go('?s=quotes'); await pg.wait_for_selector('.soi-app-qcard'); await pg.click('.soi-app-qcard >> nth=1 >> [data-act="save"]')
        await go('?s=saved'); await pg.wait_for_selector('.soi-app-irow')
        ok('saved: issues on this phone', await pg.locator('.soi-app-irow').count() >= len(PACKED) + 1)
        await pg.click('[data-seg="articles"]'); ok('saved: the saved article', await pg.locator('.soi-app-acard').count() == 1)
        await pg.click('[data-seg="quotes"]'); ok('saved: the saved quote', await pg.locator('.soi-app-qcard').count() == 1)
        await pg.click('[data-seg="issues"]'); await pg.click(f'[data-act="menu"][data-slug="{OLD}"]'); await pg.wait_for_selector('#soi-app-sheet.is-on')
        await pg.click('#soi-app-sheet button:has-text("Remove the audio")'); await pg.wait_for_function(f"!window.soiApp.offline.hasAudio('{OLD}')")
        ok('saved: remove the audio, keep the text', await J(f"window.soiApp.offline.hasText('{OLD}')") and (await J("window.soiApp.offline.used()"))['audio'] == 0)
        await pg.wait_for_timeout(500); await pg.click(f'[data-act="menu"][data-slug="{OLD}"]'); await pg.wait_for_selector('#soi-app-sheet.is-on')
        await pg.click('#soi-app-sheet button:has-text("Remove from this phone")'); await pg.wait_for_function(f"!window.soiApp.offline.hasText('{OLD}')")
        ok('saved: remove the issue', True)

        # ---------- profile, gems ----------
        await go('?s=profile'); await pg.wait_for_selector('.soi-app-rank')
        ok('profile: sample data marked as sample', await pg.locator('.soi-app-sample').count() >= 2 and await pg.locator('.soi-app-cal span').count() == 14)
        await pg.click('[data-theme="dark"]'); dark = await J("document.documentElement.classList.contains('soi-app-dark') && getComputedStyle(document.body).backgroundColor")
        ok('dark mode from Profile', dark == 'rgb(13, 29, 36)', str(dark))
        await pg.click('[data-theme="system"]'); await pg.emulate_media(color_scheme='dark'); await pg.wait_for_timeout(200)
        ok('dark mode follows the phone', await J("document.documentElement.classList.contains('soi-app-dark')"))
        await pg.emulate_media(color_scheme='light'); await pg.wait_for_timeout(200)
        f0 = await J("parseFloat(getComputedStyle(document.documentElement).fontSize)"); await pg.click('[data-text="1.3"]'); f1 = await J("parseFloat(getComputedStyle(document.documentElement).fontSize)")
        ok('text size setting enlarges the text', f1 > f0 * 1.25, f'{f0} -> {f1}')
        await pg.click('.soi-app-rank'); await pg.wait_for_selector('#soi-app-board li')
        a = await pg.inner_text('#soi-app-board'); await pg.click('[data-seg="all-time"]'); b = await pg.inner_text('#soi-app-board')
        ok('gems: leaderboard switches, marked sample and proposed', a != b and await pg.locator('.soi-app-view-gems .soi-app-sample').count() == 1 and 'PROPOSED' in (await pg.inner_text('.soi-app-earn')).upper())

        # ---------- every screen: large text, small and large phones, names, tap targets ----------
        screens = ['', '?s=search', '?s=saved', '?s=saved&tab=articles', '?s=saved&tab=quotes', '?s=profile', '?s=gems', '?s=library', '?s=quotes', f'?s=read&issue={PACKED[-1]}', f'?s=read&issue={OLD}']
        bad = []; unnamed = []; small = []
        for scale in ('1.3', '1'):
            await J(f"window.soiApp.setPref('text', {scale})")
            for w, h in ((320, 640), (375, 812), (412, 915), (768, 1024)):
                await pg.set_viewport_size({'width': w, 'height': h})
                for u in screens:
                    await go(u); await pg.wait_for_timeout(450)
                    sw = await J("document.documentElement.scrollWidth")
                    if sw > w: bad.append((scale, w, u, sw))
                    if scale == '1' and w == 375:
                        unnamed += [u + ' ' + x for x in await J(NAMES)]; small += [u + ' ' + x for x in await J(SMALL)]
        ok(f'no sideways scroll on {len(screens)} screens at 320 / 375 / 412 / 768, normal and large text', not bad, str(bad[:6]))
        ok('every button and link has a name for VoiceOver / TalkBack', not unnamed, str(unnamed[:5]))
        ok('tap targets are at least 44 px', not small, str(small[:6]))
        await pg.set_viewport_size({'width': 375, 'height': 812}); await go('')
        ok('images describe themselves or are marked decorative', await J("[...document.querySelectorAll('img')].every(i => i.hasAttribute('alt'))"))
        ok('screens are announced: main landmark, labelled tabs and regions', await J("!!document.querySelector('main') && !!document.querySelector('nav[aria-label]') && !!document.querySelector('#soi-app-toast[aria-live]') && [...document.querySelectorAll('.soi-app-view')].every(v => v.getAttribute('aria-label'))"))
        ok('no script errors', not errs, str(errs[:3]))
        await br.close()

srv = serve()
try: asyncio.run(main())
finally: srv.terminate()
print(sum(1 for r in res if r[1]), 'of', len(res), 'passed'); sys.exit(0 if all(r[1] for r in res) else 1)
