# FUZZ_STATS — content-length-parse, cycle_182

| Surface | Iters | Runtime (s) | Crashes | Hangs | OOM | Peak RSS (MB) |
|---|---|---|---|---|---|---|
| parse_core | 5000 | 0.285 | 0 | 0 | 0 | 199.8 |
| parse_safe_path | 5000 | 0.301 | 0 | 0 | 0 | 199.8 |
| format_path | 5000 | 0.302 | 0 | 0 | 0 | 199.8 |
| invariant21 | 5000 | 2.735 | 0 | 0 | 0 | 199.8 |

**Total: 20000 iters across 4 surfaces, 0 crashes, 0 hangs, 0 OOM.**

Per-surface ok vs expected_errors:
- parse_core: 408 ok, 4592 expected ContentLengthError
- parse_safe_path: 5000 ok, 0 expected errors (parse_safe never raises)
- format_path: 1283 ok, 3717 expected ContentLengthError
- invariant21: 1742 ok, 3258 expected ContentLengthError

**Environment:** Python 3.11.15, Linux 6.12.67-linuxkit, no ASan (pure Python), seed=42.

**Methodology:** Each harness is invoked as a fresh subprocess (`python3 fuzz/<surface>_harness.py --iters 5000 --seed 42`) so RSS / runtime is per-process. Peak RSS reported is the rusage observed in the parent driver after the child returned (single value because all 4 subprocesses share the same driver context); per-child RSS can be read from `/usr/bin/time -v` if needed in a future cycle.

**Triage note for T4:** With 0 crashes and 0 hangs across 20000 iters, there are no findings to triage. T4 can author FUZZING_REPORT.md declaring VERDICT: CLEAN.
