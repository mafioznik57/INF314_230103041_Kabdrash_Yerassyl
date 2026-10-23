import math
import os
import random
import threading
import time
from pathlib import Path

STUDENT_ID = 230103041
THREADS = 4
TOTAL_POINTS = 40_000_000
OUTPUT_FILE = Path(__file__).with_name('task2_output.txt')


def run_experiment(shared: bool) -> tuple[float, float, float]:
    counts = [0] * THREADS
    prng = random.Random(STUDENT_ID * 10) if shared else None
    lock = threading.Lock()

    def worker(thread_index: int) -> None:
        local_rng = None if shared else random.Random(STUDENT_ID * 10 + thread_index)
        n = TOTAL_POINTS // THREADS + (thread_index < TOTAL_POINTS % THREADS)
        inside = 0
        if shared:
            for _ in range(n):
                with lock:
                    x = prng.random()
                    y = prng.random()
                if x * x + y * y <= 1.0:
                    inside += 1
        else:
            for _ in range(n):
                x = local_rng.random()
                y = local_rng.random()
                if x * x + y * y <= 1.0:
                    inside += 1
        counts[thread_index] = inside

    started = time.perf_counter()
    workers = [threading.Thread(target=worker, args=(i,)) for i in range(THREADS)]
    for worker_thread in workers:
        worker_thread.start()
    for worker_thread in workers:
        worker_thread.join()
    elapsed_ms = (time.perf_counter() - started) * 1000
    pi_estimate = 4.0 * sum(counts) / TOTAL_POINTS
    return pi_estimate, abs(pi_estimate - math.pi), elapsed_ms


def main() -> None:
    shared_pi, shared_error, shared_ms = run_experiment(shared=True)
    independent_pi, independent_error, independent_ms = run_experiment(shared=False)
    speedup = shared_ms / independent_ms
    report = (
        'TASK 2 - Pseudo-Random Generator State Bottleneck\n'
        f'Student ID: {STUDENT_ID}\n'
        f'Logical cores: {os.cpu_count()}\n'
        f'Threads: {THREADS}\n'
        f'Total sample points per mode: {TOTAL_POINTS:,}\n\n'
        f'Shared PRNG (mutex):     pi = {shared_pi:.8f}, '
        f'absolute error = {shared_error:.8f}, time = {shared_ms:.2f} ms\n'
        f'Independent PRNGs:      pi = {independent_pi:.8f}, '
        f'absolute error = {independent_error:.8f}, time = {independent_ms:.2f} ms\n'
        f'Speedup (shared / independent): {speedup:.2f}x\n'
    )
    print(report, end='')
    OUTPUT_FILE.write_text(report, encoding='utf-8')
    print(f'Output saved to {OUTPUT_FILE.name}')


if __name__ == '__main__':
    main()
