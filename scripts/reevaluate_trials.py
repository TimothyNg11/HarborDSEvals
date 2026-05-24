"""Re-evaluate gemini's existing trial answers against the corrected
ground truth for T11-T14. Reads each trial's gemini-cli.txt, extracts the
final answer line, applies the (new) verifier logic, and reports
per-trial PASS/FAIL.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs" / "gemini"

# (task_dir_name, ground_truth, tol, mode) for each of T11-T14.
# Mode: "number" (numeric with tolerance) or "list" (comma-sep set match).
TASKS = [
    ("task_11_dabstep_orig_belles_total_2023", 6764.6140, 0.001, "number"),
    ("task_12_dabstep_orig_belles_mcc_counterfactual", 6690.6460, 0.001, "number"),
    ("task_13_dabstep_orig_fee_ids_nonzero_merchants",
     "12,16,17,29,36,38,51,53,64,65,79,84,89,95,107,123,134,141,150,154,162,163,183,187,217,229,231,249,257,276,280,284,286,300,304,319,332,347,359,364,367,381,384,394,398,427,428,431,433,454,456,459,470,471,473,477,485,491,498,501,503,536,547,556,572,595,608,612,616,622,626,631,634,637,640,648,660,678,680,682,700,701,702,704,709,721,722,725,741,769,787,792,804,813,834,849,858,861,863,868,870,871,878,884,888,891,892,895,899,913,915,921,924,939,942,960,980,996",
     None, "list"),
    ("task_14_dabstep_orig_crossfit_monthly_sd", 117.857204, 0.0001, "number"),
]


def extract_final_number(text: str) -> float | None:
    """Find the last standalone number in the transcript that looks like an
    answer.txt content (not embedded in a sentence)."""
    # Look at the last 200 lines
    lines = text.splitlines()[-300:]
    candidates = []
    for line in reversed(lines):
        line = line.strip().strip("`*").strip()
        # Skip prose lines
        if not line or len(line) > 60: continue
        # Try to parse as a number
        s = line.replace(",", "").replace("EUR", "").strip()
        if s.startswith("+"): s = s[1:]
        try:
            v = float(s)
            candidates.append(v)
            if len(candidates) >= 1:
                break
        except ValueError:
            continue
    return candidates[0] if candidates else None


def extract_final_list(text: str) -> set[int] | None:
    """Find the last long comma-separated integer list."""
    lines = text.splitlines()[-200:]
    for line in reversed(lines):
        line = line.strip().strip("`*\"' ")
        # Must be mostly digits+commas, long
        if len(line) < 100: continue
        if not re.match(r"^[\d,\s]+$", line): continue
        try:
            return set(int(x.strip()) for x in line.split(",") if x.strip())
        except ValueError:
            continue
    return None


def main():
    summary = {}
    for task_name, truth, tol, mode in TASKS:
        task_dir = JOBS / f"{task_name}_gemini"
        rewards = []
        for trial in sorted(task_dir.glob("task_*")):
            cli = trial / "agent" / "gemini-cli.txt"
            if not cli.exists():
                rewards.append((trial.name[-7:], None, "no transcript"))
                continue
            text = cli.read_text(errors="replace")
            if mode == "number":
                pred = extract_final_number(text)
                if pred is None:
                    rewards.append((trial.name[-7:], None, "no number found"))
                    continue
                ok = abs(pred - float(truth)) <= tol
                rewards.append((trial.name[-7:], 1 if ok else 0, f"pred={pred}"))
            else:  # list
                pred = extract_final_list(text)
                if pred is None:
                    rewards.append((trial.name[-7:], None, "no list found"))
                    continue
                truth_set = set(int(x) for x in truth.split(","))
                ok = pred == truth_set
                missing = sorted(truth_set - pred)
                extra = sorted(pred - truth_set)
                rewards.append((trial.name[-7:], 1 if ok else 0,
                                f"|pred|={len(pred)} missing={missing[:3]} extra={extra[:3]}"))

        n_pass = sum(1 for _, r, _ in rewards if r == 1)
        passat3 = 1 if n_pass >= 1 else 0
        pass1 = n_pass / max(1, len(rewards))
        summary[task_name] = (rewards, pass1, passat3)
        print(f"\n=== {task_name} ===")
        print(f"  truth: {truth if not isinstance(truth, str) else f'set({len(truth.split(chr(44)))})'}, tol: {tol}")
        for tid, r, det in rewards:
            print(f"  trial {tid}: reward={r}  {det}")
        print(f"  pass@1 = {pass1:.2f}, pass@3 = {passat3}")

    print("\n\n=== Summary ===")
    for t, (_, p1, p3) in summary.items():
        print(f"  {t}: pass@1={p1:.2f}  pass@3={p3}")


if __name__ == "__main__":
    main()
