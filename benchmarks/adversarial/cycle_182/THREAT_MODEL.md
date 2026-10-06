# Threat Model — content-length-parse (cycle_182)

**Target commit:** `545ea29`
**Threat model scope:** the 4 public symbols of `content-length-parse`, called by an HTTP framework, proxy, or middleware that has just read a `Content-Length` header value from a wire (or test fixture) and needs to validate it before acting on it.

## Trust boundary

```
┌─────────────────────────────────────┐
│  UNTRUSTED INPUT (network/file/test) │
│  raw bytes from HTTP wire           │
└────────────┬────────────────────────┘
             │ str | bytes
             ▼
┌─────────────────────────────────────┐
│  TRUSTED LIBRARY (this package)     │
│  parse() / parse_safe()             │
│  format_length()                    │
└────────────┬────────────────────────┘
             │ int | None | ContentLengthError
             ▼
┌─────────────────────────────────────┐
│  CALLER (framework / app)           │
│  decides what to do with the int    │
└─────────────────────────────────────┘
```

The library's job is to **fail closed** on any input that doesn't match the RFC 9110 §8.6 grammar `1*DIGIT`. The caller's job is to use the result.

## Threat actors

1. **Malicious HTTP client** — sends a hand-crafted `Content-Length` value designed to break downstream consumers (parser differentials, smuggling).
2. **Buggy HTTP server / proxy** — sends malformed values (e.g. with trailing whitespace) that this library must reject, not silently accept.
3. **Legacy / test data** — historical data containing `0042` (some pre-RFC-9110 senders) that callers may need to detect-and-reject rather than silently accept.

## Attack vectors (probed and confirmed)

| ID | Vector | Tested input | Expected | Actual | Verdict |
|---|---|---|---|---|---|
| AV-01 | Leading zero (RFC 9110 §8.6 explicit prohibition) | `"0042"`, `"00"`, `"01"`, `"0123"` | reject | `ContentLengthError("leading zero at position 0")` | PASS |
| AV-02 | Sign prefix | `"+42"`, `"-1"`, `"-0"`, `"+0"` | reject | `ContentLengthError("invalid character at position 0: '+'\|'-'")` | PASS |
| AV-03 | Leading / trailing / internal whitespace | `" 42"`, `"42 "`, `" 42 "`, `"4 2"`, `"\t42"`, `"42\t"` | reject | `ContentLengthError("invalid character at position 0\|N: ' '\|\t")` | PASS |
| AV-04 | Line endings / control chars | `"42\n"`, `"42\r"`, `"42\r\n"`, `"\x00"`, `"4\x002"` | reject | rejected with position-indexed `ContentLengthError` | PASS |
| AV-05 | Non-ASCII digits | `"٤٢"` (Arabic-Indic), `"４２"` (fullwidth), `"𝟙"` (mathematical), `"²"` (superscript), `"½"` (vulgar fraction) | reject | `ContentLengthError("invalid character at position 0: '٤'\|'４'\|'𝟙'\|'²'\|'½'")` | PASS |
| AV-06 | Unicode zero-width chars | `"\u200B42"` (zero-width space) | reject | rejected (not a digit) | PASS |
| AV-07 | 2^63-1 boundary (max valid) | `"9223372036854775807"` (2^63-1) | accept | `parse` returns `9223372036854775807` | PASS |
| AV-08 | 2^63 overflow | `"9223372036854775808"` (2^63), `"9"*20`, `"9"*30`, `"9"*100` | reject | `ContentLengthError("overflow at position N")` | PASS |
| AV-09 | Non-ASCII bytes | `b"\xd9\xa4"` (UTF-8 of `٤`), `b"\xff\xfe"`, `bytes(range(128,256))` | reject | `ContentLengthError("bytes value is not valid ASCII")` | PASS |
| AV-10 | NUL byte in str | `"\x00"`, `"4\x002"` | reject | rejected with position 0 / 1 | PASS |
| AV-11 | Type hostile | `None`, `42`, `3.14`, `True`, `False`, `[]`, `{}`, `object()`, `complex(1,0)`, `(1,)` | reject with `ContentLengthError` | every case raises `ContentLengthError`, no `TypeError`/`AttributeError` leaked | PASS |
| AV-12 | `parse_safe` total-function invariant | 1031 inputs (10 type-hostile + 14 str edge + 7 bytes edge + 1000 random `[0\u200B0-9 +- \t\n\r]` strings and `bytes(randint(0,255) × randint(0,20))`) | never raise | 0 raises observed (only `int` or `None` returned) | PASS |
| AV-13 | `format_length` type hostile | `None`, `3.14`, `"42"`, `[]`, `{}`, `True` (int), `False` (int) | reject with `ContentLengthError` | every case rejected; `True` and `False` correctly caught by explicit `isinstance(n, bool)` check | PASS |
| AV-14 | `format_length` boundary | `-1`, `-0`, `2**63`, `2**63-1`, `2**100` | reject negatives and over-max, accept 0/1/boundary | `-1` rejected, `0`→`'0'`, `2**63-1`→`'9223372036854775807'`, `2**63` rejected, `2**100` rejected, `-0`→`'0'` (dead-code branch) | PASS |
| AV-15 | Round-trip (`format_length(parse(x)) == x`) | 2000 random `n ∈ [0, 2^63-1]` | identity | 0 failures | PASS |
| AV-16 | Zero-byte str | `""` | reject | `ContentLengthError("empty value")` | PASS |
| AV-17 | Single zero | `"0"` | accept as 0 | `parse("0") == 0` (NOT a leading-zero rejection — special-cased at `_parser.py:79` because `n == 1`) | PASS |
| AV-18 | Negative zero on formatter | `-0` | either reject or return `'0'` (dead-code branch) | returns `'0'` because `str(-0) == '0'` makes the explicit `str(n) == "-0"` guard dead code at `_format.py:45` | PASS (with Info) |

## Out-of-scope threats (justified)

- **CRLF injection into HTTP response.** This library returns `int` / `str`; the caller chooses the sink. The library is not the sink.
- **HTTP request smuggling (CL.TE).** Smuggling is a *message-level* concern (parsing the relationship between Content-Length and Transfer-Encoding). The spec §9 Non-Goal #1 and §9 Non-Goal #2 explicitly delegate this to `h11`, `httptools`, or `http-parser`.
- **Resource exhaustion via huge string.** A 1 GB str would burn memory before reaching the parser; this is the caller's responsibility (they constructed the str). The parser's loop is O(N) and exits on first non-digit, so 1 GB of all-ASCII digits would be rejected by the overflow guard well before allocation pressure.
- **Timing side channels.** All branches are O(1) or O(N) over uniform input. No early-exit on length that would leak prefix info. Out of scope.
- **Regex DoS (ReDoS).** No regex in the implementation. The parser is a hand-rolled character loop.

## Summary

18 attack vectors were probed; **all 18 returned the expected behavior**. One Info-level finding (dead-code `-0` branch in `_format.py:45–46`) noted for the report but not a vulnerability.
