import time
from multiprocessing import Process, Value, Lock
from common import COUNTS, metrics, save


def contended_worker(counter, lock, iterations):
    for _ in range(iterations):
        with lock:
            counter.value += 1


def run_contended(p, total_increments=2_000_000):
    counter = Value('q', 0, lock=False)
    lock = Lock()
    chunks = [total_increments // p + (i < total_increments % p) for i in range(p)]
    workers = [Process(target=contended_worker, args=(counter, lock, n)) for n in chunks]
    start = time.perf_counter()
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    if any(worker.exitcode != 0 for worker in workers):
        raise RuntimeError('A worker failed')
    assert counter.value == total_increments
    return time.perf_counter() - start


def main():
    times = {p: run_contended(p) for p in COUNTS}
    save('exp_b.json', metrics(times))
    for p, row in metrics(times).items():
        print(f'B P={p}: {row}')


if __name__ == '__main__':
    main()
