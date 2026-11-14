# Spirit of Islam – Android / iOS app (foundation)

A Capacitor shell around the same pages the website uses. No separate app code to keep in step:
when an issue is rebuilt for the website, the app gets the same page.

## What is here
| File | What it does |
|---|---|
| `build_app.py` | Copies the built website (`dist/`) into `www/`, the folder packed inside the app. Packs the newest issues (`app-config.json` → `bundle_latest`), the search index, quotes and fonts. |
| `src/app.js` | Keeps links inside the app, saves issues on the phone (IndexedDB), the **Saved** page, and passes the audio player's title/controls to the phone. |
| `src/app.css` | Notch/safe-area spacing and the Saved page styles. |
| `app-config.json` | `remote` = the website the app fetches other issues from (now the preview; change to the real domain at launch). |
| `android/`, `ios/` | The native projects (open in Android Studio / Xcode). |
| `tests/test_app.py` | Browser test of the packed files, online and offline. |

## How it behaves
- Home, archive, search, quotes and the newest 3 issues work with no internet from the first launch.
- Any other issue is fetched the first time it is opened and then kept on the phone. **Saved** (top right)
  lists every issue, with *Save* per issue and *Save all remaining issues* (about 37 MB for all 133).
- Audio is streamed from the website; it is not saved for offline (see "Next").
- Audio uses the same player as the website. On Android the MediaSession plugin shows the media
  notification and runs the foreground service that keeps it playing with the screen off; on iPhone the
  `audio` background mode in `Info.plist` does the same, with lock-screen controls from the player itself.

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
- Background audio and lock-screen controls are wired up but **not tested on a device** (cannot be tested in a browser).
- iOS has never been built (needs Xcode on the iMac and an Apple developer account for a real device).
- App icon and splash screen are the Capacitor defaults. Put a 1024×1024 icon in `resources/` and run
  `npx @capacitor/assets generate`. A 512×512 `resources/app-art.png` is used as the lock-screen picture.
- App id is `in.co.spiritofislam.app` – it cannot be changed after the first store release; confirm before publishing.
- Next: saving audio for offline listening, Firebase login, notifications for a new issue, store listings.
