"""Typing / PEP 561 smoke tests (AC-15)."""

import os
import subprocess
import sys

import pytest

from content_length_parse import (
    parse,
    parse_safe,
    format_length,
    ContentLengthError,
    __version__,
)


class TestTypingSmoke:
    """AC-15: __version__, py.typed marker, mypy strict on init."""

    def test_version_is_str(self) -> None:
        """AC-15: __version__ is a str."""
        assert isinstance(__version__, str)
        assert __version__ == "0.1.0"

    def test_py_typed_marker_exists(self) -> None:
        """AC-15: py.typed marker is present in the package."""
        import content_length_parse
        pkg_dir = os.path.dirname(content_length_parse.__file__)
        marker = os.path.join(pkg_dir, "py.typed")
        assert os.path.isfile(marker)

    def test_parse_importable(self) -> None:
        """parse is importable from the package."""
        from content_length_parse import parse
        assert callable(parse)

    def test_parse_safe_importable(self) -> None:
        """parse_safe is importable from the package."""
        from content_length_parse import parse_safe
        assert callable(parse_safe)

    def test_format_length_importable(self) -> None:
        """format_length is importable from the package."""
        from content_length_parse import format_length
        assert callable(format_length)

    def test_content_length_error_importable(self) -> None:
        """ContentLengthError is importable."""
        from content_length_parse import ContentLengthError
        assert issubclass(ContentLengthError, ValueError)


class TestMypyStrict:
    """Run mypy --strict on the package to verify type correctness (AC-15)."""

    def test_mypy_strict_on_init(self) -> None:
        """mypy --strict passes on __init__.py (AC-15)."""
        import content_length_parse
        init_path = os.path.join(os.path.dirname(content_length_parse.__file__), "__init__.py")
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", init_path],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"mypy --strict failed:\n{result.stdout}\n{result.stderr}"
