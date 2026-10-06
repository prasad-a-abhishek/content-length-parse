"""Strict rejection tests — whitespace, non-ASCII, overflow (AC-7 through AC-10)."""

import pytest
from content_length_parse import parse, parse_safe, ContentLengthError


class TestWhitespaceRejection:
    """AC-7: whitespace (leading, trailing, internal) raises ContentLengthError."""

    def test_parse_whitespace_leading(self) -> None:
        """AC-7: parse("  42  ") raises — leading whitespace not allowed."""
        with pytest.raises(ContentLengthError):
            parse("  42")

    def test_parse_whitespace_trailing(self) -> None:
        """Trailing space raises."""
        with pytest.raises(ContentLengthError):
            parse("42 ")

    def test_parse_whitespace_both(self) -> None:
        """parse("  42  ") raises on leading whitespace."""
        with pytest.raises(ContentLengthError):
            parse("  42  ")

    def test_parse_whitespace_tab(self) -> None:
        """Horizontal tab inside value raises."""
        with pytest.raises(ContentLengthError):
            parse("4\t2")

    def test_parse_whitespace_internal(self) -> None:
        """Internal space raises: "4 2"."""
        with pytest.raises(ContentLengthError):
            parse("4 2")

    def test_parse_newline(self) -> None:
        """AC-9 / VEC-09: trailing CRLF raises."""
        with pytest.raises(ContentLengthError):
            parse("42\n")

    def test_parse_crlf(self) -> None:
        """Trailing CRLF raises."""
        with pytest.raises(ContentLengthError):
            parse("42\r\n")

    def test_parse_carriage_return_only(self) -> None:
        """Carriage return without newline raises."""
        with pytest.raises(ContentLengthError):
            parse("42\r")


class TestNonAsciiDigitRejection:
    """AC-8: non-ASCII digits raise ContentLengthError."""

    def test_parse_non_ascii(self) -> None:
        """AC-8: Arabic-Indic digits raise."""
        with pytest.raises(ContentLengthError):
            parse("٤٢")  # Arabic-Indic 4 and 2

    def test_parse_non_ascii_eastern(self) -> None:
        """Fullwidth digits raise."""
        with pytest.raises(ContentLengthError):
            parse("\uff32\uff13")  # Fullwidth 2 and 3

    def test_parse_plus_sign(self) -> None:
        """AC-5 variant: leading + sign raises."""
        with pytest.raises(ContentLengthError):
            parse("+42")

    def test_parse_sign_only(self) -> None:
        """Just a plus sign raises."""
        with pytest.raises(ContentLengthError):
            parse("+")


class TestOverflowRejection:
    """AC-9: values exceeding 2^63-1 raise ContentLengthError."""

    def test_parse_overflow(self) -> None:
        """AC-9: parse("99999999999999999999999") raises (overflow)."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse("99999999999999999999999")
        assert "overflow" in str(exc_info.value)

    def test_parse_overflow_20_digits(self) -> None:
        """20-digit all-9 overflows 2^63-1."""
        val = "1" + "9" * 19  # 20 digits, clearly > 2^63
        with pytest.raises(ContentLengthError):
            parse(val)

    def test_parse_max_valid(self) -> None:
        """2^63 - 1 (max int64) is the largest valid value."""
        max_val = 9223372036854775807
        assert parse(str(max_val)) == max_val

    def test_parse_max_plus_one(self) -> None:
        """2^63 is the first overflow value."""
        with pytest.raises(ContentLengthError):
            parse("9223372036854775808")


class TestParseSafe:
    """AC-10: parse_safe returns None on failure, int on success."""

    def test_parse_safe_valid_str(self) -> None:
        """parse_safe("42") returns 42."""
        assert parse_safe("42") == 42

    def test_parse_safe_valid_bytes(self) -> None:
        """parse_safe(b"42") returns 42."""
        assert parse_safe(b"42") == 42

    def test_parse_safe_zero(self) -> None:
        """parse_safe("0") returns 0."""
        assert parse_safe("0") == 0

    def test_parse_safe_leading_zero(self) -> None:
        """parse_safe("0042") returns None."""
        assert parse_safe("0042") is None

    def test_parse_safe_negative(self) -> None:
        """parse_safe("-1") returns None."""
        assert parse_safe("-1") is None

    def test_parse_safe_empty(self) -> None:
        """parse_safe("") returns None."""
        assert parse_safe("") is None

    def test_parse_safe_whitespace(self) -> None:
        """parse_safe("  42  ") returns None."""
        assert parse_safe("  42  ") is None

    def test_parse_safe_non_ascii(self) -> None:
        """parse_safe("٤٢") returns None."""
        assert parse_safe("٤٢") is None

    def test_parse_safe_overflow(self) -> None:
        """parse_safe(overflow) returns None."""
        assert parse_safe("9" * 30) is None

    def test_parse_safe_type_error(self) -> None:
        """parse_safe(None) returns None (never raises)."""
        assert parse_safe(None) is None

    def test_parse_safe_int_input(self) -> None:
        """parse_safe(42) returns None (type error, not raised)."""
        assert parse_safe(42) is None

    def test_parse_safe_list_input(self) -> None:
        """parse_safe(["42"]) returns None."""
        assert parse_safe(["42"]) is None

    def test_parse_safe_bytes_non_ascii(self) -> None:
        """parse_safe with non-ASCII bytes returns None."""
        assert parse_safe(b"42\xff") is None
