#!/usr/bin/env python3
"""Screenshots of every app screen at 375x812 (iPhone) and 412x915 (Android), light and dark.
    python3 app/tests/shots.py [folder]      (default: app/tests/shots/)"""
import asyncio, os, sys
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import B, ROOT, serve, route_all
OUT = sys.argv[1] if len(sys.argv) > 1 else ROOT + '/app/tests/shots'
os.makedirs(OUT, exist_ok=True)
SEED = """localStorage.setItem('soiProgress', JSON.stringify({slug:'2018-07',id:'spiritual-role-of-women',title:'Spiritual Role of Women',label:'Issue 67 · Jul 2018',min:4,frac:.46,off:520,t:192,dur:332,at:Date.now()}));
localStorage.setItem('soiSavedArticles', JSON.stringify([{slug:'2018-07',id:'man-and-god',title:'Man and God',label:'Issue 67 · Jul 2018',min:5,audio:true},{slug:'2026-11',id:'the-universe-as-gift',title:'The Universe as Gift',label:'Issue 133 · Nov–Dec 2026',min:5,audio:true}]));
localStorage.setItem('soiRead', JSON.stringify({'2026-11':{a:1,b:1,c:1,d:1,e:1,f:1,g:1},'2018-07':{a:1,b:1,c:1}}));"""
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for name, w, h, dark in (('375x812', 375, 812, False), ('412x915', 412, 915, False), ('375x812-dark', 375, 812, True), ('412x915-dark', 412, 915, True)):
            ctx = await br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, color_scheme='dark' if dark else 'light', reduced_motion='reduce')
            await route_all(ctx, {'online': True}, [])
            pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            async def shot(n, full=False): await pg.wait_for_timeout(450); await pg.screenshot(path=f'{OUT}/{name}-{n}.png', full_page=full)
            await pg.goto(B + '/index.html'); await pg.evaluate(SEED)
            await pg.goto(B + '/index.html?s=read&issue=2018-07'); await pg.wait_for_selector('.soi-ev .ev-item')
            await pg.evaluate("window.soiApp.offline.save('2018-07', true)"); await pg.wait_for_function("window.soiApp.offline.hasAudio('2018-07')", timeout=60000)
            await pg.evaluate("window.soiApp.mem.toggleQuote({t:'Wisdom is the ability to discover the relevant by sorting out the irrelevant.',s:'2018-07',a:'the-prophet-of-wisdom',at:'The Prophet of Wisdom',n:67,p:'July 2018'})")
            await pg.goto(B + '/index.html'); await pg.wait_for_selector('.soi-app-hero img'); await shot('1-home'); await shot('1-home-full', True)
            await pg.click('.soi-app-cont'); await pg.wait_for_selector('.soi-ev .ev-item.is-open'); await pg.wait_for_timeout(1500); await shot('2-reading-resumed')
            await pg.evaluate("document.querySelector('.soi-ev .ev-item.is-open .ev-pl-play').click()"); await pg.wait_for_timeout(1500); await shot('3-reading-audio')
            await pg.click('[data-back]'); await pg.wait_for_selector('#soi-app-mini:not([hidden])'); await shot('4-home-mini-player')
            await pg.click('#soi-app-tabs [data-tab="search"]'); await shot('5-search')
            await pg.fill('#soi-app-q', 'patience'); await pg.wait_for_selector('.soi-app-res'); await shot('5-search-results')
            await pg.click('#soi-app-tabs [data-tab="saved"]'); await pg.wait_for_selector('.soi-app-irow'); await shot('6-saved-issues')
            await pg.click('[data-act="menu"][data-slug="2018-07"]'); await pg.wait_for_selector('#soi-app-sheet.is-on'); await shot('6-saved-sheet'); await pg.click('#soi-app-sheet .is-cancel'); await pg.wait_for_timeout(350)
            await pg.click('[data-seg="articles"]'); await shot('6-saved-articles'); await pg.click('[data-seg="quotes"]'); await shot('6-saved-quotes')
            await pg.click('#soi-app-tabs [data-tab="profile"]'); await pg.wait_for_selector('.soi-app-rank'); await shot('7-profile'); await shot('7-profile-full', True)
            await pg.click('.soi-app-rank'); await pg.wait_for_selector('#soi-app-board li'); await shot('8-gems'); await shot('8-gems-full', True)
            await pg.evaluate("window.soiApp.player.stop()")
            await pg.goto(B + '/index.html?s=library'); await pg.wait_for_selector('.soi-app-grid3 a'); await shot('9-all-issues')
            await pg.goto(B + '/index.html?s=quotes'); await pg.wait_for_selector('.soi-app-qcard'); await shot('9-quotes')
            await pg.goto(B + '/index.html?s=read&issue=2026-11'); await pg.wait_for_selector('.soi-ev .ev-item'); await shot('2-reading-top')
            print(name, 'errors:', errs[:3])
            await ctx.close()
        await br.close()
srv = serve()
try: asyncio.run(main())
finally: srv.terminate()
