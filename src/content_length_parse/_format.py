"""Integer-to-decimal encoder for Content-Length: format_length()."""

from __future__ import annotations

from ._errors import ContentLengthError

__all__ = ["format_length"]

_MAX = 2**63 - 1


def format_length(n: int) -> str:
    """Encode an integer as a canonical Content-Length decimal string.

    The canonical form is the plain decimal representation with no padding,
    no sign, and no leading zeros.

    Args:
        n: An integer Content-Length value.

    Returns:
        The decimal string representation.

    Raises:
        ContentLengthError: If ``n`` is negative or exceeds 2**63-1.

    Examples::
        >>> format_length(42)
        '42'
        >>> format_length(0)
        '0'
    """
    # bool is a subclass of int — reject it specifically first
    if isinstance(n, bool):
        raise ContentLengthError(
            f"expected int, got {type(n).__name__}"
        )
    if not isinstance(n, int):
        raise ContentLengthError(
            f"expected int, got {type(n).__name__}"
        )
    if n < 0:
        raise ContentLengthError("negative value")
    # Reject -0: in Python -0 == 0 but we treat it as invalid per RFC 9110
    if n == 0 and str(n) == "-0":
        raise ContentLengthError("negative value")
    if n > _MAX:
        raise ContentLengthError("overflow")

    return str(n)
