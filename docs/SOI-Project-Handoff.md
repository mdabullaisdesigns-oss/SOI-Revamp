# Spirit of Islam (SOI) – Project Handoff

**Owner / developer:** Md Abullais (designs and develops the site for the client)
**Website:** https://spiritofislam.co.in
**Prepared:** 11 November 2026, from the chat of 31 Oct – 10 Nov 2026
**How to use this file:** attach it at the start of a new chat (or save it as `CLAUDE.md` in the project folder) and say "Continue the SOI project from this handoff."

---

## 1. Where things stand

| Area | Status |
|---|---|
| Archive banner on every issue page (2013 → now) | **Done and live** (head code in Divi) |
| Issue 133 (Nov–Dec 2026) e-version | **Done** – 18 articles, 16 with read-along audio, quiz, go-to-top button |
| Client report (PDF, 13 pages) | **Done** – `SOI-Website-Enhancement-Report.pdf` |
| Reusable toolkit | **Done** – `SOI-eversion-toolkit.zip` (keep it safe; attach it to new chats) |
| Redesign of all past issues (2013–2024) | **Planned** – not started |
| New code-based site (leave WordPress), search, quotes library | **Planned** |
| Android + iOS apps | **Planned** |

---

## 2. Current site facts

- WordPress + Divi on a **Hostinger basic WordPress plan**. Each issue is its own page titled "ISSUE …" (e.g. "ISSUE NOVEMBER – DECEMBER 2026").
- The user does **not** want plugins or functions.php edits; custom code goes in **Divi → Theme Options → Integration (head)** or a **Code module**.
- Page background colour of the site: **#EEEEE5**. Site hover colour: **#EA3551**.
- Uses WP Fastest Cache and LiteSpeed Cache – **clear both** after pasting new code.
- Magazine frequency: **monthly from 2013 to March 2021**, **bimonthly** after that. Issue 133 = Nov–Dec 2026 (≈133 issues in total).
- Each magazine PDF ends with a "We asked ChatGPT about CPS International" page – it is **promotional and is never included**.

---

## 3. Archive banner (head code, live on all issue pages)

- "A Magazine for The Journey of Life" card with a "Spirit of Islam • Bimonthly Periodical" pill.
- Buttons: **Browse Full Archive** and **Past Issues of [year]** – the year is detected from the page title, and the link finds the page titled "The Year YYYY" through the WordPress REST API (result cached 30 days).
- Shows only on pages whose title starts with "ISSUE"; never on home/contact pages.
- Card is 880px max, 16px side margin (28px on phones), cream #EEEEE5 background, reduced top padding.
- File: `banner/soi-banner-head-code.html` in the toolkit.

---

## 4. E-version design system (approved, use for every issue)

**Colours**
- Teal **#204E60** (dark **#173A48**) – tabs, headings, buttons
- Gold **#D4CC73** – accents, diamonds, highlights
- Cream **#EEEEE5** – page background
- Crimson **#EA3551** – **only** on the end-of-article quote hover (rejected on tabs/buttons)

**Fonts**
- Headings: **Cita Pro** (Divi font names "Cita Pro" and "Cita Pro Ita")
- Body: **Plus Jakarta Sans** (Google Fonts)

