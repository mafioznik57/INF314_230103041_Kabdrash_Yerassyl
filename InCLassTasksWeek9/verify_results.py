import json
import math
from pathlib import Path
from common import COUNTS, ROOT


def check_close(actual, expected):
    return math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8)


def main():
    results = {}
    for letter in 'abc':
        path = ROOT / 'results' / f'exp_{letter}.json'
        if not path.is_file():
            raise FileNotFoundError(f'Missing {path}. Run run_all.py first.')
        data = json.loads(path.read_text(encoding='utf-8'))
        t1 = data['1']['runtime_s']
        assert t1 > 0
        for p in COUNTS:
            row = data[str(p)]
            tp = row['runtime_s']
            assert tp > 0
            assert check_close(row['speedup'], t1 / tp)
            assert check_close(row['efficiency_pct'], 100 * t1 / tp / p)
            if p > 1:
                assert check_close(row['karp_flatt'], (p * tp / t1 - 1) / (p - 1))
        results[letter] = data
        print(f'[PASS] Experiment {letter.upper()}: metric formulas validated')

    a, b, c = (results[k] for k in 'abc')
    aflat = 0.8 <= a['4']['karp_flatt'] / a['2']['karp_flatt'] <= 1.25 if a['2']['karp_flatt'] != 0 else False
    bslow = b['4']['runtime_s'] > b['1']['runtime_s']
    bgrowth = b['4']['karp_flatt'] > b['2']['karp_flatt']
    cfast = c['4']['runtime_s'] < c['1']['runtime_s']
    ceff = c['4']['efficiency_pct'] > 70
    checks = [('A: e(4)/e(2) between 0.80 and 1.25', aflat),
              ('B: T4 > T1', bslow), ('B: e(4) > e(2)', bgrowth),
              ('C: T4 < T1', cfast), ('C: E4 > 70%', ceff)]
    for description, ok in checks:
        print(f'[{'PASS' if ok else 'NOT MET'}] {description}')
    lines = ['# Karp-Flatt Practice Lab Results', '', 'Actual measurements from this computer.', '',
             '| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Diagnosis |',
             '|---|---:|---:|---:|---:|---:|---|']
    names = {'a': ('Serial Tail', 'Fixed serial delay; e may remain nearly constant'),
             'b': ('Lock Contention', 'Shared mutex introduces coordination overhead'),
             'c': ('Privatized', 'Local counters avoid per-increment locking')}
    for k, data in results.items():
        name, diagnosis = names[k]
        lines.append(f'| {name} | {data['1']['runtime_s']:.3f} | {data['2']['runtime_s']:.3f} | {data['4']['runtime_s']:.3f} | {data['2']['karp_flatt']:.3f} | {data['4']['karp_flatt']:.3f} | {diagnosis} |')
    lines.extend(['', '## Instructor rubric', ''])
    lines.extend(f'- {'PASS' if ok else 'NOT MET'}: {description}' for description, ok in checks)
    lines.append('\nNote: Runtime and scaling depend on CPU load, physical cores, Windows process overhead, and Python version. A failed rubric target is not a calculation failure.\n')
    (ROOT / 'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    print('Saved RESULTS.md')


if __name__ == '__main__':
    main()
