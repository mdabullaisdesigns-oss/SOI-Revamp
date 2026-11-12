# Pilot results (12 Nov 2026)

Three issues taken through all stages except narration (waiting for the Gary/TTSMaker key).

| Issue | PDF | Articles | Words | Word match | Flagged | Browser test (4 widths) | To narrate |
|---|---|---|---|---|---|---|---|
| March 2013 (Issue 3) | `March-2013.pdf` | 18 | 14,047 | 99.91% | 0 | pass | 76,503 characters |
| June 2018 (Issue 66) | `June-2018.pdf` | 17 | 15,690 | 99.91% | 0 | pass | 85,933 characters |
| Sep-Oct 2023 (Issue 114) | `SOI-Sept-Oct-2023.pdf` | 26 | 14,296 | 99.90% | 0 | pass | 80,374 characters |

Each has a 10-question quiz (articles only; every source quotation checked against the article text).
The unmatched words are drop-cap openings and line-end hyphens, listed in each `review.md`.

## What the pilots showed
- **No issue is scanned.** Survey of all 139 PDFs (`inventory/pdf-survey.csv`): every one has a text layer (at most 2 picture-only pages, i.e. covers/adverts). OCR is not needed; as a safeguard, OCR of March 2013 agreed 100% with its text layer (`docs/ocr-check.md`).
- **126 of 139 PDFs use the standard typography** the structure rules rely on. The other 13 are the twelve 2025–2026 issues (new layout; their text comes from the WordPress pages anyway) and `Man-PDF-Book.pdf` (left out).
- **No Claude API cost for extraction**: the articles are rebuilt by rules from the PDF, so the planned ~$30–40 Batch spend is not needed. Claude is only used for the quiz and for corrections.
- **Narration is bigger than estimated**: the pilots average ~81,000 characters per issue. For the ~121 issues that need Gary that is about **9.8 million characters**, above the 5.5–7.5 million in the handoff and above one month of TTSMaker Studio (6M).

## Fixed during the pilots
- Q&A opening ("The remedy for ignorance…") set in bold in 2023 was read as questions → now always the "Before we begin" box.
- Questions with more than one sentence were laid out as side-by-side columns → fixed.
- Bold words that run on into a paragraph (book blurbs, "Download … here:") were read as headings → now body text.

## Waiting for the owner
1. Confirm the "Left out" table in each `issues/<slug>/review.md` (covers, contents, notices, subscription/advert pages).
2. Gary/TTSMaker key and confirmation that voice 2560 is in the API → narration + read-along timings.
3. Go-ahead for the next step: the Gary issues from WordPress pages, then the batch of remaining PDF issues.
