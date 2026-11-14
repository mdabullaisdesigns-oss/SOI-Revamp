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

## Quizzes (rewritten 14 Nov 2026 from the full text of each article)
132 issues × 10 questions. Each quiz draws on 6–10 different articles, mixes recall with "what does the article mean / how would you apply it" questions, and every explanation quotes the article and gives its title and printed page. All 132 issue pages were rebuilt and pass the checks.

**Choices made – change if you disagree**
- No quiz question (the articles themselves are on the site in full) on four articles that take a position on a current political dispute or make a dated prediction: "Peace in the Promised Land" (Jan–Feb 2024), "Steps Towards Shared Global Prosperity" (Jan–Feb 2025), "Blueprint for Lasting Peace in Palestine" (Nov–Dec 2025), "The Divine Warning of Doomsday" (Jan–Feb 2026, says most life may end by 2050).
- No questions on book reviews, readers' notices, CPS Newsletter, glossary or contents pages.
- Where an article contains a factual slip, no question was built on it: Apollo 8 dated 1985 in "Staying Cool"; the Iran Air incident dated 3 June 1988 (it was 3 July); differing neuron counts.

**Text oddities noticed in the Gary issues (text is as on the WordPress pages; not changed)**
| Issue | Article | What looks wrong |
|---|---|---|
| Nov–Dec 2024 | The Destructive Force of Hatred | body is about individual talents (Abu Hurairah / Khalid), not hatred |
| Jan–Feb 2025 | The Power of Quality in Today's World | body is about positive thinking |
| Nov–Dec 2025 | Blueprint for Lasting Peace in Palestine | starts with a stray subheading "Hard Work Builds Dignity" |
| Jul–Aug 2026 | The Power of Trust | ends with a paragraph that belongs to "Super Performers" |
| Jul–Aug 2026 | Beyond Mere Appearance | closing passage appears twice |

## App (foundation, 14 Nov 2026)
`app/` – Capacitor shell for Android and iOS; see `app/README.md`. Offline reading, saved issues and search are tested in a browser; background audio is wired but needs a real phone to confirm.

## Preview
https://soi-preview.pages.dev (Cloudflare Pages, hidden from search engines). It republishes itself on every push that changes `site/` or an issue page.
