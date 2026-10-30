import math
import time
from multiprocessing import Pool
from common import COUNTS, metrics, save


def heavy_math(n):
    return sum(math.sin(i) * math.cos(i) for i in range(1, n))


def run_experiment(workers, total_chunks=16, chunk_size=2_000_000):
    start = time.perf_counter()
    time.sleep(0.40)  # Fixed serial work
    with Pool(processes=workers) as pool:
        pool.map(heavy_math, [chunk_size] * total_chunks)
    return time.perf_counter() - start


def main():
    times = {p: run_experiment(p) for p in COUNTS}
    save('exp_a.json', metrics(times))
    for p, row in metrics(times).items():
        print(f'A P={p}: {row}')


if __name__ == '__main__':
    main()
