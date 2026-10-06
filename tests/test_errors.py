"""ContentLengthError shape and message tests (AC-13, AC-14)."""

import pytest
from content_length_parse import parse, parse_safe, ContentLengthError


class TestErrorClass:
    """AC-13: ContentLengthError is a subclass of ValueError."""

    def test_is_subclass_of_value_error(self) -> None:
        """AC-13: ContentLengthError is a subclass of ValueError."""
        assert issubclass(ContentLengthError, ValueError)

    def test_is_instance_of_value_error(self) -> None:
        """ContentLengthError instance is also a ValueError instance."""
        err = ContentLengthError("test")
        assert isinstance(err, ValueError)

    def test_error_message(self) -> None:
        """Error carries the expected message."""
        err = ContentLengthError("empty value")
        assert str(err) == "empty value"

    def test_error_message_unicode(self) -> None:
        """Error message can contain unicode."""
        err = ContentLengthError("invalid character at position 0: '+'")
        assert "'" in str(err)


class TestTypeMismatch:
    """AC-14: parse(None) and parse(42) raise ContentLengthError (type-mismatch)."""

    def test_parse_none(self) -> None:
        """AC-14: parse(None) raises ContentLengthError."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse(None)  # type: ignore[arg-type]
        assert "NoneType" in str(exc_info.value)

    def test_parse_int(self) -> None:
        """AC-14: parse(42) raises ContentLengthError."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse(42)  # type: ignore[arg-type]
        assert "int" in str(exc_info.value)

    def test_parse_list(self) -> None:
        """AC-14: parse(["42"]) raises ContentLengthError."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse(["42"])  # type: ignore[arg-type]
        assert "list" in str(exc_info.value)

    def test_parse_dict(self) -> None:
        """parse({}) raises ContentLengthError."""
        with pytest.raises(ContentLengthError) as exc_info:
            parse({})  # type: ignore[arg-type]
        assert "dict" in str(exc_info.value)

    def test_parse_float(self) -> None:
        """parse(42.0) raises ContentLengthError."""
        with pytest.raises(ContentLengthError):
            parse(42.0)  # type: ignore[arg-type]

    def test_parse_bytes_non_ascii(self) -> None:
        """Non-ASCII bytes raise ContentLengthError."""
        with pytest.raises(ContentLengthError):
            parse(b"4\xff2")


class TestInvariant21:
    """Invariant 21: public APIs are total — never raise uncaught TypeError/ValueError."""

    @pytest.mark.parametrize(
        "value",
        [
            None,
            42,
            ["42"],
            {"42": 42},
            42.0,
            b"abc",
            "",
            " 42",
            "+42",
            "-0",
        ],
    )
    def test_parse_total_over_invalid_inputs(self, value: object) -> None:
        """parse raises ContentLengthError, NOT bare TypeError/ValueError."""
        try:
            parse(value)  # type: ignore[arg-type]
            pytest.fail(f"parse({value!r}) should have raised ContentLengthError")
        except ContentLengthError:
            pass  # correct
        except (TypeError, ValueError) as e:
            pytest.fail(
                f"parse({value!r}) raised {type(e).__name__} instead of ContentLengthError: {e}"
            )

    @pytest.mark.parametrize(
        "value",
        [
            None,
            42,
            ["42"],
            {"42": 42},
            42.0,
        ],
    )
    def test_parse_safe_total_over_invalid_inputs(self, value: object) -> None:
        """parse_safe returns None (never raises) for all invalid inputs."""
        result = parse_safe(value)  # type: ignore[arg-type]
        assert result is None
