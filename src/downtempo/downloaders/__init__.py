"""Downloaders by source type. Each one fetches a `Source` into `source.target`, reports
events instead of printing and raises `UserError` for anything the user should read."""

from collections.abc import Callable

from downtempo.config import Source
from downtempo.downloaders import onedrive
from downtempo.events import Report

DOWNLOADERS: dict[str, Callable[[Source, Report], None]] = {
    "onedrive": onedrive.download,
}
