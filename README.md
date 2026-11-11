# SOI Revamp

Redesign of the Spirit of Islam magazine archive (2013 → now): e-version pages with read-along audio and quizzes, a new static website with search, and Android/iOS apps.

See `CLAUDE.md` for working rules and `docs/SOI-Project-Handoff.md` for the full plan.

## Copy the magazine files to Cloudflare R2
1. Add repo secrets: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`.
2. Actions → **Copy SOI magazine files to R2** → Run workflow.
