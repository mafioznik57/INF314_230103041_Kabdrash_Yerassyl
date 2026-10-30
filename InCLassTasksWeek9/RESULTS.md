# Karp-Flatt Practice Lab Results

Actual measurements from this computer.

| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Diagnosis |
|---|---:|---:|---:|---:|---:|---|
| Serial Tail | 6.635 | 4.150 | 2.684 | 0.251 | 0.206 | Fixed serial delay; e may remain nearly constant |
| Lock Contention | 1.961 | 14.680 | 10.458 | 13.974 | 6.778 | Shared mutex introduces coordination overhead |
| Privatized | 0.835 | 0.727 | 0.432 | 0.743 | 0.357 | Local counters avoid per-increment locking |

## Instructor rubric

- PASS: A: e(4)/e(2) between 0.80 and 1.25
- PASS: B: T4 > T1
- NOT MET: B: e(4) > e(2)
- PASS: C: T4 < T1
- NOT MET: C: E4 > 70%

Note: Runtime and scaling depend on CPU load, physical cores, Windows process overhead, and Python version. A failed rubric target is not a calculation failure.
