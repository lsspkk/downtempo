# Authenticating to OneDrive (Microsoft Entra + MSAL + Microsoft Graph)

## Answer

The supported way is OAuth through **Microsoft Entra**:

1. Register an app in Microsoft Entra (free, takes a couple of minutes).
2. The OneDrive downloader (`src/downtempo/downloaders/onedrive.py`) signs you in with **MSAL Python** using the **device code flow**. It prints
   a code, and you enter it at <https://microsoft.com/devicelogin>.
3. It calls **Microsoft Graph** (`graph.microsoft.com`) with `Authorization: Bearer <token>`.
4. It walks the folder tree and downloads each file from its short-lived
   `@microsoft.graph.downloadUrl`.

Copying browser cookies or the "Badger" token, or calling `api.onedrive.com` anonymously, is
not supported. Microsoft broke anonymous share access in late 2024 (that's the `401
Unauthorized` this project got). See [why-not-share-link-hacks.md](why-not-share-link-hacks.md).

## 1. Register the app in Microsoft Entra

Source: [entra-register-app](web/entra-register-app.txt)

1. Go to <https://entra.microsoft.com> → **Identity → Applications → App registrations → New registration**.
   You can sign in with your personal Microsoft account. If you have no tenant, use
   <https://portal.azure.com>, which creates a default directory for you.
2. **Name**: `downtempo` (any name works).
3. **Supported account types**: **Personal accounts only**. If the folder is in a work or school
   OneDrive, pick *Any Entra ID Tenant + Personal Microsoft accounts* instead and change
   `AUTHORITY` in `downloaders/onedrive.py` (see below).
4. **Redirect URI**: leave it empty. The device code flow doesn't need one.
5. Click **Register** and copy the **Application (client) ID** into `.env` as `ONEDRIVE_CLIENT_ID`.
6. Open **Authentication** → **Advanced settings** → **Allow public client flows** → **Yes** → **Save**.
   The device code flow fails with `AADSTS7000218` if this is off.
7. Optional: **API permissions** → Microsoft Graph → Delegated → `Files.ReadWrite`. For
   personal accounts, the user consents at sign-in anyway, so you can skip this step.

You don't need a client secret or certificate. This is a *public client* (a CLI on your own
machine), so it only has a client ID.

## 2. Sign-in: device code flow with MSAL

Sources: [entra-device-code-flow](web/entra-device-code-flow.txt),
[msal-python-acquire-token](web/msal-python-acquire-token.txt),
[msal-python-device-flow-sample](web/msal-python-device-flow-sample.txt),
[msal-python-token-cache](web/msal-python-token-cache.txt)

```python
app = msal.PublicClientApplication(
    client_id,
    authority="https://login.microsoftonline.com/consumers",
    token_cache=cache,
)
result = app.acquire_token_silent(SCOPES, account=accounts[0])  # cached refresh token
if not result:
    flow = app.initiate_device_flow(scopes=SCOPES)
    print(flow["message"])          # "To sign in, use a web browser to open ... and enter the code XXXX"
    result = app.acquire_token_by_device_flow(flow)
token = result["access_token"]
```

- Authority `/consumers` means personal Microsoft accounts only. Use `/common` for both personal
  and work or school accounts, or `/organizations` / `/<tenant-id>` for work or school only.
- The token cache is saved to `data/.onedrive_token.json` (git-ignored, mode 600). Later runs refresh
  silently, so you only sign in once, until the refresh token expires (roughly 90 days of inactivity).

## 3. Permissions (scopes)

Sources: [graph-shares-get](web/graph-shares-get.txt),
[graph-driveitem-list-children](web/graph-driveitem-list-children.txt),
[graph-driveitem-get-content](web/graph-driveitem-get-content.txt),
[graph-permissions-files](web/graph-permissions-files.txt)

These are the least-privileged scopes for a personal Microsoft account:

| Call | Scope |
|---|---|
| `GET /shares/{id}/driveItem` | `Files.ReadWrite` |
| `GET /drives/{d}/items/{i}/children` | `Files.Read` |
| `GET /drives/{d}/items/{i}/content` | `Files.Read` |

The script requests `Files.ReadWrite` because the shares endpoint needs it. If the folder is in
**your own** OneDrive, you can skip `/shares` and use `Files.Read` with
`GET /me/drive/root:/Path/To/Folder:/children`.

Personal accounts can't use application permissions (app-only, client secret). They need delegated
sign-in like the flow above.

## 4. Graph calls to walk and download the tree

Sources: [graph-onedrive-overview](web/graph-onedrive-overview.txt), [graph-shares-get](web/graph-shares-get.txt)

```
GET https://graph.microsoft.com/v1.0/shares/u!<base64url(share link)>/driveItem
    Authorization: Bearer <token>
    Prefer: redeemSharingLink               # adds the shared item to the signed-in user's access
→ root.id, root.parentReference.driveId

GET https://graph.microsoft.com/v1.0/drives/{driveId}/items/{itemId}/children
→ value[] (+ @odata.nextLink for paging); folders have "folder", files have "file"
   and "@microsoft.graph.downloadUrl"

GET <@microsoft.graph.downloadUrl>          # NO Authorization header; valid for only a few minutes
```

To encode the share id, base64-encode the sharing URL, convert it to URL-safe base64 with no `=`
padding, and prefix `u!`. If the link is `onedrive.live.com/?...&redeem=<b64>`, decode `redeem`
first to get the original `1drv.ms` link and encode that.

## 5. Running it

```sh
cp .env.example .env                            # fill ONEDRIVE_CLIENT_ID
cp data/sources.example.toml data/sources.toml  # add the sharing link, type = "onedrive"
uv run downtempo download                       # first run: follow the device-login prompt
```

## Troubleshooting

| Error | Meaning / fix |
|---|---|
| `AADSTS7000218 ... client_assertion or client_secret` | Turn on **Allow public client flows** in the app registration. |
| `AADSTS50020` / `AADSTS700016` | Wrong account type or authority. The app must allow personal accounts and use `/consumers` or `/common`. |
| `401` from Graph | Token is missing or expired. Delete `data/.onedrive_token.json` and sign in again. |
| `403 accessDenied` on `/shares` | The signed-in account can't use the link. Check that the link still works in a browser for that account, and that the scope includes `Files.ReadWrite`. |
| `404 itemNotFound` on `/shares` | The share id is wrong. Check the decoded `1drv.ms` URL. |
