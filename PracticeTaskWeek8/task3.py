
import os
import time
import numpy as np
from numba import njit, prange, set_num_threads, get_num_threads

STUDENT_ID = 230103041
ARRAY_SIZE = 2_000_000
REPEATS = 5


@njit
def serial_scan(values):
    output = np.empty(values.size, dtype=np.int64)
    running = np.int64(0)
    for i in range(values.size):
        running += values[i]
        output[i] = running
    return output


@njit(parallel=True)
def local_scans(values, result, chunk_totals, chunk_size):
    for chunk in prange(chunk_totals.size):
        start = chunk * chunk_size
        end = min(start + chunk_size, values.size)
        running = np.int64(0)
        for i in range(start, end):
            running += values[i]
            result[i] = running
        chunk_totals[chunk] = running


@njit(parallel=True)
def apply_offsets(result, offsets, chunk_size):

    for chunk in prange(offsets.size):
        offset = offsets[chunk]
        start = chunk * chunk_size
        end = min(start + chunk_size, result.size)
        for i in range(start, end):
            result[i] += offset


def parallel_scan(values, workers):
    chunk_size = (values.size + workers - 1) // workers
    chunks = (values.size + chunk_size - 1) // chunk_size
    result = np.empty(values.size, dtype=np.int64)
    totals = np.empty(chunks, dtype=np.int64)
    local_scans(values, result, totals, chunk_size)

    offsets = np.empty(chunks, dtype=np.int64)
    running = 0
    for chunk in range(chunks):
        offsets[chunk] = running
        running += int(totals[chunk])

    apply_offsets(result, offsets, chunk_size)
    return result


def benchmark(fn):
    timings = []
    result = None
    for _ in range(REPEATS):
        start = time.perf_counter()
        result = fn()
        timings.append((time.perf_counter() - start) * 1000)
    return min(timings), result


def main():
    workers = min(os.cpu_count() or 1, 8)
    set_num_threads(workers)
    rng = np.random.default_rng(STUDENT_ID)
    values = rng.integers(1, 11, size=ARRAY_SIZE, dtype=np.int64)


    serial_scan(values[:10])
    parallel_scan(values[:10], workers)

    serial_ms, serial_output = benchmark(lambda: serial_scan(values))
    parallel_ms, parallel_output = benchmark(lambda: parallel_scan(values, workers))

    try:
        assert parallel_output[-1] == serial_output[-1]

        assert np.array_equal(parallel_output, serial_output)
        status = 'PASS'
    except AssertionError:
        status = 'FAIL'

    lines = [
        f'Student ID: {STUDENT_ID}',
        f'Array size: {ARRAY_SIZE:,}',
        f'Workers: {get_num_threads()}',
        f'Serial Time (ms): {serial_ms:.3f}',
        f'Parallel Time (ms): {parallel_ms:.3f}',
        f'Speedup: {serial_ms / parallel_ms:.3f}x',
        f'Verification Status: {status}',
        f'Final prefix sum: {int(serial_output[-1])}',
        f'Timing: best of {REPEATS} runs, excluding JIT compilation',
    ]
    report = '\n'.join(lines)
    print(report)
    with open('task3_output.txt', 'w', encoding='utf-8') as file:
        file.write(report + '\n')
    if status == 'FAIL':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
