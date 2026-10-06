"""Shared pytest fixtures for content_length_parse tests."""

import pytest
from typing import Union


@pytest.fixture(params=["str", "bytes"])
def str_bytes(request: pytest.FixtureRequest) -> Union[str, bytes]:
    """Fixture that yields both str and bytes representations of test values.

    Use with ``parametrize("@str_bytes", [(value,)])`` to run the same
    test case against both str and bytes input.
    """
    if request.param == "str":
        return "42"
    else:
        return b"42"
