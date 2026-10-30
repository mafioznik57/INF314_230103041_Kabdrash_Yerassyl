# Karp–Flatt Practice Lab

Python 3.8+ standard library only. On Windows, use Python 3.13 or newer if available.

## Student ID

Open `run_all.py` and change the one line:

```python
STUDENT_ID = '230103041'  # ENTER YOUR STUDENT ID HERE
```

## Run (VS Code terminal / Windows PowerShell)

From the extracted project folder, run:

```powershell
& C:\python313\python.exe run_all.py
```

Or `py run_all.py` if `py` is configured. The launcher runs all three experiments and verifies calculations. Results are saved as `results/exp_a.json`, `exp_b.json`, `exp_c.json`, and `RESULTS.md`. To verify saved data again:

```powershell
& C:\python313\python.exe verify_results.py
```

**Do not launch the scripts using VS Code's `Run Selection/Line` command**. Run the whole `.py` file, since Windows multiprocessing requires `if __name__ == '__main__'`.

## Experiments

- A: 0.40 s fixed serial delay and 16 compute chunks, P = 1, 2, 4.
- B: 2,000,000 increments protected by one shared lock, P = 1, 2, 4.
- C: 20,000,000 private increments summed once after worker completion, P = 1, 2, 4.

Speedup = T1/Tp, efficiency = 100 × speedup/p, and Karp–Flatt e(p) = (p × Tp/T1 - 1)/(p - 1).

`verify_results.py` checks saved metric formulas, reports which instructor rubric thresholds were met, and writes `RESULTS.md`. It does not invent timings or force passing performance thresholds. The scripts may run more slowly on Windows due to Python worker startup and CPU contention. The handout's example times are not guaranteed on your hardware. Experiment A's stated serial fraction is not universal: it depends on the time spent in the compute phase.

## Git

The handout asks you to use the assigned course repository and student branch. When you know your assigned remote URL:

```powershell
git checkout -b practice-230103041
git add .
git commit -m "Completed Karp-Flatt practice lab"
git push -u origin practice-230103041
```

Do not overwrite an existing instructor repository. Follow their course-specific Git instructions for where to push.
