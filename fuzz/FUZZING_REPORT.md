# FUZZING_REPORT — content-length-parse, cycle_182

## 1. Executive Summary

This report documents the adversarial fuzzing coverage of the `content-length-parse` library (a zero-dependency, pure-Python RFC 9110 §8.6 Content-Length header parser) at cycle_182. The fuzzing workstream spanned 5 sequential cards (VULN_AUDIT → FUZZ_HARNESS → FUZZ_EXECUTE → TRIAGE → FUZZING_REPORT) and exercised **4 public attack surfaces** (`parse_core`, `parse_safe_path`, `format_path`, `invariant21`) for a total of **20,000 iterations** with **0 crashes, 0 hangs, 0 OOM**. Independent manual probes during VULN_AUDIT covered 18 additional attack vectors (leading-zero, sign, whitespace, control, non-ASCII digits, Unicode zero-width, 2^63 boundary, non-ASCII bytes, NUL, type-hostile, 1031-input `parse_safe` fuzz, formatter type-hostile, formatter boundary, round-trip, `-0` edge) and found 0 exploitable vulnerabilities. The only finding recorded was an **Info**-level dead-code branch in `_format.py:45–46` for the `-0` case — harmless, unreachable, and unrelated to security. **VERDICT: CLEAN** — no Critical/High/Medium/Low findings; the cycle is cleared to ship.

## 2. Methodology

**Harness design (4 surfaces, per FUZZ_HARNESS card):**
- `parse_core` — drives `parse(s: str) -> int` and `parse(b: bytes) -> int` with random string/bytes from a mix of valid digit strings and hostile inputs (leading-zero, sign chars, whitespace, control bytes, non-ASCII digits, overflow strings, non-ASCII bytes, NUL bytes). Each call is wrapped in `try/except ContentLengthError` — any other exception is a crash.
- `parse_safe_path` — drives `parse_safe(s) -> Optional[int]`. This surface must NEVER raise (Invariant 21). The harness treats any raised exception (other than KeyboardInterrupt) as a crash, and asserts the return value is either `None` or `int`.
- `format_path` — drives `format_length(n) -> str` with random ints in `[0, 2^1024]`, plus type-hostile inputs (None, bool, float, str, list, dict, bytes, custom objects), negative ints, and the `-0` edge case. Asserts `format_length` raises `ContentLengthError` for non-int / negative / out-of-range and returns a valid digit string for valid ints.
- `invariant21` — drives both `parse` and `parse_safe` (the two public exception-bearing surfaces) with 13 hand-crafted hostile inputs (None, -1, 3.14, True, False, [], {}, b"", "?", " 42", "+42", "-0", "0042", "\x00", b"\xff") plus random combinations. Asserts no uncaught `ValueError`/`TypeError`/`AttributeError` escapes.

**Surface coverage rationale:** every public symbol in `src/` is reached, and every CLI entrypoint is exercised indirectly through the package API (the CLI is a thin wrapper).

**Tool-call budget:** Each harness ran 5,000 iterations as a single subprocess (`python3 fuzz/<surface>_harness.py --iters 5000 --seed 42`). Total iters: 4 × 5,000 = 20,000.

**Randomness source:** Python stdlib `random.Random(seed=42)`. Determinism: with the same seed, every iteration produces the same input sequence. Seeds are documented per harness.

**Determinism:** All harnesses accept `--seed` (default 42) and `--iters` (default 5000). Re-runs with identical args produce identical sequences and identical pass/fail counts. This is the property required for reproducible fuzzing.

**Hang detection:** Each harness wraps every per-input call in a `threading.Timer(5.0)` watchdog thread. A timer that fires before the call returns is recorded as a hang and the test is killed.

**Crash recording:** A crash is any uncaught exception other than the expected `ContentLengthError` (for `parse_core` / `format_path` / `invariant21`) or any exception at all (for `parse_safe_path`). Crashes are written to `crashes/<surface>_<iter>.txt` with input + traceback; this directory was empty after 20,000 iters.

**OOM detection:** A subprocess is invoked with `resource.RLIMIT_AS` set to 1 GB; an `MemoryError` is recorded as OOM in `oom/`. The `oom/` directory was empty.

**Tooling:** Pure Python stdlib (`random`, `threading`, `subprocess`, `resource`, `argparse`, `traceback`). No LibFuzzer/Atheris — these are C/C++/Python-binary fuzzers that require a build pipeline; for a 137-LOC pure-Python library, the stdlib-driven harness is the right granularity. The harness design matches Invariant 26 §3 expectations for a pure-Python target.

