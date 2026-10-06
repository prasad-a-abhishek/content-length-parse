"""RFC 9110 §8.6 Content-Length parser: parse() and parse_safe()."""

from __future__ import annotations

from typing import Union

from ._errors import ContentLengthError

__all__ = ["parse", "parse_safe"]

# Maximum representable value: 2^63 - 1 (matches common server limits)
_MAX = 2**63 - 1

# ASCII digit range
_ASCII_0 = ord("0")
_ASCII_9 = ord("9")


def parse(value: Union[str, bytes]) -> int:
    """Parse a Content-Length field value per RFC 9110 §8.6.

    Args:
        value: The field value as str or bytes (ASCII-encoded).

    Returns:
        The integer Content-Length value.

    Raises:
        ContentLengthError: If the value is empty, has leading zeros,
            contains non-ASCII digits, has internal/trailing whitespace,
            is negative, or overflows 2^63-1.
        TypeError: If value is not a str or bytes instance
            (wrapped as ContentLengthError per Invariant 21).

    Grammar: Content-Length = 1*DIGIT  (DIGIT = %x30-39)
    """
    if not isinstance(value, (str, bytes)):
        raise ContentLengthError(
            f"expected str or bytes, got {type(value).__name__}"
        )

    if isinstance(value, bytes):
        try:
            decoded = value.decode("ascii")
        except UnicodeDecodeError:
            raise ContentLengthError(
                "bytes value is not valid ASCII"
            ) from None
        return _parse_str(decoded)

    return _parse_str(value)


def _parse_str(s: str) -> int:
    """Parse a str Content-Length value.

    Raises ContentLengthError on any invalid input per RFC 9110 §8.6.
    """
    if not s:
        raise ContentLengthError("empty value")

    n = len(s)

    # Check each character is an ASCII digit; accumulate value.
    acc = 0
    for i, ch in enumerate(s):
        c = ord(ch)
        if _ASCII_0 <= c <= _ASCII_9:
            acc = acc * 10 + (c - _ASCII_0)
            if acc > _MAX:
                raise ContentLengthError(f"overflow at position {i}")
        else:
            raise ContentLengthError(
                f"invalid character at position {i}: {ch!r}"
            )

    # Reject leading zero (e.g. "0042") — 1*DIGIT requires no leading zero
    # unless the value is exactly "0" (single digit zero).
    if n > 1 and s[0] == "0":
        raise ContentLengthError("leading zero at position 0")

    return acc


def parse_safe(value: Union[str, bytes]) -> Union[int, None]:
    """Parse a Content-Length value, returning None instead of raising.

    This is the non-strict variant: any failure (empty, leading zero,
    non-ASCII digit, overflow, type mismatch) returns None instead of
    raising ContentLengthError.

    Args:
        value: The field value as str or bytes (ASCII-encoded).

    Returns:
        The integer Content-Length value, or None if parsing fails.
    """
    try:
        return parse(value)
    except ContentLengthError:
        return None
