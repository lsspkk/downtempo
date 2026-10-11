"""OneDrive shared folders: MSAL device code sign-in and Microsoft Graph listing (docs/onedrive.md).

Finds folders and files only; `sync.py` downloads them through `OneDriveConnection.request`.
"""

import base64
import os
import threading
from collections.abc import Iterator, Mapping
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qs, urlparse

import msal
import requests

from downtempo.config import (
    AUDIO_EXTENSIONS,
    DATA_DIR,
    SHEET_EXTENSIONS,
    TOKENS_DIR,
    load_env,
)
from downtempo.downloaders.remote import RemoteFile, RemoteFolder, RemoteFolderInfo
from downtempo.downloaders.web import request_error
from downtempo.errors import Cancelled, UserError
from downtempo.events import Report, SignIn

GRAPH = "https://graph.microsoft.com/v1.0"
# Personal Microsoft accounts only; see docs/onedrive.md.
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Files.ReadWrite"]
TOKEN_CACHE = TOKENS_DIR / "onedrive.json"
OLD_TOKEN_CACHE = DATA_DIR / ".onedrive_token.json"  # before T59
# Downtempo's own app registration in Microsoft Entra ("downtempo", personal accounts, public
# client flows on). PUBLIC ON PURPOSE: a client ID only names the app at sign-in; it is not a
# password and gives no access to anyone's files. Each user signs in with their own account, and
# their token stays on their computer (data/tokens/). A desktop app is a "public client" and has
# no secret at all (docs/onedrive.md, web/entra-public-confidential-clients.txt).
# ONEDRIVE_CLIENT_ID in .env overrides it, e.g. with your own registration.
DOWNTEMPO_CLIENT_ID = "45bf3d02-6c45-4b46-b66c-3a7e562f9c1c"
HOSTS = {"1drv.ms", "onedrive.live.com"}


class OneDrive:
    type = "onedrive"
    label = "OneDrive"

    def owns(self, url: str) -> bool:
        return (urlparse(url).hostname or "").lower() in HOSTS

    def account(self) -> str | None:
        cache = load_cache()
        accounts = cache.find(msal.TokenCache.CredentialType.ACCOUNT)
        return accounts[0].get("username") if accounts else None

    def sign_out(self) -> None:
        load_cache()  # moves an old cache first, so it goes too
        TOKEN_CACHE.unlink(missing_ok=True)

    def connect(self, report: Report, cancel: threading.Event) -> "OneDriveConnection":
        cache = load_cache()
        try:
            app = msal.PublicClientApplication(
                client_id(), authority=AUTHORITY, token_cache=cache
            )
            accounts = app.get_accounts()
            result = accounts and app.acquire_token_silent(SCOPES, account=accounts[0])
            if not result:
                result = sign_in(app, report, cancel)
        except requests.RequestException as error:
            raise request_error(error) from error
        except ValueError as error:  # MSAL can't fetch the sign-in server's settings
            raise UserError(
                "Can't reach the Microsoft sign-in server.",
                "Check the internet connection and try again.",
            ) from error
        finally:
            save_cache(cache)
        if "access_token" not in result:
            raise UserError(
                f"OneDrive sign-in failed: {result.get('error_description', result)}",
                "Try again; if it keeps failing, sign out and in again.",
            )
        return OneDriveConnection(app, cache, app.get_accounts()[0])


def client_id() -> str:
    load_env()
    if found := os.environ.get("ONEDRIVE_CLIENT_ID") or DOWNTEMPO_CLIENT_ID:
        return found
    raise UserError(
        "OneDrive isn't set up on this computer.",
        "Set ONEDRIVE_CLIENT_ID in .env (see docs/onedrive.md).",
    )


def sign_in(
    app: msal.PublicClientApplication, report: Report, cancel: threading.Event
) -> dict[str, Any]:
    """The device code flow: report the code, then wait until the user signed in or cancelled."""
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise UserError(
            f"OneDrive sign-in could not start: {flow.get('error_description', flow)}",
            "Check that the app registration allows public client flows (docs/onedrive.md).",
        )
    report(
        SignIn(
            "OneDrive", flow["verification_uri"], flow["user_code"], flow["expires_at"]
        )
    )
    waiting = threading.Event()

    def stop_on_cancel() -> None:
        # MSAL's documented way to end the polling: it stops at its next poll, a few seconds.
        while not waiting.wait(0.3):
            if cancel.is_set():
                flow["expires_at"] = 0
                return

    threading.Thread(target=stop_on_cancel, daemon=True).start()
    try:
        result = app.acquire_token_by_device_flow(flow)
    finally:
        waiting.set()
    if cancel.is_set():
        raise Cancelled()
    if result.get("error") == "expired_token":
        raise UserError(
            "The sign-in code expired.", "Try again and enter the new code."
        )
    return result


def load_cache() -> msal.SerializableTokenCache:
    if OLD_TOKEN_CACHE.exists() and not TOKEN_CACHE.exists():
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        OLD_TOKEN_CACHE.replace(TOKEN_CACHE)
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE.exists():
        cache.deserialize(TOKEN_CACHE.read_text(encoding="utf-8"))
    return cache


