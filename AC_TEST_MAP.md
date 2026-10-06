# AC → Test Coverage Map (content-length-parse cycle_182)

Every acceptance criterion from `spec.md §5` has ≥1 test mapped below.

| AC | Description | Test(s) |
|----|-------------|---------|
| AC-1 | `parse("0")` returns `0` | `test_parse.py::TestParseHappyPath::test_parse_zero` |
| AC-2 | `parse("42")` returns `42` | `test_parse.py::TestParseHappyPath::test_parse_basic` |
| AC-3 | `parse(b"42")` returns `42` | `test_parse.py::TestParseHappyPath::test_parse_bytes` |
| AC-4 | `parse("0042")` raises `ContentLengthError` (leading zero) | `test_parse.py::TestParseRejection::test_parse_leading_zero`, `test_strict.py::TestWhitespaceRejection::(n/a - covered in parse)`, `test_vectors.py::TestVectors::test_vec_04_leading_zero_rejected` |
| AC-5 | `parse("-1")` raises `ContentLengthError` (negative) | `test_parse.py::TestParseRejection::test_parse_negative`, `test_vectors.py::TestVectors::test_vec_05_negative_rejected` |
| AC-6 | `parse("")` raises `ContentLengthError` (empty) | `test_parse.py::TestParseRejection::test_parse_empty`, `test_vectors.py::TestVectors::test_vec_06_empty_rejected` |
| AC-7 | `parse("  42  ")` raises `ContentLengthError` (whitespace) | `test_strict.py::TestWhitespaceRejection::test_parse_whitespace_leading`, `test_vectors.py::TestVectors::test_vec_07_whitespace_rejected` |
| AC-8 | `parse("٤٢")` raises `ContentLengthError` (non-ASCII digit) | `test_strict.py::TestNonAsciiDigitRejection::test_parse_non_ascii`, `test_vectors.py::TestVectors::test_vec_08_non_ascii_rejected` |
| AC-9 | `parse("99999999999999999999999")` raises `ContentLengthError` (overflow) | `test_strict.py::TestOverflowRejection::test_parse_overflow`, `test_vectors.py::TestVectors::test_vec_10_overflow_rejected` |
| AC-10 | `parse_safe("garbage")` returns `None`; `parse_safe("42")` returns `42` | `test_strict.py::TestParseSafe::test_parse_safe_valid_str`, `test_strict.py::TestParseSafe::test_parse_safe_valid_bytes`, `test_strict.py::TestParseSafe::test_parse_safe_leading_zero`, `test_strict.py::TestParseSafe::test_parse_safe_negative`, `test_strict.py::TestParseSafe::test_parse_safe_empty`, `test_strict.py::TestParseSafe::test_parse_safe_whitespace`, `test_strict.py::TestParseSafe::test_parse_safe_non_ascii`, `test_strict.py::TestParseSafe::test_parse_safe_overflow`, `test_strict.py::TestParseSafe::test_parse_safe_type_error` |
| AC-11 | `format_length(42)` returns `"42"`; `format_length(0)` returns `"0"` | `test_format.py::TestFormatLength::test_format_length_42`, `test_format.py::TestFormatLength::test_format_length_zero` |
| AC-12 | Round-trip: `format_length(parse(x)) == x` for valid x | `test_format.py::TestRoundTrip::test_roundtrip` (parametrized over 11 values), `test_roundtrip.py::TestRoundtrip::test_roundtrip_via_str` (parametrized over 26 values) |
| AC-13 | `ContentLengthError` is a subclass of `ValueError` | `test_errors.py::TestErrorClass::test_is_subclass_of_value_error`, `test_errors.py::TestErrorClass::test_is_instance_of_value_error` |
| AC-14 | `parse(None)` and `parse(42)` raise `ContentLengthError` (type-mismatch) | `test_errors.py::TestTypeMismatch::test_parse_none`, `test_errors.py::TestTypeMismatch::test_parse_int`, `test_errors.py::TestTypeMismatch::test_parse_list`, `test_errors.py::TestTypeMismatch::test_parse_dict`, `test_errors.py::TestTypeMismatch::test_parse_float` |
| AC-15 | `__version__` is a `str`; `py.typed` marker present; mypy strict passes | `test_typing.py::TestTypingSmoke::test_version_is_str`, `test_typing.py::TestTypingSmoke::test_py_typed_marker_exists`, `test_typing.py::TestMypyStrict::test_mypy_strict_on_init` |

## Test vector coverage

All 10 spec vectors (§6) are covered in `tests/test_vectors.py`:

| Vector | Input | Expected | Test |
|--------|-------|----------|------|
| VEC-01 | `"0"` | `0` | `test_vec_01_zero_valid` |
| VEC-02 | `"42"` | `42` | `test_vec_02_42_valid` |
| VEC-03 | `b"42"` | `42` | `test_vec_03_bytes` |
| VEC-04 | `"0042"` | raises | `test_vec_04_leading_zero_rejected` |
| VEC-05 | `"-1"` | raises | `test_vec_05_negative_rejected` |
| VEC-06 | `""` | raises | `test_vec_06_empty_rejected` |
| VEC-07 | `"  42  "` | raises | `test_vec_07_whitespace_rejected` |
| VEC-08 | `"٤٢"` | raises | `test_vec_08_non_ascii_rejected` |
| VEC-09 | `"42\n"` | raises | `test_vec_09_crlf_rejected` |
| VEC-10 | `"1"*20` | raises | `test_vec_10_overflow_rejected` |
