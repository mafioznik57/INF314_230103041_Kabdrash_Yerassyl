"""Experiment A: fine vs coarse Pool.map dispatch granularity."""
import argparse
import csv
import multiprocessing as mp
import os
import time
from pathlib import Path

WORKERS = (1, 2, 4, 8)
CHUNKS = (1, 10_000)


def collatz_steps(n):
    steps = 0
    while n > 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def run_granularity(workers, total_items=1_000_000, chunk_size=1):
    start = time.perf_counter()
    with mp.Pool(processes=workers) as pool:
        results = pool.map(collatz_steps, range(1, total_items + 1), chunksize=chunk_size)
    return time.perf_counter() - start, sum(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--items', type=int, default=1_000_000)
    parser.add_argument('--output', default='results_a.csv')
    args = parser.parse_args()
    if args.items < 1:
        parser.error('--items must be positive')
    rows = []
    for chunk in CHUNKS:
        baseline = None
        for p in WORKERS:
            elapsed, checksum = run_granularity(p, args.items, chunk)
            if baseline is None:
                baseline = elapsed
            speedup = baseline / elapsed
            e = None if p == 1 else ((p * elapsed / baseline) - 1) / (p - 1)
            row = dict(experiment='A', configuration=f'Micro (k={chunk})' if chunk == 1 else f'Coarse (k={chunk})',
                       workers=p, items=args.items, chunk_size=chunk, seconds=round(elapsed, 6),
                       checksum=checksum, speedup=round(speedup, 6), karp_flatt='' if e is None else round(e, 6))
            rows.append(row)
            print(f'A chunk={chunk:5} P={p} time={elapsed:.3f}s speedup={speedup:.3f}x e={e if e is not None else "N/A"} checksum={checksum}', flush=True)
    # All variants must compute precisely the same mathematical result.
    if len(set(r['checksum'] for r in rows)) != 1:
        raise AssertionError('Experiment A checksum mismatch')
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('Wrote', args.output)


if __name__ == '__main__':
    mp.freeze_support()
    main()
