"""format_length tests (AC-11 through AC-13)."""

import pytest
from content_length_parse import format_length, parse, ContentLengthError


class TestFormatLength:
    """AC-11: format_length returns canonical decimal string."""

    def test_format_length_42(self) -> None:
        """AC-11: format_length(42) returns "42"."""
        assert format_length(42) == "42"

    def test_format_length_zero(self) -> None:
        """AC-11: format_length(0) returns "0"."""
        assert format_length(0) == "0"

    def test_format_length_1(self) -> None:
        assert format_length(1) == "1"

    def test_format_length_100(self) -> None:
        assert format_length(100) == "100"

    def test_format_length_large(self) -> None:
        """A large value encodes correctly."""
        val = 9223372036854775807
        assert format_length(val) == "9223372036854775807"

    def test_format_length_no_padding(self) -> None:
        """No leading zeros in output."""
        assert format_length(7) == "7"
        assert format_length(0) == "0"

    def test_format_length_all_nines(self) -> None:
        """All 19-digit number works."""
        val = 999999999999999999
        assert format_length(val) == "999999999999999999"


class TestFormatLengthErrors:
    """format_length raises ContentLengthError on invalid inputs."""

    def test_format_length_negative(self) -> None:
        """Negative values raise ContentLengthError."""
        with pytest.raises(ContentLengthError) as exc_info:
            format_length(-1)
        assert "negative" in str(exc_info.value)

    def test_format_length_overflow(self) -> None:
        """Values > 2^63-1 raise ContentLengthError."""
        with pytest.raises(ContentLengthError) as exc_info:
            format_length(2**63)
        assert "overflow" in str(exc_info.value)

    def test_format_length_type_error_int_subclass(self) -> None:
        """bool is an int subclass, but format_length(bool) raises."""
        with pytest.raises(ContentLengthError):
            format_length(True)  # type: ignore[arg-type]


class TestRoundTrip:
    """AC-12: round-trip parse(format(n)) == n for valid n."""

    @pytest.mark.parametrize(
        "n",
        [
            0,
            1,
            10,
            42,
            100,
            999,
            2**53 - 1,
            2**53,
            1000,
            999999999999999999,
        ],
    )
    def test_roundtrip(self, n: int) -> None:
        """AC-12: parse(format(n)) == n for every valid n."""
        encoded = format_length(n)
        decoded = parse(encoded)
        assert decoded == n, f"round-trip failed for {n}"

    def test_roundtrip_max(self) -> None:
        """2^63 - 1 round-trips correctly."""
        n = 9223372036854775807
        assert parse(format_length(n)) == n
