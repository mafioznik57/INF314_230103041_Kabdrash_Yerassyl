import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'


def read_json(name):
    return json.loads((RESULTS / name).read_text())


def read_tsv(name):
    with (RESULTS / name).open(newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print('[PASS]', message)


def main():
    from src.salt import get_student_params
    params = read_json('salted_params.json')
    host = read_json('host_profile.json')
    check(params == get_student_params(params['student_id']) and bool(host['cpu']['model']), 'M0 parameters and CPU profile')
    stride = read_tsv('stride_results.tsv')
    check([int(row['stride']) for row in stride] == [1, 2, 4, 8, 16, 32, 64, 128], 'M1 stride coverage')
    matrix = read_json('loop_interchange.json')
    check(matrix['within_tolerance'] and matrix['max_absolute_error'] >= 0, 'M1 matrix comparison')
    counters = read_tsv('false_sharing_karp_flatt.tsv')
    check(len(counters) == 12 and all(int(row['total_count']) == int(row['processes']) * int(row['iterations_each']) for row in counters), 'M2 counter totals')
    scaling = read_tsv('scaling_metrics.tsv')
    check(len(scaling) >= 1 and all(row['strong_verified'] == 'True' and row['weak_verified'] == 'True' for row in scaling), 'M3 stencil comparisons')
    roofline = read_json('roofline_summary.json')
    check(roofline['arithmetic_intensity_flops_per_byte'] > 0, 'M3 arithmetic intensity')
    # This is a local integrity receipt, not the instructor-provided signature.
    files = ['host_profile.json', 'salted_params.json', 'stride_results.tsv',
             'loop_interchange.json', 'false_sharing_karp_flatt.tsv',
             'scaling_metrics.tsv', 'roofline_summary.json']
    digest = hashlib.sha256()
    for name in files:
        digest.update(name.encode())
        digest.update((RESULTS / name).read_bytes())
    (RESULTS / 'verification_receipt.sig').write_text(digest.hexdigest() + '\n')
    print('Local SHA-256 receipt written (not an instructor-issued signature).')


if __name__ == '__main__':
    main()
