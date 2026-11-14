# Redesign – approved 14 Nov 2026

Approved canvas: "SOI Redesign" (claude.ai/artifact/8V2ZVvbWWVfVUirZSBrybY). Pattern reference: Lenskart website and app (layout only, SOI branding).

## Website
- Every page starts with the existing header (pigeon, logo, slogan, world map on #4d9ec3 → #194c3c gradient) – files in `site/brand/`. Use only this logo.
- Gold (#D4CC73) menu bar, boxed (1100px), sticky, bold teal text, teal underline on current/hover. Items: Home · Latest Issue · Archives ▾ · Quotes · Listen · About Us ▾ · Further Reading ▾ · Our Websites ▾ · Contact Us; right: Search, Saved, Sign in.
- Archives ▾ = mega-menu on hover: years on the left (Cita Pro, large), that year's covers on the right.
- Home: header → menu → welcome note (word for word from the live site; website only) → latest issue hero + Continue reading + Quote of the day → latest issues row (covers) → "New here? Start with these" tutorials → Read by topic (photo tiles) → Get the app → footer with "Design & Development by Md Abullais" credit.
- Every issue page: header + menu + the "A Magazine for The Journey of Life" archive banner, then the magazine.

## App (bottom tabs: Home · Search · Saved · Profile)
- Home: search bar + gems pill, Continue where you left (resumes article, scroll and audio position), latest issue cover (Read / Listen / Save), How to use SOI videos, In this issue, Quote of the day.
- Search: recent, "Search by Quran reference (51:56)", popular.
- Saved: Issues / Articles / Quotes tabs, progress per issue, offline badges, Save all.
- Profile: gems + rank strip, Saved/Downloads/Quizzes/Alerts tiles, My reading dashboard (streak, finished, listened, quiz average, 14-day calendar), settings.
- Gems & leaderboard: This week / This issue / All time; earning values in the canvas are a proposal.
- Share any article (universal links open it in the app).

## Images
- Issue covers = page 1 of each PDF (all issues).
- Other images: real nature photos from Unsplash/Pexels (free commercial licence), ~20–25, no AI images.
- **Strictly no people** in photos. **No symbols of other religions** (churches, crosses, temples etc.) – Islamic imagery only, or plain nature.
- Tutorials: iPhone screen recordings by the owner after the app is built; captioned, 20–40 s. Placeholders until then.

## Built – 14 Nov 2026 (status)
- Website: header + gold menu on every page, Archives menu with covers by year, home page as in the canvas (welcome note checked word for word against the live page), covers on every issue card, Listen, Saved (this browser), Sign in (placeholder), Our Founder / Our Mission carried over. Test: `python3 site/tests/test_site.py`.
- Covers: `site/covers/<slug>.webp` (+ `@2x`) for all 133 issues, made by the "Make issue covers" workflow from page 1 of each PDF.
- App: tabs Home · Search · Saved · Profile, Continue where you left, offline issues, Save / Share on articles, Profile + Gems with **sample data**. Test: `python3 app/tests/test_app.py`.
- Photos: 24 Pexels photos shortlisted (`sources/photo-candidates.txt`), **awaiting approval**; until then the photo slots show a drawn landscape. Approved photos go in `site/photos/` and are switched on in `site/menu.json` → `photos`.
- Menu links and the hero line of each issue live in `site/menu.json`.

### Waiting for a decision
1. Photo shortlist (which to drop or swap).
2. Portrait of Maulana Wahiduddin Khan on Our Founder / Our Mission: the live pages show it; left out so far because of the no-people rule.
3. Contact Us: the live page is a message form; the new site has nowhere to send it yet, so the page links to the current form.
4. Footer credit: the canvas has a "Contact" link after "Design & Development by Md Abullais" – needs the address to link to.
5. Gem earning values (shown as "Proposed" in the app).

## Owner's changes (14 Nov 2026, evening)
- No separate Listen section (website or app): audio lives on each article.
- Menu (with icons): Home · Archives ▾ (covers by year) · Quotes · About Us ▾ (Our Founder, Our Mission, SOI Team) · Contact Us; right: Search · Saved · Sign in. Latest Issue, Further Reading and Our Websites removed from the menu; Further Reading and Our Websites are in the footer.
- Gold menu bar runs the full width, joined to the header. Current page: small crimson dot (no underline / block).
- Issue pages: the live site's archive banner exactly (badge, title, description, Browse Full Archive, Past issues of YEAR); one cream background; nearly full phone width for reading.
- Archive: Grid / List switch (remembered in the browser).
- Footer: full logo (pigeon + logo + slogan), no underlined links. Footer options to choose from are on the design canvas.
- No browser-default drop-downs anywhere (custom drop-down component `soiDropdown`).
- SOI Team page from the magazine masthead (Issue 133).
- Approved photos: `sources/photos-approved.txt` → `site/photos/` (workflow "Apply approved photos").
- Later: readers' reviews section, styled as cream cards with a dashed inner border (owner's reference: ulakluz.pl).

## Owner's changes (15 Nov 2026)
- Intro banner and quiz box are exactly as wide as the article tabs (desktop and phone).
- Ornament divider (`site/brand/ornament.svg`, diamonds + central eight-point star) under page and section headings.
- Icons: filled Boxicons style (owner's picks for Archives, Team/About, Reading, Sign in; the rest drawn to match).
- About Us: one page, no drop-down: about the magazine, the founder, the mission (his words from the live site) and the SOI Team (redesigned cards). Old About links redirect.
- Article body text black (#1B1B1B); drop cap stays teal.
- Menu in reversed colours (teal bar, gold text, crimson dot) available to try with `?menu=teal`; gold stays the default until the owner decides.
- Go-to-top with reading progress on every page (shared in `site.js`); issue pages keep their own copy.
- Quotes: Spotlight and Gallery views on one page (visitor chooses, remembered); Listen uses the device's voice for now (Gary later); share pictures use the approved quote photos.
- Footer after the owner's reference (seedjewelry.com): dark teal, full logo, large serif column headings, CPS social links (from cpsglobal.org), "Ask AI about Spirit of Islam" (ChatGPT, Claude, Gemini, Perplexity, Grok – names, not logos), no copyright line; developer credit kept.
- Later: readers' reviews as cream cards with a dashed inner border.
