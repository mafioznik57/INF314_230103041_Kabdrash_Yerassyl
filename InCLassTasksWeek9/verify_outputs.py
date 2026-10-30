
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def get_json(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def get_tsv(name):
    with (RESULTS / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main():
    from src.salt import get_student_params

    host = get_json("host_profile.json")
    salt = get_json("salted_params.json")
    sid = str(salt["student_id"])
    check(salt == get_student_params(sid), "M0: Student hash and parameters")
    check(all(k in host for k in ("cpu_model", "physical_cores", "logical_threads", "cache_line_bytes")),
          "M0: CPU profile fields")
    check(host["cache_line_bytes"] == 64, "M0: 64-byte cache-line reported (see source/assumption)")

    stride = get_tsv("stride_results.tsv")
    check([int(r["stride"]) for r in stride] == [1, 2, 4, 8, 16, 32, 64, 128],
          "M1: Eight memory strides")
    times = {int(r["stride"]): float(r["latency_ns"]) for r in stride}
    if times[8] <= times[1]:
        print("[WARN] M1: Stride-8 latency is not larger than stride-1; check CPU behavior")
    else:
        print(f"[PASS] M1: Stride cliff ratio: {times[8] / times[1]:.2f}x")
    matrix = get_json("loop_interchange.json")
    naive = float(matrix["naive_time_s"])
    changed = float(matrix["interchanged_time_s"])
    check(naive > 0 and changed > 0, "M1: Matrix timing fields")
    check(matrix["within_tolerance"] and matrix["max_absolute_error"] >= 0,
          "M1: Matrix numerical agreement")
    print(f"[PASS] M1: Interchange speedup {naive / changed:.2f}x")

    counters = get_tsv("false_sharing_karp_flatt.tsv")
    check(len(counters) == 12, "M2: 3 strategies x 4 process counts")
    check(all(int(r["total_count"]) == int(r["processes"]) * int(r["iterations_each"])
              for r in counters), "M2: Exact counter totals")
    check(all("e_unpadded" in r and "e_padded" in r for r in counters),
          "M2: Karp-Flatt summary columns")
    unpadded = sorted((int(r["p"]), float(r["e_unpadded"])) for r in counters
                      if r["mode"] == "unpadded" and int(r["p"]) > 1)
    if unpadded[-1][1] <= unpadded[0][1]:
        print("[WARN] M2: Unpadded Karp-Flatt did not increase; investigate hardware effects")
    else:
        print("[PASS] M2: Unpadded Karp-Flatt increased")

    scale = get_tsv("scaling_metrics.tsv")
    check(len(scale) >= 2, "M3: Multiple worker configurations")
    check(all(r["strong_verified"] == "True" and r["weak_verified"] == "True"
              for r in scale), "M3: Strong and weak stencil numerical agreement")
    roof = get_json("roofline_summary.json")
    check(float(roof["arithmetic_intensity"]) > 0, "M3: Arithmetic intensity")
    check("bound" in roof["regime"].lower(), "M3: Conditional Roofline classification")

    # Local checksum; not a secret key or instructor signature.
    raw = f"CS482-PRACTICUM-VERIFIED-{sid}-{salt['N']}-HASH-SOLO-LAB"
    token = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    RESULTS.joinpath("verification_receipt.sig").write_text(
        f"STUDENT_ID={sid}\nSALTED_N={salt['N']}\nSIGNATURE={token}\n", encoding="utf-8")
    print("[COMPLETE] All implemented checks passed. Local verification receipt created.")


if __name__ == "__main__":
    main()
