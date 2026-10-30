import time
from multiprocessing import Pool
from common import COUNTS, metrics, save


def private_worker(iterations):
    total = 0
    for _ in range(iterations):
        total += 1
    return total


def run_privatized(p, total_increments=20_000_000):
    tasks = [total_increments // p + (i < total_increments % p) for i in range(p)]
    start = time.perf_counter()
    with Pool(processes=p) as pool:
        result = sum(pool.map(private_worker, tasks))  # Reduce once
    runtime = time.perf_counter() - start
    assert result == total_increments
    return runtime


def main():
    times = {p: run_privatized(p) for p in COUNTS}
    save('exp_c.json', metrics(times))
    for p, row in metrics(times).items():
        print(f'C P={p}: {row}')


if __name__ == '__main__':
    main()
