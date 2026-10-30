| Configuration | T1 (s) | T2 (s) | T4 (s) | T8 (s) | S8 | e(2) | e(8) |
|---|---:|---:|---:|---:|---:|---:|---:|
| A: Micro (k=1) | 92.853 | 124.698 | 125.852 | 60.025 | 1.547 | 1.686 | 0.596 |
| A: Coarse (k=10000) | 11.622 | 6.668 | 4.149 | 3.183 | 3.651 | 0.147 | 0.170 |
| B: Queue Choke | 4.258 | 5.536 | 8.160 | 8.126 | 0.524 | 1.600 | 2.038 |
| C: Buffered Batch | 1.103 | 0.713 | 0.554 | 0.612 | 1.803 | 0.293 | 0.491 |


- A: At P=8, coarse chunks took 3.183s versus micro chunks 60.025s. Coarse dispatch was faster in this run.
- B: T1=4.258s and T8=8.126s. Negative scaling was observed.
- C: T1=1.103s and T8=0.612s. Positive eight-worker speedup was observed.
- B versus C compares different workloads (400,000 vs 10,000,000 items in full mode), so raw execution times alone are not an apples-to-apples speedup measure. Compare throughput (items/s) as well.
- B throughput at P=8: 49,224 items/s. C throughput at P=8: 16,338,641 items/s.
- Contention is a plausible explanation for B performance, but timings alone cannot prove OS lock thrashing. Scheduler, pipe, or synchronization profiling is needed for causal attribution.
- The instructor thresholds (C S8 > 5 and e8 <= 0.05, B rising e) are targets, **not guaranteed results**; compare measured values above.


