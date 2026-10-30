import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
RESULTS.mkdir(exist_ok=True)


def save_json(name, data):
    (RESULTS / name).write_text(json.dumps(data, indent=2), encoding='utf-8')


def load_params():
    path = RESULTS / 'salted_params.json'
    if not path.exists():
        raise RuntimeError('Run python src/profile_env.py --student-id YOUR_8_DIGIT_ID first')
    return json.loads(path.read_text(encoding='utf-8'))
