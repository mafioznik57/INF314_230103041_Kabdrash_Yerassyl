import subprocess
import sys
from pathlib import Path
from common import profile, save

STUDENT_ID = '230103041'  
ROOT = Path(__file__).resolve().parent


def main():
    if not STUDENT_ID.isdigit():
        raise ValueError('STUDENT_ID must contain digits only')
    save('host_profile.json', {'student_id': STUDENT_ID, **profile()})
    for script in ('exp_a_serial.py', 'exp_b_contention.py', 'exp_c_fixed.py'):
        print(f'\nRunning {script}', flush=True)
        subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / 'verify_results.py')], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
