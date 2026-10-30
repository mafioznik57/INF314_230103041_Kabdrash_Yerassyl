"""Run A, B, C and produce a measured Markdown report. Python 3.9+."""
import argparse
import csv
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_csv(name):
    with (ROOT / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def format_row(label, rows):
    by_p = {int(r['workers']): r for r in rows}
    def num(p, key):
        value = by_p[p][key]
        return f'{float(value):.3f}' if value != '' else 'N/A'
    speed = num(8, 'speedup')
    e2 = num(2, 'karp_flatt')
    e8 = num(8, 'karp_flatt')
    return f'| {label} | ' + ' | '.join(num(p, 'seconds') for p in (1, 2, 4, 8)) + f' | {speed} | {e2} | {e8} |'


def main():
    parser = argparse.ArgumentParser(description='Benchmark full lab or reduced smoke run.')
    parser.add_argument('--smoke', action='store_true', help='Quick correctness checks; not submission-scale benchmarks.')
    args = parser.parse_args()
    config = {'A': 1000 if args.smoke else 1_000_000,
              'B': 280 if args.smoke else 400_000,
              'C': 1000 if args.smoke else 10_000_000}
    for letter, filename, output in [('A', 'exp_a_granularity.py', 'results_a.csv'),
                                      ('B', 'exp_b_queue.py', 'results_b.csv'),
                                      ('C', 'exp_c_buffered.py', 'results_c.csv')]:
        command = [sys.executable, str(ROOT / filename), '--items', str(config[letter]),
                   '--output', str(ROOT / output)]
        print('Running:', ' '.join(command), flush=True)
        subprocess.run(command, check=True)
    a, b, c = (read_csv('results_a.csv'), read_csv('results_b.csv'), read_csv('results_c.csv'))
    micro = [r for r in a if int(r['chunk_size']) == 1]
    coarse = [r for r in a if int(r['chunk_size']) == 10_000]
    header = '''# CS482 — Variant B: Scalability Diagnostics

## Environment and methodology

'''
    host = f'- Platform: {platform.platform()}\n- Python: {platform.python_version()}\n- Logical CPUs (os.cpu_count): {os.cpu_count()}\n'
    host += f'- Run type: {"REDUCED SMOKE TEST (NOT FULL BENCHMARK)" if args.smoke else "FULL HANDOUT PARAMETERS"}\n'
    host += f'- Workloads: A={config["A"]:,} Collatz inputs; B={config["B"]:,} queue events; C={config["C"]:,} buffered elements.\n'
    host += '- Workers: P = 1, 2, 4, 8. A uses chunksize 1 or 10,000; C uses batch size 10,000.\n'
    host += '- Runtime includes worker/pool startup and shutdown. One measurement per configuration; repeat runs for statistical confidence.\n'
    host += '- T₁ is measured independently within each configuration. Speedup = T₁/Tₚ; efficiency = speedup/P × 100%; e(P) = (P×Tₚ/T₁−1)/(P−1).\n'
    body = '''
## Measured results

| Configuration | T1 (s) | T2 (s) | T4 (s) | T8 (s) | S8 | e(2) | e(8) |
|---|---:|---:|---:|---:|---:|---:|---:|
'''
    body += '\n'.join([format_row('A: Micro (k=1)', micro), format_row('A: Coarse (k=10000)', coarse),
                        format_row('B: Queue Choke', b), format_row('C: Buffered Batch', c)]) + '\n'
    def verdict(rows):
        v = {int(r['workers']):r for r in rows}
        ts = [float(v[p]['seconds']) for p in (1,2,4,8)]
        return ts
    at, bt, ct = verdict(micro), verdict(b), verdict(c)
    ac = verdict(coarse)
    body += '\n## Interpretation (based on the measurements above)\n\n'
    body += f'- A: At P=8, coarse chunks took {ac[-1]:.3f}s versus micro chunks {at[-1]:.3f}s. '
    body += ('Coarse dispatch was faster in this run.\n' if ac[-1] < at[-1] else 'Coarse dispatch was not faster in this run.\n')
    body += f'- B: T1={bt[0]:.3f}s and T8={bt[-1]:.3f}s. '
    body += ('Negative scaling was observed.\n' if bt[-1] > bt[0] else 'Negative scaling was NOT observed.\n')
    body += f'- C: T1={ct[0]:.3f}s and T8={ct[-1]:.3f}s. '
    body += ('Positive eight-worker speedup was observed.\n' if ct[-1] < ct[0] else 'Positive eight-worker speedup was NOT observed.\n')
    body += '- B versus C compares different workloads (400,000 vs 10,000,000 items in full mode), so raw execution times alone are not an apples-to-apples speedup measure. Compare throughput (items/s) as well.\n'
    body += f'- B throughput at P=8: {config["B"]/bt[-1]:,.0f} items/s. C throughput at P=8: {config["C"]/ct[-1]:,.0f} items/s.\n'
    body += '- Contention is a plausible explanation for B performance, but timings alone cannot prove OS lock thrashing. Scheduler, pipe, or synchronization profiling is needed for causal attribution.\n'
    body += '- The instructor thresholds (C S8 > 5 and e8 <= 0.05, B rising e) are targets, **not guaranteed results**; compare measured values above.\n'
    body += '\n## Data validation\n\nAll scripts assert the expected checksum for each worker count. A also compares checksums between chunk sizes. CSV files hold unrounded-by-display observations.\n'
    body += '\n## Git submission\n\nCommit `exp_a_granularity.py`, `exp_b_queue.py`, `exp_c_buffered.py`, `RESULTS_B.md` and optionally the CSV outputs. Push your own `variant-b-<STUDENT_ID>` branch.\n'
    (ROOT / 'RESULTS_B.md').write_text(header + host + body, encoding='utf-8')
    print('\nREPORT CREATED:', ROOT / 'RESULTS_B.md')


if __name__ == '__main__':
    main()
