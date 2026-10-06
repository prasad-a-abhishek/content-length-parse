"""Fuzz harness for surface 3: format_path (format_length()).

Random int inputs (including power-of-two boundary values) plus hostile non-int
inputs (None, float, bool, str). Expected error is ContentLengthError.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content_length_parse import format_length  # noqa: E402

from fuzz._common import (  # noqa: E402
    format_input_stream,
    parse_harness_args,
    run_harness,
)


def main() -> int:
    args = parse_harness_args(default_iters=5000)
    summary = run_harness(
        surface="format_path",
        fn=format_length,
        inputs=format_input_stream,
        iters=args.iters,
        seed=args.seed,
        timeout_s=args.timeout,
    )
    print(summary)
    return 0 if summary["crashes"] == 0 and summary["hangs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
