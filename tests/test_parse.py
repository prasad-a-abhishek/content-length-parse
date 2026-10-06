"""Parse happy-path and basic rejection tests (AC-1 through AC-6)."""

import pytest
from content_length_parse import parse, ContentLengthError


class TestParseHappyPath:
    """AC-1, AC-2, AC-3: valid inputs return the correct integer."""

    def test_parse_zero(self) -> None:
        """AC-1: parse("0") returns 0."""
        assert parse("0") == 0

    def test_parse_basic(self) -> None:
        """AC-2: parse("42") returns 42."""
        assert parse("42") == 42

    def test_parse_bytes(self) -> None:
        """AC-3: parse(b"42") returns 42."""
        assert parse(b"42") == 42

    def test_parse_single_digit_all(self) -> None:
        """Every single digit 0-9 parses to itself."""
        for d in range(10):
            assert parse(str(d)) == d

    def test_parse_large_value(self) -> None:
        """A large but valid Content-Length value parses correctly."""
        assert parse("9223372036854775807") == 9223372036854775807

    def test_parse_1(self) -> None:
        assert parse("1") == 1

    def test_parse_100(self) -> None:
        assert parse("100") == 100

    def test_parse_999(self) -> None:
        assert parse("999") == 999

    def test_parse_bytes_zero(self) -> None:
        """parse(b"0") returns 0."""
        assert parse(b"0") == 0

    def test_parse_bytes_large(self) -> None:
        """parse(b"1234567890") returns the correct integer."""
        assert parse(b"1234567890") == 1234567890


class TestParseRejection:
    """AC-4, AC-5, AC-6: invalid inputs raise ContentLengthError."""

    def test_parse_leading_zero(self) -> None:
        """AC-4: parse("0042") raises ContentLengthError (leading zero)."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse("0042")
        assert "leading zero" in str(exc_info.value)

    def test_parse_negative(self) -> None:
        """AC-5: parse("-1") raises ContentLengthError (negative)."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse("-1")
        assert "invalid character" in str(exc_info.value) or "position" in str(exc_info.value)

    def test_parse_empty(self) -> None:
        """AC-6: parse("") raises ContentLengthError (empty)."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse("")
        assert "empty" in str(exc_info.value)

    def test_parse_leading_zero_single_zero_ok(self) -> None:
        """The single digit "0" is valid (not a leading zero)."""
        assert parse("0") == 0

    def test_parse_leading_zero_00_rejected(self) -> None:
        """parse("00") is rejected (two-digit zero is a leading zero)."""
        with pytest.raises(ContentLengthError):
            parse("00")

    def test_parse_leading_zero_000_rejected(self) -> None:
        """parse("000") is rejected."""
        with pytest.raises(ContentLengthError):
            parse("000")

    def test_parse_042_rejected(self) -> None:
        """parse("042") is rejected (leading zero on non-zero value)."""
        with pytest.raises(ContentLengthError):
            parse("042")
