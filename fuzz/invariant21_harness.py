"""Fuzz harness for surface 4: invariant21 (all 4 public symbols with hostile inputs).

Per Invariant 21 in the repo-factory contract, public top-level functions MUST
be total over arbitrary input. None / float / bool / list / dict / object() /
complex must NEVER raise uncaught TypeError/ValueError/AttributeError — they
must return structured ContentLengthError (a ValueError subclass).

A "crash" here is any exception that is NOT ContentLengthError.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from content_length_parse import (  # noqa: E402
    format_length,
    parse,
    parse_safe,
)

from fuzz._common import (  # noqa: E402
    parse_harness_args,
    random_hostile_obj,
    run_harness,
)


# A small fixed menu of explicitly hostile inputs that exercise every type bucket.
EXPLICIT_HOSTILE: list = [
    None,
    -1,
    3.14,
    True,
    False,
    [],
    {},
    b"",
    "?",
    " 42",
    "+42",
    "-0",
    "0042",
    "\x00",
    b"\xff",
    object(),
    complex(1, 0),
    (1,),
    float("inf"),
    float("nan"),
    b"\x00\x01\x02",
    "٠",  # Arabic-Indic zero
    "４",  # fullwidth 4
    "²",  # superscript 2
    " " * 1000,
    "0" * 1000000,  # 10^6 digit overflow
    2**63,
    -(2**63),
]


def _all_symbols_stream(rng, n):
    """Yield (symbol, payload) pairs by cycling through the public API."""
    symbols = [parse, parse_safe, format_length]
    pool = list(EXPLICIT_HOSTILE)
    for _ in range(n):
        for sym in symbols:
            # Mix fixed hostile inputs with random hostile objects.
            if rng.random() < 0.5:
                yield (sym, pool[rng.randrange(len(pool))])
            else:
                yield (sym, random_hostile_obj(rng))


def main() -> int:
    args = parse_harness_args(default_iters=5000)

    def _driver(payload):
        sym, val = payload
        return sym(val)

    summary = run_harness(
        surface="invariant21",
        fn=_driver,
        inputs=_all_symbols_stream,
        iters=args.iters,
        seed=args.seed,
        timeout_s=args.timeout,
    )
    print(summary)
    return 0 if summary["crashes"] == 0 and summary["hangs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
