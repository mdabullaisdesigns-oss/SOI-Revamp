#!/usr/bin/env python3
"""App icon and splash screen, made only from the logo files in site/brand/ on the approved teal.
    python3 app/make_brand_assets.py && (cd app && npx @capacitor/assets generate --assetPath resources --android --ios)
Writes app/resources/{icon-only,icon-foreground,icon-background,splash,splash-dark}.png; the second command
turns them into every size Android and iOS need."""
import asyncio, base64, os
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); BRAND = os.path.join(os.path.dirname(HERE), "site", "brand"); OUT = os.path.join(HERE, "resources")
def uri(name):
    mime = "image/svg+xml" if name.endswith(".svg") else "image/png"
    return f"data:{mime};base64," + base64.b64encode(open(os.path.join(BRAND, name), "rb").read()).decode()
BG = "radial-gradient(120% 120% at 30% 20%, #2B6076 0%, #204E60 45%, #173A48 100%)"
def page(w, h, body, bg):
    return f'<html><body style="margin:0;width:{w}px;height:{h}px;background:{bg};display:flex;align-items:center;justify-content:center;flex-direction:column;overflow:hidden">{body}</body></html>'
async def main():
    os.makedirs(OUT, exist_ok=True)
    bird, logo, slogan = uri("Peogen-logo.png"), uri("Spirit-of-Islam-Logo.png"), uri("Slogan-Line.png")
    splash = f'<img src="{bird}" style="width:420px"><img src="{logo}" style="width:1000px;margin-top:90px"><img src="{slogan}" style="width:940px;margin-top:34px">'
    jobs = [("icon-only.png", 1024, 1024, f'<img src="{bird}" style="width:640px">', BG, False),
            ("icon-foreground.png", 1024, 1024, f'<img src="{bird}" style="width:470px">', "transparent", True),     # Android adaptive icon: art inside the safe circle
            ("icon-background.png", 1024, 1024, "", BG, False),
            ("splash.png", 2732, 2732, splash, BG, False), ("splash-dark.png", 2732, 2732, splash, "radial-gradient(120% 120% at 30% 20%, #1C4353 0%, #132F3B 50%, #0D1D24 100%)", False)]
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for name, w, h, body, bg, clear in jobs:
            pg = await br.new_page(viewport={"width": w, "height": h})
            await pg.set_content(page(w, h, body, bg)); await pg.wait_for_timeout(300)
            await pg.screenshot(path=os.path.join(OUT, name), omit_background=clear); await pg.close()
        await br.close()
    print("written:", ", ".join(j[0] for j in jobs))
asyncio.run(main())
