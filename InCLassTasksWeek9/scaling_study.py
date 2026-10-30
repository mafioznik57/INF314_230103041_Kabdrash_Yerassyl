import csv
import math
import multiprocessing as mp
import os
import time

import numpy as np
from common import RESULTS, load_params, save_json

REPEATS = 40


def stencil(chunk):
    # Four-neighbor average on each interior row.
    top = chunk[:-2, 1:-1]
    bottom = chunk[2:, 1:-1]
    left = chunk[1:-1, :-2]
    right = chunk[1:-1, 2:]
    out = np.empty_like(top)
    for _ in range(REPEATS):
        np.add(top, bottom, out=out)
        out += left
        out += right
        out *= 0.25
    return out


def split_work(matrix, p):
    # Each chunk contains one halo row on both sides.
    sections = np.array_split(np.arange(1, matrix.shape[0] - 1), p)
    return [matrix[ids[0] - 1:ids[-1] + 2, :] for ids in sections if len(ids)]


def run(matrix, p, pool=None):
    chunks = split_work(matrix, p)
    start = time.perf_counter()
    if pool:
        pieces = pool.map(stencil, chunks)
    else:
        pieces = [stencil(chunk) for chunk in chunks]
    elapsed = time.perf_counter() - start
    output = np.concatenate(pieces, axis=0)
    return elapsed, output


def main():
    params = load_params()
    n = params['N']
    rng = np.random.default_rng(params['seed'])
    matrix = rng.random((n, n), dtype=np.float64)
    logical = os.cpu_count() or 1
    try:
        import json
        profile = json.loads((RESULTS / 'host_profile.json').read_text())
        physical = profile['cpu']['physical_cores'] or logical
    except (FileNotFoundError, KeyError):
        physical = logical
    counts = [1]
    p = 2
    while p <= physical:
        counts.append(p)
        p *= 2
    if physical not in counts and physical > 1:
        counts.append(physical)
    counts = sorted(set(counts))
    baseline_time, reference = run(matrix, 1)
    rows = []
    for p in counts:
        # Pool initialization is excluded from execution time.
        if p == 1:
            strong_time, strong_out = baseline_time, reference
        else:
            with mp.Pool(p) as pool:
                strong_time, strong_out = run(matrix, p, pool)
        if not np.allclose(strong_out, reference, rtol=1e-12, atol=1e-12):
            raise AssertionError(f'Strong scaling output differs for P={p}')
        strong_speedup = baseline_time / strong_time
        serial = ((1 / strong_speedup) - (1 / p)) / (1 - 1 / p) if p > 1 else None
        weak_n = math.ceil(n * math.sqrt(p))
        weak_matrix = np.random.default_rng(params['seed']).random((weak_n, weak_n))
        if p == 1:
            weak_time, weak_out = run(weak_matrix, 1)
        else:
            with mp.Pool(p) as pool:
                weak_time, weak_out = run(weak_matrix, p, pool)
        # Validation uses a sequential reference computed outside the timed region.
        _, weak_reference = run(weak_matrix, 1)
        if not np.allclose(weak_out, weak_reference, rtol=1e-12, atol=1e-12):
            raise AssertionError(f'Weak scaling output differs for P={p}')
        work1 = (n - 2) ** 2
        workp = (weak_n - 2) ** 2
        scaled_speedup = p * work1 * baseline_time / (workp * weak_time)
        row = {'processes': p, 'strong_n': n, 'strong_seconds': round(strong_time, 6),
               'strong_speedup': round(strong_speedup, 6),
               'strong_efficiency_percent': round(100 * strong_speedup / p, 4),
               'effective_serial_fraction': round(serial, 6) if serial is not None else '',
               'weak_n': weak_n, 'weak_seconds': round(weak_time, 6),
               'scaled_speedup_spec_formula': round(scaled_speedup, 6),
               'weak_throughput_ratio': round((workp / weak_time) / (work1 / baseline_time), 6),
               'strong_checksum': round(float(np.sum(strong_out)), 6),
               'weak_checksum': round(float(np.sum(weak_out)), 6),
               'strong_verified': True, 'weak_verified': True}
        rows.append(row)
        print(row)
    with (RESULTS / 'scaling_metrics.tsv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    # One stencil output: 4 adds/multiplies and ~5 double transfers (no cache reuse).
    flops_per_point = 4
    bytes_per_point = 5 * 8
    ai = flops_per_point / bytes_per_point
    usable_serial = [float(row['effective_serial_fraction']) for row in rows if row['effective_serial_fraction'] != '' and float(row['effective_serial_fraction']) > 0]
    summary = {'kernel': '4-neighbor stencil average, repeated on original inputs',
               'repeats': REPEATS, 'flops_per_output': flops_per_point,
               'estimated_bytes_per_output_without_cache_reuse': bytes_per_point,
               'arithmetic_intensity_flops_per_byte': ai,
               'cpu_peak_flops_per_second': None, 'peak_memory_bandwidth_bytes_per_second': None,
               'roofline_bound': 'undetermined_without_hardware_peak_measurements',
               'important_note': 'DRAM bytes are an upper estimate ignoring cache reuse; observed arithmetic intensity requires hardware counters.',
               'effective_serial_fraction_positive_median': float(np.median(usable_serial)) if usable_serial else None,
               'amdahl_max_speedup_if_positive_s': (1 / float(np.median(usable_serial))) if usable_serial else None,
               'note': 'Negative effective serial fractions are possible under measurement noise or superlinear speedup.'}
    save_json('roofline_summary.json', summary)


if __name__ == '__main__':
    mp.freeze_support()
    main()
