"""Spec test vectors end-to-end (VEC-01 through VEC-10).

These reference the 10 vectors in spec §6 verbatim.
"""

import pytest
from content_length_parse import parse, ContentLengthError


class TestVectors:
    """10 spec test vectors from spec §6."""

    def test_vec_01_zero_valid(self) -> None:
        """VEC-01: "0" -> 0 (RFC 9110 §8.6 — zero is valid)."""
        assert parse("0") == 0

    def test_vec_02_42_valid(self) -> None:
        """VEC-02: "42" -> 42 (RFC 9110 §8.6 + MDN example)."""
        assert parse("42") == 42

    def test_vec_03_bytes(self) -> None:
        """VEC-03: b"42" -> 42 (bytes decoded as ASCII)."""
        assert parse(b"42") == 42

    def test_vec_04_leading_zero_rejected(self) -> None:
        """VEC-04: "0042" raises (leading zero, RFC 9110 §8.6)."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse("0042")
        assert "leading zero" in str(exc_info.value)

    def test_vec_05_negative_rejected(self) -> None:
        """VEC-05: "-1" raises (unsigned octet count, RFC 9110 §8.6)."""
        with pytest.raises(ContentLengthError):
            parse("-1")

    def test_vec_06_empty_rejected(self) -> None:
        """VEC-06: "" raises (1*DIGIT requires ≥1 digit)."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse("")
        assert "empty" in str(exc_info.value)

    def test_vec_07_whitespace_rejected(self) -> None:
        """VEC-07: "  42  " raises (field-value is raw octets, no stripping)."""
        with pytest.raises(ContentLengthError):
            parse("  42  ")

    def test_vec_08_non_ascii_rejected(self) -> None:
        """VEC-08: "٤٢" raises (non-ASCII digits, RFC 9110 §5.5)."""
        with pytest.raises(ContentLengthError):
            parse("٤٢")

    def test_vec_09_crlf_rejected(self) -> None:
        """VEC-09: "42\\n" raises (line endings are message-level, not field-level)."""
        with pytest.raises(ContentLengthError):
            parse("42\n")

    def test_vec_10_overflow_rejected(self) -> None:
        """VEC-10: "1"*20 raises (overflow > 2^63, practical server limit)."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse("1" * 20)
        assert "overflow" in str(exc_info.value)
