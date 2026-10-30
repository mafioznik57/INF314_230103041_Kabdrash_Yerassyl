"""Experiment C: local batching and pre-aggregation before a Queue.put."""
import argparse
import csv
import multiprocessing as mp
import time

WORKERS = (1, 2, 4, 8)


def buffered_worker(out_queue, count, start_index, batch_size=10_000):
    batch_total = 0
    batch_count = 0
    for i in range(start_index, start_index + count):
        batch_total += i % 7
        batch_count += 1
        if batch_count >= batch_size:
            out_queue.put(batch_total)
            batch_total, batch_count = 0, 0
    if batch_count:
        out_queue.put(batch_total)
    out_queue.put(None)  # One end-of-work signal per producer.


def run_buffered(p, total_items=10_000_000, batch_size=10_000):
    q = mp.Queue()
    counts = [total_items // p + (1 if i < total_items % p else 0) for i in range(p)]
    offsets = []
    offset = 0
    for count in counts:
        offsets.append(offset)
        offset += count
    workers = [mp.Process(target=buffered_worker, args=(q, count, offsets[i], batch_size))
               for i, count in enumerate(counts)]
    start = time.perf_counter()
    for w in workers:
        w.start()
    checksum, completed = 0, 0
    while completed < p:
        item = q.get()
        if item is None:
            completed += 1
        else:
            checksum += item
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
    parser.add_argument('--items', type=int, default=10_000_000)
    parser.add_argument('--batch-size', type=int, default=10_000)
    parser.add_argument('--output', default='results_c.csv')
    args = parser.parse_args()
    if args.items < 1 or args.batch_size < 1:
        parser.error('--items and --batch-size must be positive')
    expected = (args.items // 7) * 21 + sum(i % 7 for i in range(args.items % 7))
    rows = []
    baseline = None
    for p in WORKERS:
        elapsed, checksum = run_buffered(p, args.items, args.batch_size)
        if checksum != expected:
            raise AssertionError(f'Buffered checksum mismatch for P={p}: {checksum} != {expected}')
        if baseline is None:
            baseline = elapsed
        speedup = baseline / elapsed
        e = None if p == 1 else ((p * elapsed / baseline) - 1) / (p - 1)
        rows.append(dict(experiment='C', configuration='Buffered Batch', workers=p, items=args.items,
                         batch_size=args.batch_size, seconds=round(elapsed, 6), checksum=checksum,
                         speedup=round(speedup, 6), karp_flatt='' if e is None else round(e, 6)))
        print(f'C P={p} time={elapsed:.3f}s speedup={speedup:.3f}x e={e if e is not None else "N/A"} checksum={checksum}', flush=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('Wrote', args.output)


if __name__ == '__main__':
    mp.freeze_support()
    main()
