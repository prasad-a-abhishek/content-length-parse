"""Round-trip tests: parse(format(n)) == n for all valid n (AC-12)."""

import pytest
from content_length_parse import parse, format_length


class TestRoundtrip:
    """AC-12: round-trip for a wide range of valid values."""

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
            9999,
            99999,
            999999,
            9999999,
            99999999,
            999999999,
            9999999999,
            99999999999,
            999999999999,
            9999999999999,
            99999999999999,
            999999999999999,
            9999999999999999,
            99999999999999999,
            999999999999999999,
            9223372036854775807,  # max int64
        ],
    )
    def test_roundtrip_via_str(self, n: int) -> None:
        """AC-12: parse(format_length(n)) == n."""
        encoded = format_length(n)
        decoded = parse(encoded)
        assert decoded == n, f"round-trip failed for n={n}: got {decoded}"

    def test_roundtrip_max_boundary(self) -> None:
        """2^63-1 (max) round-trips exactly."""
        n = 9223372036854775807
        assert parse(format_length(n)) == n

    def test_roundtrip_min(self) -> None:
        """0 round-trips correctly."""
        assert parse(format_length(0)) == 0

    def test_roundtrip_one(self) -> None:
        """1 round-trips correctly."""
        assert parse(format_length(1)) == 1
