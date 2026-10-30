import csv
import statistics
import time

import numpy as np
from common import RESULTS, load_params


def main():
    params = load_params()
    data = np.ones(params['buffer_elements'], dtype=np.float64)
    rows = []
    for stride in [1, 2, 4, 8, 16, 32, 64, 128]:
        view = data[::stride]
        for _ in range(5):
            np.sum(view)
        times = []
        for _ in range(5):
            start = time.perf_counter_ns()
            total = float(np.sum(view))
            times.append(time.perf_counter_ns() - start)
            assert total == len(view)
        median = statistics.median(times)
        rows.append({'stride': stride, 'elements_touched': len(view),
                     'median_time_ns': median, 'ns_per_element': round(median / len(view), 5)})
        print(rows[-1])
    with (RESULTS / 'stride_results.tsv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    main()
