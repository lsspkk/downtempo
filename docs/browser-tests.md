# Browser test pages

**Summary**: Built (T132, OneDrive only; Google Drive waits). One page in `frontends/browser-tests/` (plain HTML + JS, no build step, no library) tests whether a web page can sign in to OneDrive, list a shared folder, download a file into the browser's private file system and play it again after a reload: tests 1, 2 and 6 of [browser-research.md](browser-research.md#what-t132-tests). A GitHub Actions workflow publishes it to `https://lsspkk.github.io/downtempo/`. The user's try-out is T133.

## Files

| File | One job |
|---|---|
| `settings.js` | client id, authority, scopes (nothing secret) |
| `onedrive.js` | sign-in by hand-written PKCE (redirect to `/authorize`, one `POST` to `/token`, refresh when the access token runs out), share link → share id, walk the folder, each file's `downloadUrl` |
| `storage.js` | the private file system: save a download as it streams, list, open, delete; used / allowed, `persist()` |
| `page.js`, `index.html` | the page: sign in, paste a link, list, download + play, saved files, a log to copy into a report |
| `.github/workflows/browser-tests.yml` | publishes the folder on every push to `main` that changes it |

Hand-written PKCE instead of MSAL.js: MSAL has no CDN of its own and the flow is a page of code ([browser-research.md](browser-research.md#onedrive-in-a-web-page)). Tokens live in `sessionStorage`: closing the tab signs out.

## Setup (once)

- Entra, the Downtempo registration: Authentication → Add a platform → **Single-page application**, redirect URIs `https://lsspkk.github.io/downtempo/` and `http://localhost:8000/` (exactly, with the final `/`).
- GitHub: Settings → Pages → Source: **GitHub Actions**; the repository public.

## Run

- Locally: `uv run python -m http.server 8000 -d frontends/browser-tests`, open `http://localhost:8000/`.
- Published: push to `main`; the Actions tab shows the run; then open `https://lsspkk.github.io/downtempo/`.
