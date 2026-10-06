"""Shared harness utilities: random input generation, crash capture, hang timeout.

Pure stdlib only. No atheris / hypothesis / libFuzzer.
"""
from __future__ import annotations

import argparse
import os
import random
import signal
import string
import sys
import threading
import traceback
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, cast

# Locate the package: fuzz/ lives at <repo>/fuzz/, so the repo root is parent.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_CRASHES_DIR = Path(__file__).resolve().parent / "crashes"
_LOGS_DIR = Path(__file__).resolve().parent / "logs"


# ---------------------------------------------------------------------------
# Crash / hang infrastructure
# ---------------------------------------------------------------------------


class _HangError(Exception):
    """Raised when a fuzz call exceeds the timeout budget."""


def _hang_watchdog(seconds: float, container: list) -> None:
    """Threaded timer that fires _HangError into `container[0]` after `seconds`."""
    def _fire() -> None:
        if not container:
            return
        container[0] = _HangError(f"call exceeded {seconds}s")

    t = threading.Timer(seconds, _fire)
    t.daemon = True
    t.start()


def call_with_timeout(
    fn: Callable[..., Any],
    args: tuple,
    kwargs: dict,
    seconds: float,
) -> Any:
    """Invoke ``fn(*args, **kwargs)``; raise _HangError after ``seconds`` if it stalls.

    Uses a background thread + sentinel pattern so it works even on platforms
    that swallow SIGALRM (e.g. background worker threads).
    """
    result: list = [None]
    error: list = [None]

    def _runner() -> None:
        try:
            result[0] = fn(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 — fuzz harness catches all
            error[0] = exc

    th = threading.Thread(target=_runner, daemon=True)
    th.start()
    th.join(timeout=seconds)
    if th.is_alive():
        # Can't actually kill the thread, but we stop waiting.
        raise _HangError(f"call exceeded {seconds}s (thread still running)")
    if error[0] is not None:
        raise error[0]
    return result[0]


def record_crash(
    surface: str,
    iter_idx: int,
    payload: Any,
    exc: BaseException,
    tb_text: str,
) -> Path:
    """Write the offending input and stack trace to fuzz/crashes/.

    Returns the directory path created.
    """
    _CRASHES_DIR.mkdir(parents=True, exist_ok=True)
    safe_tag = "".join(c if c.isalnum() else "_" for c in surface)
    in_path = _CRASHES_DIR / f"{safe_tag}_{iter_idx:06d}.in"
    stack_path = _CRASHES_DIR / f"{safe_tag}_{iter_idx:06d}.stack.txt"

    # Serialize payload. bytes -> latin-1 preserves bytes; everything else via repr.
    try:
        if isinstance(payload, bytes):
            in_path.write_bytes(payload)
        else:
            in_path.write_text(repr(payload))
    except Exception:
        in_path.write_text(f"<unserializable payload of type {type(payload).__name__}>")

    stack_path.write_text(
        f"surface: {surface}\n"
        f"iter:    {iter_idx}\n"
        f"type:    {type(exc).__name__}\n"
        f"exc:     {exc!r}\n"
        f"--- traceback ---\n{tb_text}\n"
    )
    return _CRASHES_DIR


# ---------------------------------------------------------------------------
# Random input generators
# ---------------------------------------------------------------------------


# Pool of digit characters used to build decimal strings of various flavors.
_DIGITS = "0123456789"


def random_decimal_str(rng: random.Random, max_len: int = 64) -> str:
    """A random decimal-looking string, possibly with leading zeros / sign / ws."""
    # 30% chance to lead with a sign
    sign = ""
    if rng.random() < 0.30:
        sign = rng.choice(["+", "-"])

    # 20% chance to lead with zero-padded
    pad = ""
    if rng.random() < 0.20:
        pad = "0" * rng.randint(1, 5)

    # Core: random digits of length 0..max_len
    n_digits = rng.randint(0, max_len)
    core = "".join(rng.choice(_DIGITS) for _ in range(n_digits))

    # 15% chance to inject trailing/leading/internal whitespace
    body = sign + pad + core
    if rng.random() < 0.15:
        ws = rng.choice([" ", "\t", "\n", "\r", "\r\n"])
        where = rng.choice(["lead", "trail", "both"])
        if where == "lead":
            body = ws + body
        elif where == "trail":
            body = body + ws
        else:
            body = ws + body + ws

    return body


def random_bytes(rng: random.Random, max_len: int = 64) -> bytes:
    """A random byte string up to max_len, possibly full non-ASCII range."""
    n = rng.randint(0, max_len)
    return bytes(rng.randint(0, 255) for _ in range(n))


def random_non_ascii_str(rng: random.Random, max_len: int = 16) -> str:
    """Strings containing exotic Unicode digit characters (Arabic-Indic, fullwidth)."""
    exotic = list("٤٢١٠４２１０²³¹⁰⁰⁰")
    n = rng.randint(1, max_len)
    return "".join(rng.choice(exotic) for _ in range(n))


def random_hostile_obj(rng: random.Random) -> Any:
    """Hostile non-str/bytes object: None, int, float, bool, list, dict, object, ..."""
    choices: list = [
        None,
        -1,
        0,
        1,
        2**63,
        3.14,
        True,
        False,
        [],
        [1, 2, 3],
        {},
        {"x": 1},
        object(),
        (1,),
        complex(1, 0),
        b"",
        " 42",
        "+42",
        "-0",
        "0042",
        "\x00",
        b"\xff",
    ]
    return rng.choice(choices)


def gen_parse_input(rng: random.Random) -> Any:
    """60% random decimal str / 30% random bytes / 10% non-ASCII str."""
    r = rng.random()
    if r < 0.60:
        return random_decimal_str(rng)
    if r < 0.90:
        return random_bytes(rng)
    return random_non_ascii_str(rng)


def parse_input_stream(rng: random.Random, n: int) -> Iterable[Any]:
    """Yield `n` independent parse inputs, seeded by `rng`."""
    for _ in range(n):
        yield gen_parse_input(rng)


def gen_format_input(rng: random.Random) -> Any:
    """40% power-of-two int / 30% other int / 20% hostile non-int / 10% bool."""
    r = rng.random()
    if r < 0.40:
        return rng.choice([0, 1, 2**8, 2**16, 2**32, 2**63 - 1, 2**63, 2**64, 2**100, 2**1024])
    if r < 0.70:
        return rng.randint(-(2**10), 2**100)
    if r < 0.90:
        return random_hostile_obj(rng)
    return rng.choice([True, False])


def format_input_stream(rng: random.Random, n: int) -> Iterable[Any]:
    """Yield `n` independent format inputs, seeded by `rng`."""
    for _ in range(n):
        yield gen_format_input(rng)


# ---------------------------------------------------------------------------
# Driver loop
# ---------------------------------------------------------------------------


def run_harness(
    surface: str,
    fn: Callable[[Any], Any],
    inputs: Any,
    iters: int,
    seed: int,
    timeout_s: float = 5.0,
) -> dict:
    """Run ``fn(input)`` for each of ``iters`` inputs, recording any crash/hang.

    ``inputs`` may be either:
      * an Iterable[Any] of pre-built payloads, or
      * a Callable[[random.Random, int], Iterable[Any]] factory that takes
        (rng, iters) and yields exactly ``iters`` payloads.

    Returns a dict with counters and the crash directory (if any).
    """
    rng = random.Random(seed)
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _LOGS_DIR / f"run_{surface}.log"
    log_lines: list = []

    crashes = 0
    hangs = 0
    ok = 0
    raised_expected = 0  # ContentLengthError is the *expected* failure mode

    # Materialize inputs into a list so we can index by i (callable factories
    # produce generators that don't support indexing).
    if callable(inputs):
        built = list(inputs(rng, iters))
    else:
        # `inputs` is a pre-built Iterable (callable branch handled above).
        built = list(cast(Iterable[Any], inputs))  # type: ignore[arg-type]

    for i in range(iters):
        payload = built[i]
        try:
            call_with_timeout(fn, (payload,), {}, seconds=timeout_s)
            ok += 1
        except _HangError as exc:
            hangs += 1
            tb = traceback.format_exc()
            record_crash(surface, i, payload, exc, tb)
            log_lines.append(f"[{i}] HANG payload={payload!r}")
        except Exception as exc:  # noqa: BLE001
            # ContentLengthError is the contract — count as expected, not crash.
            if exc.__class__.__name__ == "ContentLengthError":
                raised_expected += 1
            else:
                crashes += 1
                tb = traceback.format_exc()
                record_crash(surface, i, payload, exc, tb)
                log_lines.append(f"[{i}] CRASH {type(exc).__name__}: {exc!r} payload={payload!r}")

    summary = {
        "surface": surface,
        "iters": iters,
        "ok": ok,
        "expected_errors": raised_expected,
        "crashes": crashes,
        "hangs": hangs,
    }
    log_path.write_text(
        "\n".join(log_lines)
        + "\n--- summary ---\n"
        + "\n".join(f"{k}: {v}" for k, v in summary.items())
        + "\n"
    )
    return summary


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def parse_harness_args(default_iters: int = 5000) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fuzz harness for content-length-parse")
    p.add_argument("--iters", type=int, default=default_iters, help="iterations")
    p.add_argument("--seed", type=int, default=42, help="PRNG seed for reproducibility")
    p.add_argument("--timeout", type=float, default=5.0, help="per-call timeout (s)")
    return p.parse_args()
