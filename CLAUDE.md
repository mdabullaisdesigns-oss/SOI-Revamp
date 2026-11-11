# SOI Revamp – rules for Claude

Spirit of Islam magazine (https://spiritofislam.co.in). Owner/developer: Md Abullais.
Full background and decisions: `docs/SOI-Project-Handoff.md` – read it before starting new work.

## Hard rules
- **Ask before skipping or leaving out any content** (articles, sections, audio, notes – anything).
- Never include the "We asked ChatGPT about CPS International" page at the end of each magazine PDF (promotional).
- **No PDFs, MP3s or zips in git.** Media lives in Cloudflare R2 (bucket `soi-media`: `pdfs/<year>/…`, `audio/<year>/…`). `.gitignore` enforces this.
- No API keys or passwords in the repo. Keys go in GitHub Actions secrets or env vars (`GKEY`, `R2_*`).
- Current live site is WordPress + Divi: no plugins, no functions.php edits; custom code goes in Divi head Integration or a Code module.

## Design system (approved)
- Teal #204E60 (dark #173A48), gold #D4CC73, cream #EEEEE5. Crimson #EA3551 only on the end-of-article quote hover.
- Headings Cita Pro; body Plus Jakarta Sans.
- 880px max width, 16px side margin (28px on phones), no sideways scroll 320–1280px.
- All CSS scoped to `.soi-ev` / `#soi-quiz`; all ids and animation names prefixed `soi`.

## Layout of this repo
- `scripts/soi-fetch-archive.py` – lists every PDF/MP3/ISSUE page via the public WP REST API and downloads them.
- `.github/workflows/soi-media-to-r2.yml` – Actions job (run manually) that copies site media to R2 and commits `inventory/*.csv`.
- `inventory/` – generated lists of PDFs, audio and issue pages.
- `docs/` – handoff and decisions.
