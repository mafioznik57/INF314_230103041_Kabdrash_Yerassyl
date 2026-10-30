import hashlib
import statistics
import time

import numpy as np
from common import save_json, load_params


def naive(a, b):
    m = a.shape[0]
    c = np.zeros((m, m), dtype=np.float64)
    for i in range(m):
        for j in range(m):
            value = 0.0
            for k in range(m):
                value += float(a[i, k]) * float(b[k, j])
            c[i, j] = value
    return c


def interchanged(a, b):
    m = a.shape[0]
    c = np.zeros((m, m), dtype=np.float64)
    for i in range(m):
        for k in range(m):
            c[i, :] += a[i, k] * b[k, :]
    return c


def benchmark(func, a, b):
    times = []
    result = None
    for _ in range(3):
        start = time.perf_counter()
        result = func(a, b)
        times.append(time.perf_counter() - start)
    return statistics.median(times), result


def main():
    params = load_params()
    m = params['N'] // 2
    rng = np.random.default_rng(params['seed'])
    a = rng.random((m, m))
    b = rng.random((m, m))
    print(f'Matrix block: {m} x {m}. Pure Python naive loops may take several minutes.')
    t_naive, c1 = benchmark(naive, a, b)
    t_interchanged, c2 = benchmark(interchanged, a, b)
    max_error = float(np.max(np.abs(c1 - c2)))
    # Floating-point reductions can differ in order.
    tolerance_pass = bool(np.allclose(c1, c2, rtol=1e-12, atol=1e-12))
    if not tolerance_pass:
        raise AssertionError(f'Matrix mismatch: maximum absolute error {max_error}')
    digest = hashlib.sha256(np.round(c1, 6).tobytes()).hexdigest()
    data = {'N': params['N'], 'M': m, 'naive_median_seconds': t_naive,
            'interchanged_median_seconds': t_interchanged, 'speedup': t_naive / t_interchanged,
            'max_absolute_error': max_error, 'within_tolerance': tolerance_pass,
            'rounded_sha256': digest}
    save_json('loop_interchange.json', data)
    print(data)


if __name__ == '__main__':
    main()
