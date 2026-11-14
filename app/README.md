# Spirit of Islam – Android / iOS app (foundation)

A Capacitor shell around the same pages the website uses. No separate app code to keep in step:
when an issue is rebuilt for the website, the app gets the same page.

## What is here
| File | What it does |
|---|---|
| `build_app.py` | Copies the built website (`dist/`) into `www/`, the folder packed inside the app, and adds the app's own screens. Packs the newest issues (`app-config.json` → `bundle_latest`), all small covers, the search index, quotes and fonts. |
| `src/app.js` | Keeps links inside the app, saves issues on the phone (IndexedDB), app bar and bottom tabs, sharing, links that open the app, lock-screen audio controls. |
| `src/screens.js` | The tab screens: Home, Search, Saved, Profile, and the Gems & leaderboard page (approved canvas "SOI Redesign"). |
| `src/app.css` | App styles. |
| `../site/site.js` | Shared with the website: reading memory (Continue where you left: article, place on the page, audio time), finished articles, saved articles and quotes, Save / Share buttons. |
| `app-config.json` | `remote` = the website the app fetches other issues from; `share` = the address used in shared links (both the preview for now; change to the real domain at launch). |
| `android/`, `ios/` | The native projects (open in Android Studio / Xcode). |
| `tests/test_app.py` | Browser test of the packed files, online and offline. |

## How it behaves
- Bottom tabs: **Home · Search · Saved · Profile**. Reading an issue is full screen with a slim bar (back, issue, share).
- Home: search bar, gems pill, *Continue where you left*, the three newest covers (Read / Listen / Save), How to use SOI
  (placeholders until the videos are recorded), In this issue, Quote of the day.
- Offline: the app screens, archive, search, quotes, all covers and the newest 3 issues work with no internet from the first
  launch. Any other issue is fetched the first time it is opened and then kept. Saved → Issues has *Save all* (about 35 MB).
- Continue where you left: the article, the place on the page and the audio time are remembered on the phone.
- Share: every article has Save and Share; the link is `<share address>/issues/<issue>/#soi-<article>`.
- **Sample data** (marked on screen) until sign-in exists: the name, gems, rank, leaderboard and the "My reading" figures.
  Finished articles and reading days are already recorded on the phone (`soiRead`, `soiDays`) ready to feed the dashboard.
- Audio is streamed from the website; it is not saved for offline yet.

## Build
```
python3 site/build_site.py          # website -> dist/
cd app && npm install
python3 build_app.py                # dist/ -> app/www/
npx cap sync                        # copy www/ into android/ and ios/
npx cap open android                # Android Studio  (or: cd android && ./gradlew assembleDebug)
npx cap open ios                    # Xcode, on the iMac only
```
A test APK is also built by GitHub Actions: **Actions → Build SOI Android app → Artifacts → soi-app-debug**.

## Not done yet / must be checked on a real phone
- Background audio, lock-screen controls and the share sheet are wired up but **not tested on a device**.
- iOS has never been built (needs Xcode on the iMac and an Apple developer account for a real device).
- Links that open the app: Android is prepared (`AndroidManifest.xml`); it becomes automatic once
  `/.well-known/assetlinks.json` (with the release key fingerprint) is on the website. iOS needs the Associated Domains
  entitlement and `/.well-known/apple-app-site-association` (needs the Apple team id). Both are launch steps.
- App icon and splash screen are the Capacitor defaults: put a 1024×1024 icon in `resources/` and run `npx @capacitor/assets generate`.
- App id is `in.co.spiritofislam.app` – it cannot be changed after the first store release; confirm before publishing.
- Voice search (the microphone in the canvas) is left out for now: speech input is unreliable inside app web views.
- Next: Firebase sign-in, real gems and leaderboard, notifications, offline audio, tutorial videos, store listings.
