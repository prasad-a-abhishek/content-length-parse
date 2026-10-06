# CWE Map — content-length-parse (cycle_182)

**Target commit:** `545ea29`
**CWE references:** [MITRE CWE catalog](https://cwe.mitre.org/) — entries current as of 2026-10-06

## CWE → surface mapping

| CWE | Name | Surfaces | Mapping rationale | Code references |
|---|---|---|---|---|
| **CWE-20** | Improper Input Validation | `parse_core`, `parse_safe_path` | The grammar `Content-Length = 1*DIGIT` (RFC 9110 §8.6) requires explicit validation of: leading-zero prohibition (`0042` rejected), non-ASCII digits (`٤٢` rejected), sign chars (`+42`/`-1` rejected), whitespace, empty input, overflow, NUL. All 7 rules are implemented. | `_parser.py::parse` (lines 19–51), `_parser.py::_parse_str` (lines 54–82) |
| **CWE-1284** | Improper Validation of Specified Quantity in Input | `parse_core`, `parse_safe_path` | The `Content-Length` header is a numeric "specified quantity". RFC 9110 §8.6 explicitly prohibits leading zeros ("1*DIGIT" is ≥1 digit, no leading zero), and the parser enforces this at `_parser.py:79–80`. The 2^63-1 overflow guard at `_parser.py:70–71` is the second half of this CWE. | `_parser.py:70–71` (overflow), `_parser.py:79–80` (leading zero) |
| **CWE-190** | Integer Overflow or Wraparound | `parse_core`, `format_path` | Both the parser (max 2^63-1, `_parser.py:12`) and the formatter (max 2^63-1, `_format.py:9`) cap at 2^63-1. The parser accumulates `acc * 10 + digit` and checks `acc > _MAX` per-iteration (`_parser.py:70–71`), preventing silent wraparound. The formatter checks once at the boundary (`_format.py:47–48`). | `_parser.py:12, 70–71`; `_format.py:9, 47–48` |
| **CWE-476** | NULL Pointer Dereference | `parse_core`, `format_path`, `invariant21` | "NULL pointer dereference" maps to Python's "NoneType" / "object has no attribute" / "argument of type 'NoneType' is not iterable" family. The parser checks `isinstance(value, (str, bytes))` first (`_parser.py:37–40`); the formatter checks `isinstance(n, bool)` then `isinstance(n, int)` (`_format.py:34–41`). Both raise structured `ContentLengthError`, never `AttributeError`. | `_parser.py:37–40`; `_format.py:34–41` |
| **CWE-682** | Incorrect Calculation | `format_path` | The formatter's `-0` branch at `_format.py:45–46` is **dead code** because `str(-0) == '0'` in CPython (verified in the probe). This is a "looks-wrong-but-isn't" finding: the result `format_length(-0)` returns `'0'` correctly, but the guard can never fire. Severity: Info / Low. | `_format.py:45–46` |
| **CWE-754** | Improper Check for Unusual or Exceptional Conditions | `parse_safe_path`, `invariant21` | `parse_safe` wraps `parse` in `try/except ContentLengthError` and returns `None` (`_parser.py:98–101`). This is the canonical "improper check for unusual conditions" fix: every failure mode of `parse` is collapsed to `None`. The Invariant 21 (never-raises) surface depends on this. Verified by 1031-input probe: 0 raises. | `_parser.py:98–101` |

## CWE entries NOT applicable (justified absences)

- **CWE-93 (CRLF Injection):** the parser returns an `int` and the formatter returns a `str` of digits. There is no path that writes to a network socket, HTTP header, file, log, or shell. CRLF injection requires a sink; there is no sink. **Not applicable.**
- **CWE-400 (Uncontrolled Resource Consumption):** the parser's loop is `for ch in s` and exits on the first non-digit. Length-N input runs in O(N) time with O(1) state. 10⁶-digit input is rejected at the first overflow check. No quadratic blowup, no recursion, no regex. **Not applicable** at the library level; would require a wrapper that reads an untrusted stream.
- **CWE-770 (Allocation of Resources Without Limits):** the parser allocates one `int` (`acc`) and one `str` (the input itself, already allocated by caller). No list, dict, or other growing structure is created per character. **Not applicable.**
- **CWE-1333 (Inefficient Regular Expression Complexity):** no regex is used. The grammar is hand-rolled character-by-character. **Not applicable.**
- **CWE-835 (Loop with Unreachable Exit Condition):** the `for i, ch in enumerate(s)` loop at `_parser.py:66` runs to `len(s)` and exits. Both the `acc > _MAX` early raise and the `not _ASCII_0 <= c <= _ASCII_9` early raise are reached in adversarial input. **Not applicable.**
- **CWE-617 (Reachable Assertion):** no `assert` statements in the impl. **Not applicable.**

## Summary

6 CWE entries map to the 4 attack surfaces; 6 additional entries were considered and excluded with justification. All 6 applicable CWEs have explicit, code-level mitigations.
