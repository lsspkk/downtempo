"""Downloaders by source type. Each one fetches a `Source` into `source.target`."""

from collections.abc import Callable

from downtempo.config import Source
from downtempo.downloaders import onedrive

DOWNLOADERS: dict[str, Callable[[Source], None]] = {
    "onedrive": onedrive.download,
}
