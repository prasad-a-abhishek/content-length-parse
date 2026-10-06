# Test Gaps — content-length-parse (cycle_182)

**Target commit:** `545ea29`
**Test corpus:** 137 tests across 7 test files (collected via `pytest --collect-only`):
- `tests/test_parse.py` — 87 lines
- `tests/test_strict.py` — 154 lines
- `tests/test_format.py` — 88 lines
- `tests/test_errors.py` — 111 lines
- `tests/test_roundtrip.py` — 57 lines
- `tests/test_vectors.py` — 61 lines
- `tests/test_typing.py` — 66 lines
- `tests/conftest.py` — 17 lines (one fixture)

## 15-AC coverage matrix

| AC | Description (spec §5) | Test file(s) | Test name(s) | Status |
|---|---|---|---|---|
| **AC-1** | `parse("0")` returns 0 | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_zero`, `TestParseStrict::test_parse_strict_zero`, `TestVectors::test_vec_01_zero_valid` | COVERED (3+ tests) |
| **AC-2** | `parse("42")` returns 42 | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_basic`, `TestParseStrict::test_parse_strict_basic`, `TestVectors::test_vec_02_42_valid` | COVERED (3+ tests) |
| **AC-3** | `parse(b"42")` returns 42 (bytes) | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_bytes`, `TestParseStrict::test_parse_strict_bytes`, `TestVectors::test_vec_03_bytes` | COVERED (3+ tests) |
| **AC-4** | `parse("0042")` raises (leading zero) | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_leading_zero`, `TestParseStrict::test_parse_strict_leading_zero`, `TestVectors::test_vec_04_leading_zero_rejected` | COVERED (3+ tests) |
| **AC-5** | `parse("-1")` raises (negative) | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_negative`, `TestParseStrict::test_parse_strict_negative`, `TestVectors::test_vec_05_negative_rejected` | COVERED (3+ tests) |
| **AC-6** | `parse("")` raises (empty) | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_empty`, `TestParseStrict::test_parse_strict_empty`, `TestVectors::test_vec_06_empty_rejected` | COVERED (3+ tests) |
| **AC-7** | `parse("  42  ")` raises (whitespace) | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_whitespace`, `TestParseStrict::test_parse_strict_whitespace`, `TestVectors::test_vec_07_whitespace_rejected` | COVERED (3+ tests) |
| **AC-8** | `parse("٤٢")` raises (non-ASCII) | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_non_ascii`, `TestParseStrict::test_parse_strict_non_ascii`, `TestVectors::test_vec_08_non_ascii_rejected` | COVERED (3+ tests) |
| **AC-9** | `parse("9"*N)` raises for N≫1 (overflow) | `test_parse.py`, `test_strict.py`, `test_vectors.py` | `test_parse_overflow`, `TestParseStrict::test_parse_strict_overflow`, `TestVectors::test_vec_10_overflow_rejected` | COVERED (3+ tests) |
| **AC-10** | `parse_safe("garbage")`→`None`; `parse_safe("42")`→`42` | `test_strict.py` (10 tests), `test_roundtrip.py` | `TestParseSafe::test_parse_safe_*` (zero, leading_zero, negative, empty, whitespace, non_ascii, overflow, type_error, int_input, list_input, bytes_non_ascii) | COVERED (11 tests) |
| **AC-11** | `format_length(42)`→`"42"`; `format_length(0)`→`"0"` | `test_format.py`, `test_strict.py` | `test_format_length_basic`, `TestFormatLengthStrict::test_format_length_*` (positive, zero, max_value) | COVERED (5+ tests) |
| **AC-12** | Round-trip `format_length(parse(x)) == x` | `test_roundtrip.py` | `TestRoundTrip::test_round_trip_*` (2000 random n in [0, 2^63-1]) | COVERED |
| **AC-13** | `ContentLengthError` is a `ValueError`; message encodes position | `test_errors.py` | `TestContentLengthError::test_subclass_of_value_error`, `test_message_includes_position`, `test_caught_by_except_value_error` | COVERED (3+ tests) |
| **AC-14** | `parse(None)`, `parse(42)` raise (type-mismatch) | `test_parse.py`, `test_strict.py` | `test_parse_type_error`, `TestParseSafe::test_parse_safe_type_error`, `test_parse_safe_int_input`, `test_parse_safe_list_input`, `TestParseStrict::test_parse_strict_type_error` | COVERED (5+ tests) |
| **AC-15** | `__version__` is `str`; `py.typed` exists; `mypy --strict` passes | `test_typing.py` | `TestTypingSmoke::test_version_is_str`, `test_py_typed_marker_exists`, `test_mypy_strict_on_init`, plus 4 importable checks | COVERED (7 tests) |

## Coverage verdict: **15/15 ACs COVERED, 137 tests collected, 0 gaps**

## Probed but not in spec (supplementary coverage)

| Probe | Where covered | Notes |
|---|---|---|
| CRLF (`"42\n"`, `"42\r\n"`) | `TestVectors::test_vec_09_crlf_rejected` | spec §3 row 8 |
| Tab character | covered by `test_parse_whitespace` parametrization | RFC 9110 §5.5 disallows HTAB in field-value |
| NUL byte in str (`"\x00"`) | covered by whitespace / non-ASCII parametrization | RFC 9110 §5.5 |
| Non-ASCII bytes (high-bit) | `TestParseSafe::test_parse_safe_bytes_non_ascii` | RFC 9110 §5.5 + UnicodeDecodeError path |
| 2^63-1 boundary (max valid) | `TestFormatLengthStrict::test_format_length_max_value` | overflow at exactly +1 |
| `-0` to formatter | covered transitively (returns `'0'`) | dead-code branch, see Info finding |
| `bool` to `format_length` | covered by `TestFormatLengthStrict::test_format_length_bool` | explicit `isinstance(n, bool)` check |
| `True`/`False` (Python `bool ⊂ int`) | covered | rejected as expected |
| `[]`, `{}`, `object()` to `parse` | `TestParseSafe::test_parse_safe_list_input` and parametrized type_error | Invariant 21 |
| 1000+ input random fuzz to `parse_safe` | `TestParseSafe::test_parse_safe_*` + `TestRoundTrip::test_round_trip_*` (2000 random) | invariant 21 stress |

## Gaps (none material)

The only "gap" I would flag is the `mypy --strict` test in `test_typing.py` is environment-dependent (requires `mypy` installed). The QA report (parent task `t_6a497431`) confirmed this: 136/137 pass in fresh venv without mypy, 137/137 with mypy installed. This is **not a code gap**; it is a dependency gap and is documented in the README/QA report. No new test is required.

## Conclusion

All 15 ACs have at least 1 dedicated test, and most have 3+. The 137-test corpus exceeds the 100-test floor. There are no ACs with 0 coverage. **No new tests are required to close gaps.** The QA worker has already verified 15/15 ACs covered in their report.
