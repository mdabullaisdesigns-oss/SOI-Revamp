# Batch results (13 Nov 2026)

All **132 issues pass every check** (the 133rd, Nov–Dec 2026 / Issue 133, is the hand-finished reference).
Status for each issue is in `inventory/batch-status.csv`; re-run with `python3 pipeline/batch.py --quick --jobs 2`.

| | |
|---|---|
| PDF issues (Mar 2013 → Jul–Aug 2024, incl. May 2015 = Issue 29) | 119 |
| Gary issues from the WordPress pages (Sep–Oct 2024 → Sep–Oct 2026) | 13 |
| Articles | 2,521 (2,539 with Issue 133) |
| Quizzes | 132 × 10 questions (1,320), sources in `quiz-src/` |
| Quotes in the library | 1,778 |
| Narration still to make (PDF issues) | about 9.6 million characters – **pending** |

## Decisions applied
- CPS feature in Jan 2019, Feb 2019 and Jan 2020 is included as an article, without audio.
- Gary issues: printed text that was missing on the web page was added from the PDF. CPS Newsletter has no audio.
- Small PDF problems (captions, notes, missing words) were fixed through each issue's `overrides.json`. Nothing was left that could not be fixed.
- Duplicates: the four 2023 pairs are word-for-word the same. `SOI-Issue-120-Sep-Oct-2024.pdf` holds the magazine twice; the 52-page `Spirit_of_Islam_Sep-Oct2024.pdf` is used. `January-2022.pdf` is Jan–Feb (Issue 104) and `February-2022.pdf` is Mar–Apr (Issue 105).
- The "We asked ChatGPT about CPS International" page is left out everywhere.

## Gary recordings to make again (18 articles)
The existing recording does not match the article text (a different article was read, or part is missing), or there is none. These articles are shown without a player until re-narrated.

| Issue | Articles |
|---|---|
| Sep–Oct 2024 | Discovery of the Quran · Think, Reflect, and Realize · The Path to Contentment · The Word of God (no recording) |
| Nov–Dec 2024 | Leadership Through Expertise · The Consideration of Circumstances (no recording) |
| Mar–Apr 2025 | The Los Angeles Wildfires |
| May–Jun 2025 | The Essence of Praying · Treasury of Islamic Virtues |
| Nov–Dec 2025 | The Upper Hand of Effort · Your Questions Answered |
| Mar–Apr 2026 | The Path to Paradise · Children's Corner (no recording) |
| May–Jun 2026 | Spiritual Uplift · Eclipse: A Divine Miracle (no recording) |
| Jul–Aug 2026 | In Search of Self · Your Questions Answered · The Word of God |

## Quizzes – worth a read before going live
Every question quotes its article in the explanation and names the article and printed page. Questions are drawn from each article's opening passage, so they are on the easy side, and a few came from short excerpts. A read-through by an editor is advisable.

## Preview
https://soi-preview.pages.dev (Cloudflare Pages, hidden from search engines). It republishes itself on every push that changes `site/` or an issue page.
