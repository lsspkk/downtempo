# Browser version: sign-in, files, storage, hosting (research)

**Summary**: Plan (T131, from documentation only; the test pages are T132). A browser version can work. **OneDrive: yes**: the docs confirm sign-in from a page, Graph calls from a page and file downloads through each file's own download link. **Google Drive: yes for a band, with limits**: reading a shared folder needs a "restricted" permission that public apps must get reviewed, but in Testing mode up to 100 listed people may use it (a warning screen, sign in again every 7 days). Whether Google's picker or an API key can do it without that permission is not in the docs: T132 tests it. **Storage: fine**: the browser's private file system holds hundreds of MB in every major browser. **Hosting**: GitHub Pages through a GitHub Actions workflow.

Idea **Browser player**; tasks in [todo.md](todo.md#browser-player). Today's Python downloader for comparison: [onedrive.md](onedrive.md). The OneDrive test page is built: [browser-tests.md](browser-tests.md).

## OneDrive in a web page

- **Sign-in**: the authorization code flow with PKCE, the way single-page apps sign in. The Entra registration gets a **Single-page application** platform with the page's address as redirect URI (`https://…`, or `http://localhost:…` for local tries) ([entra-redirect-uri-howto](web/entra-redirect-uri-howto.txt), [entra-spa-app-registration](web/entra-spa-app-registration.txt)). Authority as now: `https://login.microsoftonline.com/consumers`; scope as now (`Files.ReadWrite`; T132 can try `Files.Read`).
- **Library**: MSAL.js (`@azure/msal-browser`). Its own CDN is gone since v3: "consume MSAL through a package manager or bundling tool" ([msal-browser-readme](web/msal-browser-readme.txt)). Without a build step there are two ways, both for T132 to try: load the npm package through an ESM CDN (esm.sh or jsDelivr's `+esm`), or write the PKCE flow by hand (a code verifier, a redirect to `/authorize`, one `POST` to `/token`): about a page of code, no library.
- **How long it lasts**: refresh tokens given to a single-page app expire after **24 hours**; then the page sends the browser to the sign-in page again, "users don't have to enter their credentials and usually don't even see" it ([entra-refresh-tokens](web/entra-refresh-tokens.txt)). MSAL keeps tokens in `sessionStorage` by default (gone with the tab); `localStorage` survives browser restarts only with "Keep me signed in"; Safari may wipe it after about 7 days without a visit ([msal-browser-caching](web/msal-browser-caching.txt)).
- **Graph from a page**: "The OneDrive API supports HTTP access control (CORS) to allow single page JavaScript applications" ([onedrive-cors](web/onedrive-cors.txt)). The calls are today's: `/shares/{share id}/driveItem`, list children, walk the folders.
- **Downloading a file**: not `/content` ("you can't use the /content API, because this responds with a 302 redirect", which CORS forbids with an `Authorization` header). Instead ask for each file's `@microsoft.graph.downloadUrl` (`?select=id,@microsoft.graph.downloadUrl`): "Because these URLs are preauthenticated, they can be retrieved without a CORS preflight request" ([graph-driveitem-get-content](web/graph-driveitem-get-content.txt)). The links are short-lived, so ask just before downloading, as the Python code does.

## Google Drive in a web page

- **Sign-in**: Google Identity Services, token model: `initTokenClient` → `requestAccessToken` gives an access token in the page; there is no refresh token in the browser, so the page asks again when it runs out ([gis-token-model](web/gis-token-model.txt)).
- **Permissions** ([drive-scopes](web/drive-scopes.txt)):
  - `drive.file` (recommended, not restricted): only files the user opened with the app "or that the user shares with an app while using the Google Picker API".
  - `drive.readonly` ("View and download all your Drive files") is **restricted**: an app open to the public needs Google's restricted-scope verification, a security assessment included.
- **Testing mode is enough for a band** ([google-app-audience](web/google-app-audience.txt)): a project in Testing status serves "up to 100 test users listed in the OAuth consent screen"; Google shows each a warning first; "Authorizations by a test user will expire seven days from the time of consent". So: the owner adds each bandmate's Google address, and they confirm again weekly. No review needed.
- **The picker** ([drive-picker-overview](web/drive-picker-overview.txt), [drive-picker-web](web/drive-picker-web.txt)): on the web it works with `drive.file` or `drive.readonly`, can show folders only, and needs a token (`setOAuthToken`), an API key and the app id. **Open**: whether picking a *folder* under `drive.file` gives access to the files inside it. The docs don't say; if yes, Google Drive works for everyone without Testing mode or review. T132 tests it.
- **Open: no sign-in at all** for folders shared as "anyone with the link": Drive API calls with only an API key (list the folder's files, download with `alt=media`) are not covered by the saved docs. T132 tests it; if it works, it is the simplest Google path.
- **Downloading**: `files.get` with `alt=media` ([drive-download](web/drive-download.txt)), with the access token (or the API key).

## Where the files live

- **The browser's private file system** (Origin Private File System): "Baseline, widely available" ([mdn-opfs](web/mdn-opfs.txt)). Files are written there and played from a `Blob` URL; IndexedDB would also do.
- **How much** ([mdn-storage-quotas](web/mdn-storage-quotas.txt)): Chrome and Edge up to 60 % of the disk per site; Firefox the smaller of 10 % of the disk and 10 GiB (50 % once persistent); Safari about 60 %. A band's 200 MB is far below all of them.
- **Kept or not**: storage is "best-effort" by default and may be cleared when the disk fills; `navigator.storage.persist()` asks to keep it (Chrome, Edge and Safari decide by themselves from how the site is used). The page should show "kept" or "may be cleared", and the files can always be downloaded again.
- **A real folder on disk** (`showDirectoryPicker`): "not Baseline because it does not work in some of the most widely-used browsers" ([mdn-show-directory-picker](web/mdn-show-directory-picker.txt)): Chrome and Edge only. An extra at most.

## Hosting on GitHub Pages

- Publishing from a branch takes only the repository's root or `/docs` ([github-pages-publishing-source](web/github-pages-publishing-source.txt)). Our `docs/` are these notes, so the test pages live in their own folder and a **GitHub Actions workflow** publishes that folder. In the repository: Settings → Pages → Source: GitHub Actions.
- The address is `https://<user>.github.io/<repo>/`: it is the redirect URI in Entra and the "authorized JavaScript origin" (`https://<user>.github.io`) of the Google client.
- **Check**: GitHub Pages for a private repository may need a paid plan (not in the saved docs).
- Nothing private goes in the pages: client ids and the API key identify the app (the API key restricted to the Pages address); links are pasted into the page; tokens and files stay in the visitor's browser.

## What the user sets up for T132

1. **Entra** (the Downtempo registration or a separate test one): Authentication → Add a platform → Single-page application → redirect URIs: the Pages address and `http://localhost:8000/`.
2. **Google Cloud**: a project; enable the Google Drive API and the Google Picker API; OAuth consent screen in **Testing** with your own address as a test user; an OAuth client of type Web application with the Pages origin; an API key restricted to those APIs and the Pages address. The client id, API key and project number go into the test page's settings.
3. **GitHub**: Settings → Pages → Source: GitHub Actions; the repository public, or a plan that allows Pages for private ones.

## What T132 tests

| # | Test | Answers |
|---|---|---|
| 1 | OneDrive: sign in (MSAL through an ESM CDN; hand-written PKCE if that fails), paste a share link, list media files with sizes | sign-in and Graph from a page |
| 2 | OneDrive: download one file through its `downloadUrl` into the private file system, play it | downloads, storage |
| 3 | Google, picker with `drive.file`: pick a shared folder, list its files, download one | can `drive.file` read inside a picked folder |
| 4 | Google, API key only: paste an "anyone with the link" folder link, list, download one | sign-in-free Google |
| 5 | Google, Testing mode with `drive.readonly`: the same as 3 without the picker | the fallback for a band |
| 6 | Storage: used / allowed (`navigator.storage.estimate()`), `persist()` result, reload the page and play the saved file | does it stay |

Each page carries the banner "Test pages for trying a browser version of Downtempo. Not the app." Browsers: Chrome and Firefox, Safari or a phone if handy.
