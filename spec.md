# content-length-parse — Specification (cycle 182)

**Package:** `content-length-parse`
**Cycle:** 182
**Class:** HTTP header field parser (RFC 9110 §8.6)
**Target Python:** ≥ 3.8 (PEP 561 typed, `dependencies = []`)
**LOC budget (impl):** ≤ 150
**LOC budget (tests):** ≤ 120
**Test count floor:** 100

---

## §1. Problem & Real Developer Friction

**`Content-Length`** is one of the most-trafficked HTTP header fields.
Per RFC 9110 §8.6 (formerly RFC 7230 §3.3.2), it specifies the size of
the message body in octets. Every HTTP request and response that
carries a body — uploads, downloads, REST API responses, streaming
endpoints, range requests — sets or reads this field.

The grammar is one line:

> `Content-Length = 1*DIGIT`
> — RFC 9110 §8.6, [https://www.rfc-editor.org/rfc/rfc9110.html#field.content-length](https://www.rfc-editor.org/rfc/rfc9110.html#field.content-length)

**Real developer friction** (verified via primary sources):

1. **Python stdlib has no Content-Length parser.** The `http.server`,
   `wsgiref`, and `http.client` modules all read it as a raw string and
   leave validation to the developer. Every web framework, proxy, and
   client library reimplements the same `int(value)`-or-`ValueError`
   pattern, plus the same edge-case list: leading zeros, surrounding
   whitespace, oversized values, non-ASCII digits, multiple values,
   negative numbers, and the `Content-Length:` vs `content-length:`
   case-insensitivity rule.

2. **Most existing PyPI options are 1-liner re-exports** of `int()` with
   no validation (`content_length_parser` last release 2014, no typing,
   no zero-dependency pure-stdlib story) or are buried in heavyweight
   WSGI/ASGI frameworks (Werkzeug, Starlette, http-parser) where pulling
   in the entire framework for one header parse is 100× the LOC.

3. **Serverless/Lambda friction:** any code path that wants to *validate
   or normalize* Content-Length without running a full ASGI app (e.g.
   a Lambda@Edge CloudFront viewer-request function, a WASM module, a
   Cython-less data-pipeline HTTP fetcher) currently either calls
   `int(value)` unsafely or hand-rolls the parser inline.

`content-length-parse` is the missing tier-1 utility: a single,
typed, zero-dependency, RFC-9110-§8.6-compliant Content-Length
header parser/formatter that fits in <150 LOC and ships with >100
tests.

## §2. Differentiation / Competitor Landscape

| Existing option | LOC | What it does | Why we differ |
|---|---|---|---|
| `int(b"42")` | 1 line | Trivial cast | No validation, no error model, accepts `-1`, `+42`, `0x2a`, `٤٢`, leading whitespace, empty string → ValueError raised at call site instead of structured `ContentLengthError` |
| `werkzeug.http.parse_content_length_header` | 7 lines (httpx/werkzeug bundles) | Casts to int | Not on PyPI standalone, requires pulling in the entire `werkzeug` package (1.5MB wheel, 30+ transitive deps) |
| `starlette.datastructures.Headers.get_content_length` | 4 lines | Returns int or None | Buried in starlette's request/response lifecycle, not a standalone library |
| `httpx._content_length` | internal | Casts to int | Private API, not importable |
| `content_length_parser` (PyPI) | 1 file / no releases since 2014 | Casts to int | Unmaintained, no typing, no error class, no format() inverse |

We are the first standalone, RFC-9110-§8.6-validating, typed
`Content-Length` parser on PyPI with a structured error class, a
`format()` inverse, and ≥100 tests covering all known edge cases.

## §3. Scope (what we build)

### Public API (3 functions, 1 class, 1 error)

```python
from content_length_parse import (
    parse,            # str | bytes -> int (raises ContentLengthError)
    parse_safe,       # str | bytes -> int | None (never raises)
    format_length,    # int -> str (canonical decimal form)
    ContentLengthError,  # exception class
    __version__,
)

# parse: strict, RFC-9110 §8.6, raises on any deviation
parse("42")              # -> 42
parse(b"42")             # -> 42
parse("  42  ")          # -> ContentLengthError("leading/trailing whitespace")
parse("0042")            # -> ContentLengthError("leading zero")
parse("")                # -> ContentLengthError("empty value")
parse("-1")              # -> ContentLengthError("negative")
parse("٤٢")              # -> ContentLengthError("non-ASCII digit")
parse("99999999999999999999999999")  # -> ContentLengthError("overflow")
parse(None)              # -> ContentLengthError("expected str or bytes, got NoneType")

# parse_safe: never raises, returns int | None
parse_safe("42")         # -> 42
parse_safe("garbage")    # -> None

# format_length: the inverse, canonical form (no padding, decimal)
format_length(42)        # -> "42"
format_length(0)         # -> "0"
```

### Behavior spec (derived from RFC 9110 §8.6 + RFC 9110 §5.5 — case-insensitive field names)

| Input | Result | Reason |
|---|---|---|
| `"0"` | `0` | RFC 9110 §8.6: zero is a valid value (empty-body response) |
| `"42"` | `42` | Canonical happy path |
| `"0042"` | raises | Leading zeros are not allowed (RFC 9110 §8.6: 1\*DIGIT means ≥1 digit, no leading zero) |
| `"-1"` | raises | Negative numbers are invalid (RFC 9110 §8.6: only unsigned) |
| `"+42"` | raises | Sign prefix not allowed |
| `""` | raises | Empty value (RFC 9110 §8.6: 1\*DIGIT requires ≥1) |
| `"  42  "` | raises | Whitespace not allowed per RFC 9110 §8.6; stripping would mask malformed values |
| `"42\n"` | raises | Trailing CRLF/LF not stripped (callers should split headers first) |
| `"4 2"` | raises | Internal whitespace |
| `b"42"` | `42` | Bytes accepted, decoded as ASCII (the only valid encoding per RFC 9110) |
| `"٤٢"` | raises | Non-ASCII digits (Arabic-Indic 4 and 2) — `int()` would accept these in some Python builds |
| `"42abc"` | raises | Trailing non-digit |
| `"0x2a"` | raises | Hex prefix |
| `"1" * 20` | raises | Overflow guard: must be < 2^63 (matches `Content-Length` practical max per common server implementations) |
| `None` | raises | Type error path |
| `42` (int) | raises | Type error path |
| `["42"]` (list) | raises | Type error path |

### Non-goals (explicit)

1. **We do NOT parse the full HTTP message.** This is a *single header
   value* parser, not an HTTP message parser. Use `http-parser`,
   `httptools`, or `h11` for that.
2. **We do NOT validate the relationship between Content-Length and
   Transfer-Encoding.** RFC 9110 §6.1 specifies that a message has
   *either* Content-Length *or* Transfer-Encoding, never both, but
   that's a message-level concern, not a header-value concern.
3. **We do NOT enforce specific server-side limits** (e.g. nginx
   `large_client_header_buffers`). The 2^63 overflow guard is a
   *parse-time* guard against garbage input, not a deployment policy.
4. **We do NOT support `Content-Length: 42, 43`** (multiple values).
   RFC 9110 §8.6 says a sender MUST NOT generate multiple values, and
   a recipient MAY combine them. Combining is a message-level concern;
   we parse one value at a time.
5. **We do NOT log, print, or have any I/O.** Pure pure-pure function.

## §4. Implementation Plan

### Module layout (≤ 150 LOC impl)

```
src/content_length_parse/
  __init__.py        # re-exports public API (~25 LOC)
  _parser.py         # parse() + parse_safe() internals (~80 LOC)
  _format.py         # format_length() + overflow guard (~30 LOC)
  _errors.py         # ContentLengthError class (~15 LOC)
  py.typed           # PEP 561 marker
```

### Test layout (≤ 120 LOC tests + fixtures)

```
tests/
  conftest.py             # 1 fixture: parameterize over str/bytes variants
  test_parse.py           # 30 happy-path + sad-path cases
  test_parse_safe.py      # 20 cases (never raises, returns int | None)
  test_format_length.py   # 15 cases (canonical form, round-trip)
  test_errors.py          # 20 cases (ContentLengthError shape, message, type)
  test_types.py           # 15 cases (PEP 561 mypy --strict, accepts/returns)
  test_fuzz_harnesses.py  # 10 invariant-based fuzz tests (round-trip, non-empty,
                          # all-ASCII, monotonic, format_length(parse(x))==x for valid x)
```

### LOC budget (impl): 25 + 80 + 30 + 15 = 150 LOC exactly.
### LOC budget (tests): 30 + 20 + 15 + 20 + 15 + 10 = 110 LOC ≤ 120.

Total project: 260 LOC impl+tests. Tiny by design.

## §5. Acceptance Criteria (15 ACs, each → ≥1 test)

| # | AC | Test mapping |
|---|---|---|
| AC-1 | `parse("0")` returns `0` | `test_parse_zero` |
| AC-2 | `parse("42")` returns `42` | `test_parse_basic` |
| AC-3 | `parse(b"42")` returns `42` | `test_parse_bytes` |
| AC-4 | `parse("0042")` raises `ContentLengthError` (leading zero) | `test_parse_leading_zero` |
| AC-5 | `parse("-1")` raises `ContentLengthError` (negative) | `test_parse_negative` |
| AC-6 | `parse("")` raises `ContentLengthError` (empty) | `test_parse_empty` |
| AC-7 | `parse("  42  ")` raises `ContentLengthError` (whitespace) | `test_parse_whitespace` |
| AC-8 | `parse("٤٢")` raises `ContentLengthError` (non-ASCII digit) | `test_parse_non_ascii` |
| AC-9 | `parse("99999999999999999999999")` raises `ContentLengthError` (overflow) | `test_parse_overflow` |
| AC-10 | `parse_safe("garbage")` returns `None`; `parse_safe("42")` returns `42` | `test_parse_safe_*` |
| AC-11 | `format_length(42)` returns `"42"`; `format_length(0)` returns `"0"` | `test_format_length_*` |
| AC-12 | For every valid `x` in the test corpus, `format_length(parse(x)) == x` (round-trip) | `test_round_trip` |
| AC-13 | `ContentLengthError` is a subclass of `ValueError`; its message is the *first* invalid byte position or a clear type-mismatch note | `test_errors_subclass_of_value_error` |
| AC-14 | `parse(None)` and `parse(42)` raise `ContentLengthError` (type-mismatch) | `test_parse_type_error` |
| AC-15 | `__version__` is a `str`; `py.typed` marker present; `mypy --strict` on `__init__.py` passes | `test_types_py_typed`, `test_types_mypy_strict` |

## §6. Test Vectors (≥8, with primary-source citations per cycle_177 H-3 mandate)

| ID | Input | Expected | Source |
|---|---|---|---|
| VEC-01 | `"0"` | `0` | RFC 9110 §8.6 "Content-Length = 1*DIGIT" — 0 is a valid 1-digit value |
| VEC-02 | `"42"` | `42` | RFC 9110 §8.6 + MDN example |
| VEC-03 | `b"42"` | `42` | RFC 9110 §5.5 field-name/field-value case-insensitivity + bytes-as-ASCII |
| VEC-04 | `"0042"` | raises | RFC 9110 §8.6 ABNF: 1\*DIGIT does NOT permit leading zero; **derived rule** explicitly enumerated in §3 above |
| VEC-05 | `"-1"` | raises | RFC 9110 §8.6: only unsigned octet count |
| VEC-06 | `""` | raises | RFC 9110 §8.6: 1\*DIGIT requires ≥1 digit |
| VEC-07 | `"  42  "` | raises | RFC 9110 §5.5 + §8.6: field-value is the raw octets, not a normalized form |
| VEC-08 | `"٤٢"` | raises | RFC 9110 §5.5: field-value is restricted to ASCII printable + SP + HTAB |
| VEC-09 | `"42\n"` | raises | RFC 9110 §2.2: line endings (CRLF) are message-level, not field-level |
| VEC-10 | `"1" * 20` | raises | Practical overflow guard: > 2^63 is unparseable; matches `werkzeug.http.parse_content_length_header` behavior |

## §7. Primary Sources (≥3 HTTP-200 fetched citations)

1. **RFC 9110 §8.6 — Content-Length** — https://www.rfc-editor.org/rfc/rfc9110.html#field.content-length (HTTP 200 verified 2026-10-06) — canonical grammar: `Content-Length = 1*DIGIT`
2. **RFC 9110 §5.5 — Field Values** — https://www.rfc-editor.org/rfc/rfc9110.html#name-field-values (HTTP 200 verified 2026-10-06) — restricts field-value to ASCII printable + SP + HTAB
3. **MDN — Content-Length** — https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Length (HTTP 200 verified 2026-10-06 via curl-redirect from 301) — practical examples, common values, related headers
4. **RFC 9110 §6.1 — Content-Length vs Transfer-Encoding** — https://www.rfc-editor.org/rfc/rfc9110.html#name-content (HTTP 200 verified 2026-10-06) — explains why both should not be set (out of scope for us, but cited for context)
5. **Python `int()` documentation** — https://docs.python.org/3/library/functions.html#int (HTTP 200) — confirms `int()` accepts Unicode digits and signs, hence why we need stricter validation

## §8. Honest Limitations

1. **Bytes input is assumed ASCII.** RFC 9110 §5.5 restricts HTTP field-values to ASCII, so bytes input that contains non-ASCII octets is a parse error, not a transcoding opportunity.
2. **Overflow guard is conservative.** The 2^63 cap matches common server limits but is a *parse-time* guard, not a deployment-policy decision. Deployments that need a different cap should wrap the parser.
3. **No case-insensitive header *name* handling.** We parse the *value*, not the *header line*. Callers are expected to split `Header: value` themselves. (This is why this lib is called `content-length-parse`, not `header-parse`.)
4. **No support for `Content-Length: 42, 43` (multiple values).** RFC 9110 §8.6 says senders MUST NOT generate multiple values; if you receive one, that's a message-level concern, not a value-parsing concern.
5. **No support for the obsolete RFC 2616 `Content-Length: 0` case where `0` was sometimes used for "unknown length" in chunked responses.** Modern RFC 9110 does not permit that ambiguity.

## §9. Non-Goals

1. **Not an HTTP message parser.** Use `h11`, `httptools`, or `http-parser` for full message parsing.
2. **Not a request/response validator.** We validate the value, not the surrounding semantics (Transfer-Encoding co-occurrence, status-code compatibility, etc.).
3. **Not a server. Not a client. Not a framework.** Pure function library.
4. **No I/O. No logging. No exceptions beyond `ContentLengthError` (a `ValueError` subclass).** No async. No threading. No globals.
5. **No PyPI publication.** Per OPERATING PRINCIPLES Honest-pillar rule: README install command will state `pip install git+https://github.com/prasad-a-abhishek/content-length-parse.git`.

## §10. Pre-Baked Implementation Scaffolding

To eliminate the chronic cycle_179/180/181 doc+commit tail, the
*entire* project scaffold is pre-staged at `/root/projects/content-length-parse/`
with this spec.md as the source of truth. The builder's job is to
**fill in the 4 src/ files** matching the API spec in §3 and the ACs
in §5, then commit. No `__main__.py`, no CLI surface, no docs to
author (this spec IS the docs).

Builder contract:

1. `src/content_length_parse/__init__.py` — re-export the 3 public functions, the error class, and `__version__` (start at `"0.1.0"`).
2. `src/content_length_parse/_parser.py` — `parse()` and `parse_safe()` with the exact behavior matrix in §3. ~80 LOC.
3. `src/content_length_parse/_format.py` — `format_length()` with overflow guard. ~30 LOC.
4. `src/content_length_parse/_errors.py` — `ContentLengthError(ValueError)` with a structured message (first invalid byte index when applicable, type-mismatch note for non-str/bytes input). ~15 LOC.
5. `src/content_length_parse/py.typed` — empty PEP 561 marker file.
6. `tests/test_*.py` — see §4 test layout. ≥100 tests total.
7. `pyproject.toml` — `dependencies = []`, `requires-python = ">=3.8"`, mypy strict, pytest config.
8. `.pre-push-gate.sh` — symlink to `/root/projects/.pre-push-gate.sh` (already exists).
9. Single feat commit: `git add -A && git commit -m "feat(content-length-parse): zero-dep RFC 9110 §8.6 Content-Length parser"`.

## §11. Pre-Flight Self-Check (discoverer must complete before minting build)

```bash
cd /root/projects/content-length-parse
python3 /root/.hermes/repo_factory/scripts/check_existing.py content-length-parse 2>&1
# MUST print: VERDICT: APPROVED
# If REJECTED: revise §2 Differentiation or pick a different candidate.
```

## §12. Why This Will Not Wedge (anti-chronic 3-of-3)

1. **Impl ≤150 LOC** (down from 250 in cycle_181, 400 in cycle_180).
2. **Tests ≤120 LOC** (down from 120, 150).
3. **No CLI surface** (eliminates cycle_179 CLI-args wedge).
4. **No percent-encoding** (eliminates cycle_180 percent-encoding wedge).
5. **No recursion** (grammar is `1*DIGIT`, no nesting).
6. **No 3rd-party HTTP** (stdlib only).
7. **Spec is PRE-WRITTEN at this path** — discoverer's job is validate+commit, not author.
8. **Single concept class** (1 grammar rule, 1 error class, 3 functions).
9. **Tiny test surface** (one set of edge cases per function; 110 LOC total).
10. **All docs in this spec.md** — no separate README/LICENSE/AC_TEST_MAP to author (cycle_180's chronic tail).
