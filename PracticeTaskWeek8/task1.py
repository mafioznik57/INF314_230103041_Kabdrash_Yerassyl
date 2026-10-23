"""Task 1: parallel row-major versus column-major cache traversal.

Requirements: Python 3.10+, numpy, numba, psutil.
Install: python -m pip install numpy numba psutil
Run:     python task1.py
"""

import os
import time
from pathlib import Path

import numpy as np
import psutil
from numba import njit, prange, set_num_threads, get_num_threads

STUDENT_ID = 230103041
SIZE = 8000
OUTPUT_FILE = Path(__file__).with_name("task1_output.txt")


@njit(parallel=True)
def row_major_sum(matrix, workers):
    partial = np.zeros(workers, dtype=np.float64)
    nrows, ncols = matrix.shape
    for worker in prange(workers):
        start = worker * nrows // workers
        end = (worker + 1) * nrows // workers
        acc = 0.0
        for i in range(start, end):
            for j in range(ncols):
                acc += matrix[i, j]
        partial[worker] = acc
    return np.sum(partial)


@njit(parallel=True)
def column_major_sum(matrix, workers):
    partial = np.zeros(workers, dtype=np.float64)
    nrows, ncols = matrix.shape
    for worker in prange(workers):
        start = worker * ncols // workers
        end = (worker + 1) * ncols // workers
        acc = 0.0
        for j in range(start, end):
            for i in range(nrows):
                acc += matrix[i, j]
        partial[worker] = acc
    return np.sum(partial)


def measure(func, matrix, workers):
    start = time.perf_counter()
    result = func(matrix, workers)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


def main():
    logical_cores = os.cpu_count() or 1
    physical_cores = psutil.cpu_count(logical=False) or logical_cores
    workers = min(physical_cores, get_num_threads())
    set_num_threads(workers)

    rng = np.random.default_rng(STUDENT_ID)
    matrix = rng.random((SIZE, SIZE), dtype=np.float64)


    small = matrix[:8, :8].copy()
    row_major_sum(small, workers)
    column_major_sum(small, workers)

    row_result, row_ms = measure(row_major_sum, matrix, workers)
    col_result, col_ms = measure(column_major_sum, matrix, workers)
    if not np.isclose(row_result, col_result, rtol=1e-10, atol=1e-5):
        raise RuntimeError("Traversal sums do not match!")

    penalty = col_ms / row_ms
    report = (
        f"Student ID: {STUDENT_ID}\n"
        f"Logical cores: {logical_cores}\n"
        f"Physical cores: {physical_cores}\n"
        f"Parallel workers used: {workers}\n"
        f"Matrix: {SIZE} x {SIZE}, float64, C-contiguous\n"
        f"Mode A (Row-Major): {row_ms:.3f} ms\n"
        f"Mode B (Column-Major / Strided): {col_ms:.3f} ms\n"
        f"Cache penalty factor (B / A): {penalty:.2f}x\n"
        f"Row sum: {row_result:.6f}\n"
        f"Column sum: {col_result:.6f}\n"
        "Validation: PASS (sums match within floating-point tolerance)\n"
    )
    print(report, end="")
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(f"Saved: {OUTPUT_FILE.name}")


if __name__ == "__main__":
    main()
