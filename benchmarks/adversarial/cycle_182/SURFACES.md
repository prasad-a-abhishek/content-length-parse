# Attack Surfaces — content-length-parse (cycle_182)

**Target commit:** `545ea29`
**Package:** `content-length-parse` v0.1.0 — zero-dep pure-Python RFC 9110 §8.6 Content-Length header parser
**Module layout:** 4 src files, 4 public symbols, ~150 LOC impl, 137 tests, 7 test files

## Surface enumeration (4 surfaces)

| # | Surface | Entry point | Inputs | Outputs | Edge cases probed | Test files |
|---|---|---|---|---|---|---|
| 1 | `parse_core` | `src/content_length_parse/_parser.py::parse` (line 19) | `str` \| `bytes` | `int` (decimal) or raises `ContentLengthError` | empty string, single `0`, leading-zero `0042`, `+42`, `-1`, internal/trailing/leading whitespace, tab/newline/CRLF, NUL byte, non-ASCII digits (Arabic-Indic `٤٢`, fullwidth `４２`, superscript `²`), 2^63-1 boundary, 2^63 overflow, 10⁶-digit overflow, all-byte-range bytes | test_parse.py, test_strict.py, test_vectors.py |
| 2 | `parse_safe_path` | `src/content_length_parse/_parser.py::parse_safe` (line 85) | `str` \| `bytes` | `int` or `None` (NEVER raises) | same 28 input classes as `parse_core` PLUS type-hostile (None, int, float, bool, list, dict, object()), 500 random strings of `[0\u200B0-9 +- \t\n\r]` and 500 random bytes `bytes(randint(0,255) × randint(0,20))` (1031 inputs total) | test_strict.py, test_roundtrip.py |
| 3 | `format_path` | `src/content_length_parse/_format.py::format_length` (line 12) | `int` (or other) | `str` (canonical decimal) or raises `ContentLengthError` | `None`, `3.14`, `True`, `False`, `"42"`, `-1`, `-0` (dead-code branch), `2**63` (just-over), `2**63-1` (just-OK), `2**100` (huge), `0`, `1` | test_format.py, test_roundtrip.py |
| 4 | `invariant21` | all 4 public symbols (parse, parse_safe, format_length, ContentLengthError) | hostile: `None`, `3.14`, `True`, `False`, `[]`, `{}`, `object()`, `complex(1,0)`, `(1,)` | structured | must NEVER raise uncaught `TypeError`/`ValueError`/`AttributeError` — must return structured `ContentLengthError` (a `ValueError` subclass) | test_strict.py, test_errors.py, test_typing.py |

## Notes

- All 4 public symbols are pure functions / a `ValueError` subclass. No I/O, no global state, no logging, no threads. The attack surface is the input values, full stop.
- `ContentLengthError` is a `ValueError` subclass (`_errors.py:6`), so a caller using `except ValueError` catches it. This is **deliberate** per spec §3 (callers "that only need a boolean can use `except ValueError`") and a feature, not a flaw.
- There is no `__main__.py`, no CLI surface, no logging, no file I/O. The package is a library, not a server. Network-related CWEs (CRLF injection, HTTP smuggling, etc.) are **out of scope** for this surface map because the parser has no I/O to inject into.
