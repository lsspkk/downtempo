"""OneDrive shared folders via MSAL device code sign-in and Microsoft Graph (see docs/onedrive.md)."""

import base64
import os
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import msal
import requests

from downtempo.config import DATA_DIR, MEDIA_EXTENSIONS, Source
from downtempo.downloaders.files import request_error, save_url
from downtempo.errors import UserError
from downtempo.events import Report, SignIn, Skipped

GRAPH = "https://graph.microsoft.com/v1.0"
# Personal Microsoft accounts only; see docs/onedrive.md.
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Files.ReadWrite"]
TOKEN_CACHE = DATA_DIR / ".onedrive_token.json"


def acquire_token(client_id: str, report: Report) -> str:
    """Sign in with the device code flow, reusing the cached refresh token."""
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE.exists():
        cache.deserialize(TOKEN_CACHE.read_text(encoding="utf-8"))
    app = msal.PublicClientApplication(
        client_id, authority=AUTHORITY, token_cache=cache
    )

    result = None
    if accounts := app.get_accounts():
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise UserError(
                f"OneDrive sign-in could not start: {flow.get('error_description', flow)}",
                "Check that the app registration allows public client flows (docs/onedrive.md).",
            )
        report(
            SignIn(
                "OneDrive",
                flow["verification_uri"],
                flow["user_code"],
                flow["expires_at"],
            )
        )
        result = app.acquire_token_by_device_flow(flow)

    if cache.has_state_changed:
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE.write_text(cache.serialize(), encoding="utf-8")
        TOKEN_CACHE.chmod(0o600)
    if "access_token" not in result:
        if result.get("error") == "expired_token":
            raise UserError("The sign-in code expired.", "Run the download again.")
        raise UserError(
            f"OneDrive sign-in failed: {result.get('error_description', result)}"
        )
    return result["access_token"]


def share_id(url: str) -> str:
    """Encode a sharing URL as a Graph share id (u!<unpadded base64url>)."""
    redeem = parse_qs(urlparse(url).query).get("redeem", [None])[0]
    if redeem:
        redeem += "=" * (-len(redeem) % 4)
        url = base64.urlsafe_b64decode(redeem).decode("utf-8")
    encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return f"u!{encoded}"


def list_children(
    session: requests.Session, drive_id: str, item_id: str
) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    next_url: str | None = f"{GRAPH}/drives/{drive_id}/items/{item_id}/children"
    while next_url:
        response = session.get(next_url)
        response.raise_for_status()
        page = response.json()
        children.extend(page.get("value", []))
        next_url = page.get("@odata.nextLink")
    return children


def download_tree(
    session: requests.Session,
    drive_id: str,
    item_id: str,
    output_dir: Path,
    source: str,
    report: Report,
) -> None:
    for item in list_children(session, drive_id, item_id):
        if "folder" in item:
            download_tree(
                session, drive_id, item["id"], output_dir / item["name"], source, report
            )
        elif Path(item["name"]).suffix.lower() in MEDIA_EXTENSIONS:
            # Pre-authenticated, short-lived URL: fetch it without the Graph token.
            if url := item.get("@microsoft.graph.downloadUrl"):
                save_url(
                    url,
                    output_dir / item["name"],
                    source,
                    report,
                    item.get("size"),
                    item.get("lastModifiedDateTime"),
                )
            else:
                report(Skipped(source, output_dir / item["name"], "no download URL"))


def download(source: Source, report: Report) -> None:
    """Download the source's shared folder; failures become `UserError`s."""
    client_id = os.environ.get("ONEDRIVE_CLIENT_ID")
    if not client_id:
        raise UserError(
            "OneDrive isn't set up on this computer.",
            "Set ONEDRIVE_CLIENT_ID in .env (see docs/onedrive.md).",
        )
    try:
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {acquire_token(client_id, report)}"
        root = open_share(session, source.url)
        drive_id = root["parentReference"]["driveId"]
        target = find_subfolder(session, drive_id, root, source.subfolder)
        download_tree(
            session, drive_id, target["id"], source.target, source.name, report
        )
    except requests.RequestException as error:
        raise request_error(error) from error


def open_share(session: requests.Session, url: str) -> dict[str, Any]:
    response = session.get(
        f"{GRAPH}/shares/{share_id(url)}/driveItem",
        headers={"Prefer": "redeemSharingLink"},
    )
    if response.status_code in (400, 404):
        raise UserError(
            "This link doesn't open a OneDrive shared folder.",
            "Copy the folder's share link again; it may have been removed.",
        )
    response.raise_for_status()
    root = response.json()
    if "folder" not in root:
        raise UserError(
            "The link opens a file, not a folder.",
            "Share the folder that holds the songs.",
        )
    return root


def find_subfolder(
    session: requests.Session, drive_id: str, root: dict[str, Any], name: str
) -> dict[str, Any]:
    """The top-level folder `name` inside the share (any case), or the share itself."""
    if not name:
        return root
    top_level = list_children(session, drive_id, root["id"])
    wanted = name.casefold()
    found = next(
        (i for i in top_level if "folder" in i and i["name"].casefold() == wanted),
        None,
    )
    if not found:
        names = ", ".join(i["name"] for i in top_level if "folder" in i)
        raise UserError(
            f"No folder '{name}' in the shared folder.", f"Folders found: {names}"
        )
    return found
