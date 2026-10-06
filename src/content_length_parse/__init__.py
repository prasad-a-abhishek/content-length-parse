"""RFC 9110 §8.6 Content-Length parser — zero-dependency, typed.

Public API::

    from content_length_parse import (
        parse,            # str | bytes -> int
        parse_safe,       # str | bytes -> int | None
        format_length,    # int -> str
        ContentLengthError,
        __version__,
    )
"""

from __future__ import annotations

from ._errors import ContentLengthError
from ._format import format_length
from ._parser import parse, parse_safe

__version__ = "0.1.0"

__all__ = [
    "parse",
    "parse_safe",
    "format_length",
    "ContentLengthError",
    "__version__",
]
