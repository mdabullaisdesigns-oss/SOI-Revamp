#!/usr/bin/env python3
"""Turn the <text>Magazine</text> in site/brand/soi-mark-white.svg into outlines
drawn with Cabinet Grotesk (Fontshare, ITF Free Font Licence), so the logo looks
the same everywhere, even where the font is not installed.

Usage: python3 scripts/outline_logo_text.py <font file (.woff2/.ttf/.otf)> [svg]
"""
import re, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

font_path = sys.argv[1]
svg_path = sys.argv[2] if len(sys.argv) > 2 else "site/brand/soi-mark-white.svg"
svg = open(svg_path, encoding="utf-8").read()
m = re.search(r'<text([^>]*)>([^<]*)</text>', svg)
if not m:
    sys.exit("no <text> left in " + svg_path)
attrs, word = m.group(1), m.group(2)
num = lambda k: float(re.search(k + r'="([\d.]+)"', attrs).group(1))
x, y, size = num("x"), num("y"), num("font-size")
vb_w = float(svg.split('viewBox="')[1].split()[2])

f = TTFont(font_path)
gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
upm = f["head"].unitsPerEm
s = size / upm
names = [cmap[ord(c)] for c in word]
width = sum(hmtx[n][0] for n in names) * s
sx = min(1.0, (vb_w - x - 0.2) / width)          # never wider than the logo's box
pen = SVGPathPen(gs)
adv = 0
for n in names:
    gs[n].draw(TransformPen(pen, (s * sx, 0, 0, -s, x + adv * s * sx, y)))
    adv += hmtx[n][0]
d = pen.getCommands()
svg = svg.replace(m.group(0), f'<path d="{d}"/>')
open(svg_path, "w", encoding="utf-8").write(svg)
print(f"'{word}' outlined: {width:.2f} units wide, horizontal scale {sx:.3f}")
