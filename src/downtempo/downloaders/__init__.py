"""Providers by source type. Each one signs in, opens a share link and lists its folders and
files (`remote.py`); `sync.py` downloads. A new provider = one module + one line here + one doc."""

from downtempo.downloaders.onedrive import OneDrive
from downtempo.downloaders.remote import Provider
from downtempo.errors import UserError

PROVIDERS: list[Provider] = [OneDrive()]


def provider_for(url: str) -> Provider | None:
    """The provider whose link this is; no network."""
    return next((p for p in PROVIDERS if p.owns(url)), None)


def provider(type: str) -> Provider:
    """The provider of a source's `type`."""
    for found in PROVIDERS:
        if found.type == type:
            return found
    known = ", ".join(p.type for p in PROVIDERS)
    raise UserError(f"Unknown source type '{type}'.", f"Known types: {known}.")


def unknown_link() -> UserError:
    labels = " or ".join(p.label for p in PROVIDERS)
    return UserError(
        f"This link isn't a {labels} shared folder.",
        f"Open the folder in {labels}, press Share, copy the link and paste it here.",
    )
