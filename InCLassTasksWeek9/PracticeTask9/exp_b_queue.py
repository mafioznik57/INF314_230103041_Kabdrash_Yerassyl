"""Experiment B: a shared IPC Queue carrying every individual event."""
import argparse
import csv
import multiprocessing as mp
import time

WORKERS = (1, 2, 4, 8)


def queue_worker(out_queue, count, start_index):
    for i in range(start_index, start_index + count):
        out_queue.put(i % 7)


def run_queue_benchmark(p, total_items=400_000):
    q = mp.Queue()
    counts = [total_items // p + (1 if i < total_items % p else 0) for i in range(p)]
    offsets = []
    offset = 0
    for count in counts:
        offsets.append(offset)
        offset += count
    workers = [mp.Process(target=queue_worker, args=(q, count, offsets[i])) for i, count in enumerate(counts)]
    start = time.perf_counter()
    for w in workers:
        w.start()
    checksum = sum(q.get() for _ in range(total_items))
    for w in workers:
        w.join()
        if w.exitcode != 0:
            raise RuntimeError(f'Worker failed with exit code {w.exitcode}')
    elapsed = time.perf_counter() - start
    q.close()
    q.join_thread()
    return elapsed, checksum


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--items', type=int, default=400_000)
    parser.add_argument('--output', default='results_b.csv')
    args = parser.parse_args()
    if args.items < 1:
        parser.error('--items must be positive')
    rows = []
    baseline = None
    expected = (args.items // 7) * 21 + sum(i % 7 for i in range(args.items % 7))
    for p in WORKERS:
        elapsed, checksum = run_queue_benchmark(p, args.items)
        if checksum != expected:
            raise AssertionError(f'Queue checksum mismatch for P={p}: {checksum} != {expected}')
        if baseline is None:
            baseline = elapsed
        speedup = baseline / elapsed
        e = None if p == 1 else ((p * elapsed / baseline) - 1) / (p - 1)
        rows.append(dict(experiment='B', configuration='Queue Choke', workers=p, items=args.items,
                         seconds=round(elapsed, 6), checksum=checksum, speedup=round(speedup, 6),
                         karp_flatt='' if e is None else round(e, 6)))
        print(f'B P={p} time={elapsed:.3f}s speedup={speedup:.3f}x e={e if e is not None else "N/A"} checksum={checksum}', flush=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('Wrote', args.output)


if __name__ == '__main__':
    mp.freeze_support()
    main()
