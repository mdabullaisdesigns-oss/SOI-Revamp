# Issue pipeline

One issue = one folder `issues/<slug>/` (slug = `YYYY-MM`, first month of the issue).

| Stage | Command | Where | Output |
|---|---|---|---|
| 1 extract | add a line to `sources/request.txt` (runs the "Extract issue text" workflow) | GitHub Actions (PDF read from R2, never in git) | `raw/pages.json`, `raw/pdftotext.txt`, `raw/meta.json` |
| 2 structure | `python3 pipeline/structure.py <slug>` | anywhere | `issue.json` – articles rebuilt from the magazine's typography; every word comes from the PDF |
| 3 check | `python3 pipeline/check.py <slug>` | anywhere | `check.json`, `review.md` – word match per article (flag < 99%), list of everything left out, any PDF text that is in no article |
| – quiz | written by Claude from `issue.json` | session | `quiz.json` – 10 questions, articles only |
| 4 narration | `python3 pipeline/narrate.py prepare <slug>` | anywhere | `narration.json` – exact sentences to speak, character counts. All "pending" until the Gary/TTSMaker key exists; then MP3s + timings go in `audio.json` |
| 5 build | `python3 pipeline/build.py <slug> --preview` | anywhere | `SOI-<slug>-complete.html` (the one Divi Code-module block, built from the approved Issue 133 shell) and `preview.html` (mock Divi page, not committed) |
| 6 test | `python3 pipeline/test_page.py <slug>` | anywhere with Chrome | `test.json` – 1280/768/390/320px: every tab opens alone at the top, no sideways scroll, no script errors, quiz completes, go-to-top |

## Corrections
`issues/<slug>/overrides.json` forces the role of a PDF block when the typography rules get it wrong
(block ids are shown by `python3 pipeline/dump.py <slug> <page>`; result by `python3 pipeline/show.py <slug> <article no>`).
Re-run stages 2–6 afterwards.

## Rules the pipeline keeps
- Nothing is dropped silently: `review.md` lists every block that is not in an article, for the owner to confirm.
- The "We asked ChatGPT about CPS International" page is never included.
- Issues with Gary audio (Sep-Oct 2024 → Sep-Oct 2026) take their text from the WordPress page (`sources/pages.txt`), not from the PDF. Not built yet – see `docs/pilot-results.md`.
