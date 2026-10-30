import subprocess
import sys
from pathlib import Path

STUDENT_ID = "230103041"

ROOT = Path(__file__).resolve().parent


def main():
    if not (STUDENT_ID.isdigit() and len(STUDENT_ID) == 9):
        raise ValueError("Edit STUDENT_ID in run_all.py with your 9-digit ID")

    scripts = [
        "profile_env.py",
        "stride_bench.py",
        "dense_kernel.py",
        "false_sharing.py",
        "scaling_study.py",
    ]
    for script in scripts:
        command = [sys.executable, str(ROOT / "src" / script)]
        if script == "profile_env.py":
            command += ["--student-id", STUDENT_ID]
        print(f"Running {script}", flush=True)
        subprocess.run(command, cwd=ROOT, check=True)

    subprocess.run([sys.executable, str(ROOT / "verify_outputs.py")], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