def save_cache(cache: msal.SerializableTokenCache) -> None:
    """Only the owner may read it (mode 600), written whole or not at all."""
    if not cache.has_state_changed:
        return
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    temporary = TOKEN_CACHE.with_name(TOKEN_CACHE.name + ".tmp")
    handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w", encoding="utf-8") as output:
        output.write(cache.serialize())
    os.replace(temporary, TOKEN_CACHE)
    cache.has_state_changed = False


def share_id(url: str) -> str:
    """Encode a sharing URL as a Graph share id (u!<unpadded base64url>)."""
    redeem = parse_qs(urlparse(url).query).get("redeem", [None])[0]
    if redeem:
        redeem += "=" * (-len(redeem) % 4)
        url = base64.urlsafe_b64decode(redeem).decode("utf-8")
    encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return f"u!{encoded}"


def kind(name: str) -> str:
    suffix = PurePosixPath(name).suffix.lower()
    return (
        "audio"
        if suffix in AUDIO_EXTENSIONS
        else "sheet"
        if suffix in SHEET_EXTENSIONS
        else ""
    )


class OneDriveConnection:
    def __init__(
        self,
        app: msal.PublicClientApplication,
        cache: msal.SerializableTokenCache,
        account: dict[str, Any],
    ) -> None:
        self.app, self.cache, self.account = app, cache, account
        self.session = requests.Session()

    def token(self) -> str:
        """The access token, refreshed by MSAL when it's about to expire (long downloads)."""
        result = self.app.acquire_token_silent(SCOPES, account=self.account)
        save_cache(self.cache)
        if not result or "access_token" not in result:
            raise UserError("The OneDrive sign-in has expired.", "Sign in again.")
        return result["access_token"]

    def get(self, url: str, **headers: str) -> requests.Response:
        try:
            response = self.session.get(
                url,
                headers={"Authorization": f"Bearer {self.token()}", **headers},
                timeout=60,
            )
            if response.status_code not in (400, 404):
                response.raise_for_status()
            return response
        except requests.RequestException as error:
            raise request_error(error) from error

    def children(self, ref: tuple[str, str]) -> list[dict[str, Any]]:
        drive, item = ref
        items: list[dict[str, Any]] = []
        next_url: str | None = f"{GRAPH}/drives/{drive}/items/{item}/children"
        while next_url:
            response = self.get(next_url)
            if not response.ok:
                raise UserError(
                    "A folder in the share can't be listed.",
                    "It may have been moved or deleted; try again.",
                )
            page = response.json()
            items.extend(page.get("value", []))
            next_url = page.get("@odata.nextLink")
        return items

    def open(self, url: str, folder: str = "") -> RemoteFolder:
        response = self.get(
            f"{GRAPH}/shares/{share_id(url)}/driveItem", Prefer="redeemSharingLink"
        )
        if not response.ok:
            raise UserError(
                "This link doesn't open a OneDrive shared folder.",
                "Copy the folder's share link again; it may have been removed.",
            )
        root = response.json()
        if "folder" not in root:
            raise UserError(
                "The link opens a file, not a folder.",
                "Share the folder that holds the songs.",
            )
        drive = root["parentReference"]["driveId"]
        current = RemoteFolder(root["name"], "", (drive, root["id"]))
        for part in (p for p in folder.split("/") if p):
            subfolders = [i for i in self.children(current.ref) if "folder" in i]
            found = next(
                (i for i in subfolders if i["name"].casefold() == part.casefold()), None
            )
            if not found:
                names = ", ".join(i["name"] for i in subfolders) or "none"
                raise UserError(
                    f"No folder '{part}' in '{current.name}'.",
                    f"Folders there: {names}",
                )
            path = f"{current.path}/{found['name']}".lstrip("/")
            current = RemoteFolder(found["name"], path, (drive, found["id"]))
        return current

    def folders(self, folder: RemoteFolder) -> list[RemoteFolderInfo]:
        drive = folder.ref[0]
        found = []
        for item in self.children(folder.ref):
            if "folder" not in item:
                continue
            below = list(self.walk((drive, item["id"]), PurePosixPath()))
            kinds = [kind(f.path.name) for f in below]
            found.append(
                RemoteFolderInfo(
                    item["name"],
                    f"{folder.path}/{item['name']}".lstrip("/"),
                    kinds.count("audio"),
                    kinds.count("sheet"),
                    len({f.path.parts[0] for f in below if len(f.path.parts) > 1}),
                )
            )
        return sorted(found, key=lambda f: f.name.casefold())

    def files(self, folder: RemoteFolder) -> Iterator[RemoteFile]:
        yield from self.walk(folder.ref, PurePosixPath())

    def walk(self, ref: tuple[str, str], below: PurePosixPath) -> Iterator[RemoteFile]:
        for item in self.children(ref):
            if "folder" in item:
                yield from self.walk((ref[0], item["id"]), below / item["name"])
            elif "file" in item and kind(item["name"]):
                modified = item.get("lastModifiedDateTime")
                yield RemoteFile(
                    below / item["name"],
                    item.get("size"),
                    datetime.fromisoformat(modified) if modified else None,
                    (ref[0], item["id"]),
                )

    def request(self, file: RemoteFile) -> tuple[str, Mapping[str, str]]:
        # Graph answers with a redirect to a short-lived download URL; requests drops the
        # Authorization header when it follows a redirect to another host.
        drive, item = file.ref
        return (
            f"{GRAPH}/drives/{drive}/items/{item}/content",
            {"Authorization": f"Bearer {self.token()}"},
        )