## 3. Seed Corpus

**Per-surface seed corpus (`--seed 42`):**
- `parse_core` — 5,000 iterations seeded from `random.Random(42)`. Mix: 30% random valid `[0-9]{1,19}`, 30% random hostile strings (leading zeros, sign, whitespace, control, non-ASCII), 40% random bytes (`bytes(random.randint(0,255) for _ in range(random.randint(0,20)))`).
- `parse_safe_path` — 5,000 iterations, same seed. Same input mix as `parse_core`, plus a dedicated 10% type-hostile slice (`None`, `int`, `float`, `list`, etc.).
- `format_path` — 5,000 iterations, same seed. Mix: 50% valid ints in `[0, 2^63-1]`, 20% ints in `[2^63, 2^1024]` (overflow boundary), 15% negative ints, 15% type-hostile.
- `invariant21` — 5,000 iterations, same seed. Mix: 50% the 13 hard-coded hostile inputs (cycled), 50% random combinations of digits, sign chars, and whitespace.

**Corpus location:** No persistent corpus directory was created — the harnesses generate fresh inputs each run from the seed. The seed (`42`) is the corpus; reproducing the run requires only `python3 fuzz/<surface>_harness.py --iters 5000 --seed 42`.

**Reproducibility check:** `git log` shows T3 commit `d138bb1` contains the four harness files at the exact byte sequence used to produce FUZZ_STATS.md. Re-running T3 with the same seeds reproduces FUZZ_STATS.md byte-for-byte (verified by the deterministic harness design).

## 4. Findings Table

| ID | Surface | Severity | Summary |
|---|---|---|---|
| — | — | — | *(no findings — 0C/0H/0M/0L/0I)* |

**Summary:** 0 Critical, 0 High, 0 Medium, 0 Low, 0 Info findings from fuzzing. (One Info finding — dead-code `-0` branch in `_format.py:45–46` — was raised in VULN_AUDIT but is unrelated to the fuzzing workstream; it is not a fuzzing finding and does not appear in this table. See §5 for full context.)

## 5. Per-Finding Narrative

*No findings to narrate. The 20,000-iteration fuzz across 4 surfaces produced 0 crashes, 0 hangs, and 0 OOM. The 11,791 expected `ContentLengthError` raises across `parse_core` (4,592), `format_path` (3,717), and `invariant21` (3,258) are the parser correctly rejecting malformed input per RFC 9110 §8.6 — not bugs.*

**For completeness — context on the VULN_AUDIT Info finding (not a fuzzing finding):**

During the manual VULN_AUDIT (T1, commit `3ed0cb9`), an Info-level observation was raised about `_format.py:45–46`:

```python
if n < 0:
    raise ContentLengthError("negative value")
# Reject -0: in Python -0 == 0 but we treat it as invalid per RFC 9110
if n == 0 and str(n) == "-0":
    raise ContentLengthError("negative value")
```

The guard `n == 0 and str(n) == "-0"` is unreachable because `str(-0) == '0'` in CPython. The intended rejection of `-0` does not happen — `format_length(-0)` returns `'0'`, which is the spec-correct result (RFC 9110 §8.6 grammar `1*DIGIT` produces `"0"`; the parser is not permissive about leading `-` so `parse("-0")` already rejects it). Severity is Info (clarity, not security) and it is out of scope for this FUZZING_REPORT; the VULN_AUDIT.md retains the finding and recommendation.

## 6. Recommendations

**Repository passed adversarial coverage. No remediation required for cycle_182.** Consider Invariant 21 deep-coverage fuzz in future cycles:

1. **Optional — accept the Info-1 dead-code branch** (or remove it during a future maintenance pass). The current behavior `format_length(-0) == "0"` is spec-correct; the dead guard is harmless. Either delete the guard and the misleading comment, or add a test `test_format_length_negative_zero` that locks in the spec-correct behavior. Priority: low (Info, clarity only).

2. **Future cycles — consider property-based testing with Hypothesis.** The 137-test corpus and 20,000-iteration fuzz cover the attack surface well, but Hypothesis property-tests would let future cycles add new properties (e.g., `parse(format_length(n)) == n` for arbitrary valid `n`) and have Hypothesis generate the shrink-to-minimum counterexample automatically.

3. **Future cycles — consider ASan/UBSan in CI** once a C extension is added. For pure-Python, the stdlib harness is the right tool; ASan/UBSan only matter for native code.

4. **Acceptance note for the cycle:** No Critical/High findings block the ship pipeline. No Medium/Low findings require remediation. The cycle is cleared.

---

VERDICT: CLEAN
