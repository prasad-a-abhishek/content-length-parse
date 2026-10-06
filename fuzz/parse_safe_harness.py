"""Fuzz harness for surface 2: parse_safe_path (parse_safe()).

Invariant: parse_safe() MUST NEVER raise — it must return int or None for any
input. A crash here is a contract violation.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content_length_parse import parse_safe  # noqa: E402

from fuzz._common import (  # noqa: E402
    parse_harness_args,
    parse_input_stream,
    run_harness,
)


def main() -> int:
    args = parse_harness_args(default_iters=5000)
    summary = run_harness(
        surface="parse_safe_path",
        fn=parse_safe,
        inputs=parse_input_stream,
        iters=args.iters,
        seed=args.seed,
        timeout_s=args.timeout,
    )
    print(summary)
    # parse_safe is allowed to return None, so `ok` here means "returned without raising".
    # We treat any raise as a CRASH (parse_safe contract violation).
    # The driver already classifies ContentLengthError as "expected", but parse_safe
    # catches it internally, so under normal behavior it should never appear here.
    return 0 if summary["crashes"] == 0 and summary["hangs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
