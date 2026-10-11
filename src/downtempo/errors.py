"""Failures the user can act on (a plain message and what to do), and a cancel by the user."""


class UserError(Exception):
    """Raised by the core for anything the user should read; frontends show `message` and `hint`."""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        return f"{self.message} {self.hint}".strip()


class Cancelled(Exception):
    """The user stopped the work; nothing to show, finished files are kept."""
