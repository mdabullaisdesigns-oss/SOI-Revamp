# Spirit of Islam – Android / iOS app

A Capacitor app. It is **one page that never reloads** (so audio keeps playing while the reader moves between
screens) with its own screens and styles; from the website it takes only data – the list of issues, the issue
pages (the magazine block is shown as it is, never rewritten), covers, quotes and the search index.

## What is here
| File | What it does |
|---|---|
| `src/shell.html` | The single page: screen area, bottom tabs, mini player, sheet, toast. |
| `src/core.js` | Screens and transitions, theme and text size, reading view, reading memory (Continue reading), offline issues **with audio**, the mini player, lock-screen controls, sharing. |
| `src/screens.js` | Home, Search, Saved, Profile, Gems & leaderboard, All issues, Quotes. |
| `src/app.css` | The approved SOI design system for the app, light and dark. |
| `build_app.py` | Packs `dist/` data + `src/` into `www/` (the folder inside the app). |
| `make_brand_assets.py` | App icon and splash screen from the logo files in `site/brand/` only. |
| `app-config.json` | `remote` = the website the app fetches issues and audio from; `share` = address used in shared links; `bundle_latest` = how many newest issues are packed in the app. |
| `android/`, `ios/` | The native projects (Android Studio / Xcode). |
| `tests/test_app.py` | Browser test (49 checks). `tests/shots.py` takes screenshots at 375×812 and 412×915, light and dark. |

## How it behaves
- **Tabs:** Home · Search · Saved · Profile. Pushed screens (All issues, Quotes, Gems) and the reading view slide in and
  have a back button; Android's back button and edge-swipe go back.
- **Home:** search bar, gems pill (sample), *Continue reading*, the latest issue (Read / Listen / Save), the three newest
  covers, In this issue, tutorial placeholders (plain tiles, no photos, until the videos exist), quote of the day.
- **Reading view:** full screen with a slim bar (back, issue, share). The article, the place on the page and the audio
  time are remembered; *Continue reading* returns to exactly that place and the audio continues from the same second.
- **Audio everywhere:** leave the reading view and a mini player stays above the tabs on every screen (play/pause,
  close, tap to return to the article). Android: media notification + foreground service (MediaSession plugin).
  iPhone: `audio` background mode; lock-screen controls come from the player itself.
- **Offline:** screens, search, quotes, all covers and the newest 3 issues work with no internet from the first launch.
  Any other issue is kept once opened. *Save for offline* offers **Text and audio**: the recordings are downloaded with
  progress shown in Saved; Saved shows the storage used (text / audio) and lets the reader remove the audio or the issue.
- **Appearance:** dark mode follows the phone or is chosen in Profile; text size follows the phone (Dynamic Type on
  iPhone, font scale on Android) and can be raised in Profile; safe areas for the notch / Dynamic Island / gesture bar;
  tap targets of 44 px or more; names for VoiceOver and TalkBack on every control; reduced-motion respected.
- **Sample data** (marked on screen) until sign-in exists: name, gems, rank, leaderboard and "My reading".

## Build
```
python3 site/build_site.py          # website -> dist/
cd app && npm install
python3 build_app.py                # dist/ + src/ -> app/www/
npx cap sync                        # copy www/ into android/ and ios/
npx cap open android                # Android Studio  (or: cd android && ./gradlew assembleDebug)
npx cap open ios                    # Xcode, on the iMac only
```
Icon and splash (only when the brand files change):
`python3 make_brand_assets.py && npx @capacitor/assets generate --assetPath resources --android --ios`

A test APK and the screenshots are built by GitHub Actions: **Actions → Build SOI Android app → Artifacts**.

## How the reading view works (for whoever maintains it)
The issue page is fetched (from the app, the phone's storage or the website), the magazine block inside
`<div class="soi-issue">` is put into the page and its own scripts are run. The block's player creates an `Audio`
element; `core.js` watches every `Audio` that is created and `navigator.mediaSession`, which is how the mini player
and the Android notification know what is playing. Saved audio is stored in IndexedDB and handed to the block as
local addresses. The block starts only once per page, so opening a *different* issue reloads the page (audio from
the previous issue stops). In dark mode the block's colour variables are re-pointed in `app.css`; the block is not edited.

## Must be checked on a real phone (cannot be tested in a browser)
- Audio with the screen locked and from the lock screen / notification, on Android and iPhone.
- Saving audio for the Sep–Oct 2024 → Sep–Oct 2026 issues: their recordings are still on the old website's address;
  if that server refuses web downloads the app falls back to a native download, which is untested. Audio under
  `/media/audio/` (all newly narrated issues) is tested.
- Storage limits with many issues' audio saved (the phone decides how much a web view may keep).
- Share sheet, haptics, status-bar colours in light/dark, the splash screen, the notch and gesture-bar spacing.
- VoiceOver and TalkBack read-through (names and roles are tested; the spoken flow is not).
- iOS has never been built (needs Xcode on the iMac and an Apple developer account for a real device).

## Launch steps still open
- Links that open the app: Android is prepared (`AndroidManifest.xml`); needs `/.well-known/assetlinks.json` with the
  release key fingerprint on the website. iOS needs the Associated Domains entitlement and
  `/.well-known/apple-app-site-association` (Apple team id).
- App id `in.co.spiritofislam.app` cannot be changed after the first store release; confirm before publishing.
- `app-config.json`: change `remote` and `share` from the preview to the real domain.
- The pigeon in the icon is enlarged from a 470 px file; a vector or 1024 px original would be sharper.
- Next: Firebase sign-in, real gems and leaderboard, notifications, tutorial videos, store listings.
