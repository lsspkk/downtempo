"""Failures the user can act on: a plain message and what to do about it."""


class UserError(Exception):
    """Raised by the core for anything the user should read; frontends show `message` and `hint`."""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        return f"{self.message} {self.hint}".strip()
