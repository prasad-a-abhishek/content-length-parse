"""ContentLengthError: structured error for Content-Length parsing."""

from __future__ import annotations


class ContentLengthError(ValueError):
    """Raised when a Content-Length value cannot be parsed per RFC 9110 §8.6.

    The message encodes the failure reason. When the input is a str or bytes
    and the failure is at a specific character position, the message includes
    ``{position}`` so callers can locate the invalid byte.

    Subclass of ``ValueError`` so callers that only need a boolean can use
    ``except ValueError`` and still catch this.
    """

    __slots__ = ()

    def __init__(self, message: str) -> None:
        super().__init__(message)
