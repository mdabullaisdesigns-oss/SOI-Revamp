#!/usr/bin/env python3
"""
One-off: cuts the reusable shell out of the approved Issue 133 build
(reference/issue-133-live.html, copied from the live page) so every other issue
is built with exactly the same CSS, player, quiz and go-to-top code.

Writes pipeline/templates/issue-shell.html (with {{TOKENS}}), player.html and
infocus-photo.txt.  Re-run only when the approved design changes.
"""
import re, os
code = open("reference/issue-133-live.html", encoding="utf-8").read()
T = "pipeline/templates"
os.makedirs(T, exist_ok=True)

A = code.index('<div class="soi-ev"', code.index("</style>"))
S1 = code.index("<script>", A)
E = code.rindex("</div>", A, S1) + 6
articles = code[A:E]
open_tag = articles[:articles.index(">") + 1]

# one player, as a template
m = re.search(r'<div class="ev-pl-spot">(<div class="ev-player".*?)</div>\s*<div class="ev-body">', articles, re.S)
player = m.group(1)
player = re.sub(r'data-duration="[^"]*"', 'data-duration="{{DURATION}}"', player, count=1)
player = re.sub(r'(<audio[^>]*\bsrc=")[^"]*(")', r"\1{{AUDIO_URL}}\2", player, count=1)
player = re.sub(r'(<a[^>]*\bhref=")[^"]*\.mp3(")', r"\1{{AUDIO_URL}}\2", player)
player = re.sub(r'download="[^"]*"', 'download="{{AUDIO_FILE}}"', player)
open(f"{T}/player.html", "w", encoding="utf-8").write(player)

photo = re.search(r'<div class="ev-note-person"><img[^>]*src="(data:image/[^"]+)"', articles).group(1)
open(f"{T}/infocus-photo.txt", "w", encoding="utf-8").write(photo)

shell = code[:A] + open_tag + "\n{{ARTICLES}}\n</div>" + code[E:]
shell = re.sub(r"<!-- ===== SPIRIT OF ISLAM · ISSUE 133.*?-->", "{{HEADER_COMMENT}}", shell, count=1, flags=re.S)
n = {}
shell, n["album"] = re.subn(r"album: 'Issue 133 · Nov–Dec 2026'", "album: {{ISSUE_SHORT_JS}}", shell)
shell, n["pill"] = re.subn(r'(<span class="z-pill light">)Issue 133 · Nov–Dec 2026(</span>)', r"\1{{ISSUE_SHORT}}\2", shell)
shell, n["issue"] = re.subn(r"var ISSUE = '[^']*';", "var ISSUE = {{ISSUE_LONG_JS}};", shell)
shell, n["salute"] = re.subn(r"' · Issue 133 reflection complete'", "{{SALUTE_JS}}", shell)
qa = shell.index("var QUESTIONS = [")
qb = shell.index("\n  ];", qa) + 5
shell = shell[:qa] + "var QUESTIONS = {{QUESTIONS}};" + shell[qb:]
n["count"] = len(re.findall(r"Ten short questions", shell))
left = re.findall(r".{30}(?:133|Nov–Dec).{30}", shell)
open(f"{T}/issue-shell.html", "w", encoding="utf-8").write(shell)
print(n, "left-over issue strings:", left, len(shell), len(player), len(photo))