**Article tabs**
- One tab per article; opening one closes the others.
- Numbered circle, gold section label (kicker), Cita Pro title.
- Icon: **gold diamond (icon 4)** with **ripple animation (anim 4)** and a smooth scale on hover.
- Tabs stay plain teal; buttons are light/outlined. (An inverted palette was tried and **rejected**.)
- Tapping a tab brings the **article heading to the top of the screen** (allows ~76px on phones for Safari's floating bar; disables scroll anchoring while opening; closes other tabs instantly to stop jumps).
- Every article has its own link, e.g. `…#soi-the-purpose-of-life`.

**Content details**
- End-of-article reflection: **Style 02** – gold rules + diamonds, turns crimson only on hover. No "A Thought to Ponder" label.
- Drop cap: enlarge **only the letter**, never a leading quotation mark.
- **In Focus** note shows **Maulana Wahiduddin Khan's photo** beside his quote.
- **Q&A opening passage** ("The remedy for ignorance is asking questions. (Prophet Muhammad) …") appears in every issue: shown in a **gold-tinted note box labelled "Before we begin"** (option 2), saying set large in Cita Pro italic.
- Author notes and section intros: soft gold boxes. Quran references like (51: 56) in small bold type.
- CPS Newsletter: every PDF link as an outlined button; books as cards.

**Layout**
- Magazine block and quiz match the banner width: **880px max; 16px side margin; 28px on phones**. No sideways scroll at any width (tested 320–1280px).
- The Divi section that holds the code is turned cream with no padding automatically (CSS `:has()` rule).
- All CSS scoped to `.soi-ev` / `#soi-quiz`; all ids and animation names prefixed **"soi"** so nothing clashes with the site.

---

## 5. Read-along audio player (final "Style 5")

- Sits under each article title: Play, **Back 10s**, **Forward 10s**, **Speed**, **Download**.
- **Speed menu**: 0.75 / 1 / 1.25 / 1.5 / 1.75 / 2×, plus switches **"Follow the text"** (keeps the spoken sentence on screen) and **"Play the next article"**. Centred under the player on phones.
- **Download** button saves the MP3; on small phones it moves into the Speed menu.
- **Docked capsule** at the bottom appears **only while playing and only when the reader has scrolled away**. No "playing in the player below" text.
- **Up next**: 5-second countdown, Play now / Cancel, then the next article opens and plays.
- **Sentence highlighting** in gold; **tap any sentence** to play from it.
- Lock-screen/headphone controls (Media Session); remembers speed and switches (localStorage).
- One shared audio element for all articles (lets auto-next work on iPhone). Blob fallback if the server lacks Range support.
- "10" digits are drawn inside the SVG icons (fixed an iPhone display bug).

**How highlighting works:** at build time a Python script splits each article into sentences and finds each sentence's start time in the MP3 (silence detection + matching sentence lengths); each sentence is written as `<span class="ev-s" data-t="12.4">`. In the browser, plain JavaScript highlights the sentence whose start time has passed and seeks when a sentence is tapped. No framework.

---

## 6. Readers' Reflection quiz

- About **10 multiple-choice questions from the articles only** (not the newsletter); respectful, encouraging wording.
- Asks the **reader's name** first; **30-second timer** per question.
- Every option has an explanation with the **article and page**; "Read the article again" opens that article.
- Results: score, accuracy, time, reader level; **confetti for 7+**; full answer review with source quotations; Retake (shuffled).
- Share: **WhatsApp, X, Copy link** (link opens `#soi-quiz`).
- Visually distinct from the article tabs.
- **Start button: "Let's Start" split block** (teal label + gold arrow block). No Bismillah wording.

---

## 7. Go-to-top button

- **Option D "light coin"**: cream button whose **gold ring fills with scroll progress**; arrow bobs gently.
- Shows the **percentage read on hover** (on press on phones).
- Appears after ~500px of scroll; **moves up above the docked audio player** so they never overlap.

---

## 8. How Issue 133 is installed

1. Upload the **16 MP3s** (`SOI-133-<article-id>.mp3`) to the Media Library. The code points to `https://spiritofislam.co.in/wp-content/uploads/2026/10/`, so they must be in the **2026/10** folder (the Media Library "Folders" plugin is only virtual; the real folder is by upload month). Don't rename files.
2. Add a **Regular** section → single-column row → **Code** module → paste **`SOI-Issue-133-complete.html`** (e-version + quiz + go-to-top in one block). Remove any older separate modules.
3. Save, clear WP Fastest Cache + LiteSpeed, check on a phone.

**Audio in Issue 133:** voice **Gemini TTS "Charon"** (model gemini-3.8-flash-lite-tts, temperature 0.5). **Children's Corner** (a Goodword "Five Pillars Family Games" product page) and **CPS Newsletter** (event notices and links) have **no audio** – Claude left them out without asking; user may want them added. Plan: re-narrate Issue 133 with **Gary** for consistency.

---

## 9. Toolkit (`SOI-eversion-toolkit.zip`)

- `issue-133/SOI-Issue-133-complete.html` – the final Divi code.
- `build/build.py` – issue text → 18 tabs (drop caps, notes, Q&A box, newsletter links, sentence spans, players).
- `build/combine.py` – joins e-version + quiz, adds page-fit rules, go-to-top, "soi" prefixes.
- `build/align.py`, `build/sentences.py` – joins narration clips into one MP3 per article (96 kbps mono, −16 LUFS) and times every sentence.
- `build/player.css`, `build/player.js` – the player. `build/extra.css`, `build/soi-eversion-tabs-v6.html` – tab design and open/scroll behaviour.
- `build/quiz-template.html` – quiz (questions in the `QUESTIONS` list).
- `build/raw.json`, `outline.json`, `audio_texts.json`, `audio_cues.json` – Issue 133 data.
- `audio-tools/` – Gemini TTS + transcription check (API key via `GKEY` env var; **no keys stored**).
- `banner/`, `fonts/` (Cita Pro), `report/` (client report template), `README.md`.
- The cloud workspace used in this chat is temporary – **only the zip and delivered files survive**.

---

## 10. Problems met and how they were solved

- **Free TTS (Kokoro)** quality not good enough → moved to Gemini.
- **Gemini read the style instructions aloud** → switched to the "director's notes" prompt format.
- **Gemini free daily limit (~10 requests)** hit repeatedly → bigger chunks (≤900 words); recommended billing.
- **Copyright filter** blocked "The Word of God" (Quran translation + Tazkirul Quran commentary are published online) → split into 14 short pieces; generated via API.
- **AI Studio recording cut off** mid-article → caught by word-by-word transcript check.
- **MutationObserver loop froze the page** → only react when open state changes.
- **Audio wouldn't play in chat preview** → real MP3 files, visible error, blob fallback.
- **Seeking failed without Range support** → canSeek + download-as-blob fallback.
- **White bands above/below the code in Divi** → section/row padding removed with scoped `:has()` CSS.
- **Mobile looked cramped** (Divi row is 80% wide) → row full width, block matches banner width; smaller kickers; time no longer overlaps Back.
- **Tapping an article showed the audio, or jumped to the footer** → scroll to heading with offset, close others instantly, disable scroll anchoring during opening, correct drift after 700ms.
- **Speed menu off-centre on phones; "10" hidden in icons** → centred menu; SVG text.
- **Docked player could be clipped** near the quiz → removed clip-path background trick.

---

## 11. Plan: redesign every past issue

- **Scope:** about **121 issues** – 2013 to 2024 (~99 monthly + ~22 bimonthly). Issues from **2025 onward already have Gary audio**; they still get the new design, and their existing audio can get read-along timings if it matches the text.
- **Voice decision:** use **TTSMaker "Gary" (#2560, US male)** for everything, matching 2025+ issues. TTSMaker now has an **API** (Pro/Studio only, 20,000 characters per request, ~1 request/second, speed 0.5–2×, paragraph pause 0.5–5 s, MP3 link expires in 2 h). **Confirm Gary is in the API voice list before paying.**
- **Characters needed:** ~5.5–7.5 million → **TTSMaker Studio for 1 month** (6M characters, ~$120–140) + a small top-up if needed. Pro Max (~1.2M/month) would take 5–6 months.
- **Source files:** read PDFs and old audio **directly from WordPress** via the REST API (`/wp-json/wp/v2/media`, `/pages`). Use a WordPress **Application Password** (not the admin password). First job: an **inventory spreadsheet** of every issue – PDF location, which articles have audio, what's missing. (User mentioned some audio may not be on WordPress – confirm where.)
- **Pipeline per issue:** PDF → structured text (Claude) → automatic **word-match check against the PDF** (flag <99%) → OCR route for scanned 2013-era PDFs → quiz + quotes → Gary narration via API → align → build → test.
- **Cheapest route for the bulk:** scripted Claude API with Batch (≈ $0.40–0.55 per issue, ~$30–40 for all with Batch); development work on a Claude subscription.
- **Pilot first:** 2–3 issues including one scanned 2013 issue, to measure real cost and time.

---

## 12. Plan: new website (leave WordPress)

- **Static site** generated by the build scripts (plain HTML/CSS/JS) – faster, nothing to hack or update, free hosting. PHP not required.
- **Hosting:** Cloudflare Pages (free, unlimited bandwidth). **Audio:** Cloudflare R2 (free up to 10 GB; ~6 GB expected). Can stay on Hostinger for now if storage allows; only one address in the build changes later.
- **Before cancelling Hostinger:** check whether domain **email** runs there; build **redirects for old `?page_id=` links** so 13 years of shared links keep working; replace the contact form (Formspree or a Cloudflare Worker).
- **Search (Pagefind, free):** across all issues; results open the **exact article and sentence** (option to play from there); snippets with highlighted words; filters by year, issue, author, section; Quran references ("51:56"); tolerant of spelling (favour/favor) and typos; works offline in the app. Later option: meaning-based search.
- **Quotes library:** collect every closing reflection and In Focus quote from all issues automatically; filter by topic/issue; link back to the article; share as an image card (WhatsApp/Instagram); "Quote of the day". (Confirm this is what the user meant by "quotes".)

---

## 13. Plan: Android + iOS apps

- **Tech:** **Capacitor** wrapping the same web code (no rewrite). Pages **shipped inside the app** for instant, offline reading. Audio through a **native player plugin** for screen-locked/background play – the **same player UI and all controls stay** (Back/Forward 10s, speed, follow text, auto-next, tap sentence, docked player, download).
- **Backend:** **Firebase** – Auth (Google, email, **Sign in with Apple – required by Apple when Google login is offered**), Firestore (progress, scores), Cloud Messaging (notifications). Free at this size.
- **Features:** login; reading progress synced across devices; notification for each new issue; **scoreboards per issue and all-time**; bookmarks/favourite quotes; offline downloads; lock-screen controls; share; dark mode; search; quote of the day.
- **Harder/extra:** widgets, Apple Watch, CarPlay, in-app purchases (Apple commission).
- **Offline:** downloaded issues, downloaded audio, search, and quizzes work offline (scores sync later). Login, live scoreboards, new issues and notifications need internet.
- **Size:** Android ~5–15 MB, iOS ~15–30 MB; issues/audio downloaded on demand.
- **Feel:** smooth for reading/audio/quiz; slightly less native for gestures/transitions unless designed carefully.
- **Apple review:** needs real app features (offline downloads, background audio, notifications) – a plain website wrapper risks rejection. Store review takes days to weeks.
- **Status (14 Nov 2026):** foundation built in `app/` (Capacitor 8, `android/` + `ios/` projects, offline reading with a Saved page, website player connected to the Android media notification / iOS audio background mode, test APK from GitHub Actions). Not yet: device test of background audio, iOS build, icon/splash, offline audio, Firebase. Details: `app/README.md`.
- **Accounts:** Google Play $25 one-time; Apple Developer ~₹8,700/year. The user's **iMac** handles iOS builds.

---

## 14. Working setup

- Use **Claude Code** (VS Code extension on the iMac) with the project in a **GitHub repo**; keep MP3s and PDFs **out of GitHub** (R2/Hostinger/separate storage).
- Claude Code needs **continuous internet**; the iMac is often offline (iPhone hotspot) → run long batch work as **Claude Code cloud sessions** (claude.ai/code; keep running when the Mac is off; same plan limits, no extra charge). Review in VS Code at home.
- **Don't set an Anthropic API key** on the Mac while using the subscription, or usage is billed to the API.
- Put a **CLAUDE.md** with these rules in the repo. Include: **"Ask before skipping or leaving out any content."**
- **Fable reset coupon:** one-time "Reset for free" in the Usage screen, **expires 17 November 2026**. Refills the Fable allowance and the 5-hour limit and gives back Fable's share of the weekly limit. Use it when stuck at a limit in the middle of heavy work, not when bars are low.

---

## 15. Cost and time estimates (INR, ~₹95/$, before 18% GST + ~2–3.5% forex)

| Item | Estimate |
|---|---|
| TTSMaker Studio, 1 month (+ possible top-up) | ~₹13,500–16,000 |
| Claude Max (~₹9,500/month + GST), 1–2 months | ~₹11,200–22,500 |
| Scripted Claude API for bulk extraction (optional) | ~₹3,000–7,500 |
| Hosting, search, login, notifications | ₹0 (free tiers) |
| Google Play (one-time) + Apple (yearly) | ~₹11,100 |
| **Total** | **~₹36,000–50,000** (first year); ~₹8,700/year after |

- **Time:** archive 2–4 weeks of work; website + search ~1 week; apps 1–2 weeks + store review; realistic calendar **4–8 weeks**. User review ~10–15 min per issue.
- Note: Gemini once claimed "₹700–1,700 total" – that contained a 10× arithmetic error on TTS and left out output tokens and most of the project.

---

## 16. Open questions / next steps

1. Confirm **Gary (#2560)** is available through the TTSMaker API; check current TTSMaker prices in the account.
2. Where are the audio files that aren't on WordPress?
3. Add audio for **Children's Corner** and **CPS Newsletter**? Re-narrate Issue 133 with Gary?
4. Confirm the **quotes library** idea is what was meant.
5. Check whether domain **email** is on Hostinger before moving off it.
6. **Next actions:** create the GitHub repo + CLAUDE.md → WordPress inventory → build the bulk pipeline → pilot 2–3 issues → website + search → app foundation.

---

## 17. Useful links (private to the user's Claude account)

- E-version preview (Issue 133): https://claude.ai/artifact/SLmec4W3cFkYj7BTW8kef3
- Client report page: https://claude.ai/artifact/Ha9S9FdfGnGWWLHgs4qLKP
- Q&A intro options: https://claude.ai/artifact/BT486Pupf2TD4zPpYgK2w7
- Go-to-top / Let's Start options: https://claude.ai/artifact/Hvq4bQj6DZk6wxxm4XQXvB
- Narration scripts page: https://claude.ai/artifact/79mUz8HpQLWfWpPUwdQPUM
- Gemini API keys shared in screenshots during this chat should be **deleted** and replaced.
