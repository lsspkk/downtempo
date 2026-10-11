"""Request failures in plain words, shared by the providers and `sync.py`."""

import requests

from downtempo.errors import UserError


def request_error(error: requests.RequestException) -> UserError:
    """A failed request as the user should read it: what happened and what to do."""
    match error:
        case requests.ConnectionError():
            return UserError(
                "No internet connection.",
                "Your downloaded songs still work. Check the connection and try again.",
            )
        case requests.Timeout():
            return UserError(
                "The server took too long to answer.", "Try again in a moment."
            )
        case requests.HTTPError(response=response) if response is not None:
            code = response.status_code
            if code == 401:
                return UserError("The sign-in was not accepted.", "Sign in again.")
            if code == 403:
                return UserError(
                    "The folder can't be opened: the link may have expired, or your account lacks access.",
                    "Ask for a new link.",
                )
            if code == 404:
                return UserError(
                    "The folder can't be found: it may have been moved, or the link removed.",
                    "Ask for a new link.",
                )
            if code == 429 or code >= 500:
                return UserError(
                    f"The server is busy or failing (HTTP {code}).", "Try again later."
                )
            return UserError(f"The server refused the request (HTTP {code}).")
    return UserError(f"The download failed: {error}")
