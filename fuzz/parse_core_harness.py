"""Fuzz harness for surface 1: parse_core (strict parse()).

Pure stdlib. The crash budget is: any uncaught exception other than
ContentLengthError, or any hang > --timeout seconds.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path so we can import the package being fuzzed.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content_length_parse import parse  # noqa: E402

from fuzz._common import (  # noqa: E402
    parse_harness_args,
    parse_input_stream,
    run_harness,
)


def main() -> int:
    args = parse_harness_args(default_iters=5000)
    summary = run_harness(
        surface="parse_core",
        fn=parse,
        inputs=parse_input_stream,
        iters=args.iters,
        seed=args.seed,
        timeout_s=args.timeout,
    )
    print(summary)
    # Exit 0 if no crashes/hangs; non-zero otherwise so CI can gate on it.
    return 0 if summary["crashes"] == 0 and summary["hangs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
