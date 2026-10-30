import csv
import ctypes
import multiprocessing as mp
import time

from common import RESULTS

K = 5_000_000


def worker(array, worker_id, iterations, mode):
    position = worker_id * 8 if mode == 'padded' else worker_id
    if mode == 'privatized':
        value = 0
        for _ in range(iterations):
            value += 1
        array[position] = value
    else:
        for _ in range(iterations):
            array[position] += 1


def measure(processes, mode):
    # RawArray avoids the per-increment lock overhead of Array.
    array = mp.RawArray(ctypes.c_int64, processes * 8 if mode == 'padded' else processes)
    jobs = [mp.Process(target=worker, args=(array, i, K, mode)) for i in range(processes)]
    start = time.perf_counter()
    for job in jobs:
        job.start()
    for job in jobs:
        job.join()
    elapsed = time.perf_counter() - start
    if any(job.exitcode != 0 for job in jobs):
        raise RuntimeError('Worker failed')
    total = sum(array[i * 8 if mode == 'padded' else i] for i in range(processes))
    assert total == processes * K, (mode, total)
    return elapsed, total


def main():
    rows = []
    for mode in ('unpadded', 'padded', 'privatized'):
        baseline = None
        for p in (1, 2, 4, 8):
            elapsed, total = measure(p, mode)
            if p == 1:
                baseline = elapsed
            speedup = baseline / elapsed
            e = ((1 / speedup) - (1 / p)) / (1 - (1 / p)) if p > 1 else None
            row = {'mode': mode, 'processes': p, 'iterations_each': K,
                   'seconds': round(elapsed, 6), 'total_count': total,
                   'speedup': round(speedup, 6),
                   'karp_flatt': round(e, 6) if e is not None else ''}
            rows.append(row)
            print(row)
    with (RESULTS / 'false_sharing_karp_flatt.tsv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    mp.freeze_support()
    main()
