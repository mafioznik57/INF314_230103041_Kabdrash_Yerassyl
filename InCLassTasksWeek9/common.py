import json
import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COUNTS = (1, 2, 4)


def metrics(times):
    base = times[1]
    return {p: {
        'runtime_s': times[p],
        'speedup': base / times[p],
        'efficiency_pct': 100 * base / times[p] / p,
        'karp_flatt': None if p == 1 else (p * times[p] / base - 1) / (p - 1),
    } for p in COUNTS}


def save(name, data):
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results' / name).write_text(json.dumps(data, indent=2), encoding='utf-8')


def profile():
    return {'os': platform.platform(), 'processor': platform.processor(), 'logical_cores': os.cpu_count(), 'python': platform.python_version()}
