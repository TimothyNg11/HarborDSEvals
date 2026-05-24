#!/bin/bash
# Run the rule-precedence prompt intervention on 5 tasks (T05-T09), both models.
# Tasks are in samples_intervention/ (verifier identical to samples/, only
# instruction.md has the prepended rule-semantics block).
#
# Usage: scripts/run_intervention.sh [gemini|haiku|both]   (default: both)
set -u
cd "$(dirname "$0")/.."

source scripts/load_env.sh
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY not loaded from .env}"
: "${GEMINI_API_KEY:?GEMINI_API_KEY not loaded from .env}"

WHICH="${1:-both}"

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

run_arm() {
    local label="$1"      # gemini | haiku
    local agent="$2"      # gemini-cli | claude-code
    local model="$3"
    local apikey_var="$4" # GEMINI_API_KEY | ANTHROPIC_API_KEY
    local outdir="jobs/intervention_${label}"
    mkdir -p "$outdir"

    for task_dir in samples_intervention/task_*; do
        task=$(basename "$task_dir")
        job="${task}_intv_${label}"
        if [ -f "${outdir}/${job}/result.json" ]; then
            echo "==================== [${label}] $task (cached) ===================="
            continue
        fi
        echo "==================== [${label}] $task ===================="
        rm -rf "${outdir}/${job}"
        harbor run -p "$task_dir" \
            -a "$agent" \
            -m "$model" \
            --ae "${apikey_var}=${!apikey_var}" \
            -o "$outdir" \
            --job-name "$job" \
            -k 3 -n 2 -y -q 2>&1 | tail -10
    done
}

if [ "$WHICH" = "gemini" ] || [ "$WHICH" = "both" ]; then
    run_arm gemini gemini-cli google/gemini-3-flash-preview GEMINI_API_KEY
fi
if [ "$WHICH" = "haiku" ] || [ "$WHICH" = "both" ]; then
    run_arm haiku claude-code claude-haiku-4-5-20251001 ANTHROPIC_API_KEY
fi

echo
echo "==================== INTERVENTION SUMMARY ===================="
python - <<'PY'
import json, os, glob
for arm_label in ('gemini', 'haiku'):
    arm_dir = f'jobs/intervention_{arm_label}'
    if not os.path.isdir(arm_dir):
        continue
    print(f"\n--- {arm_label} ---")
    rows = []
    for f in sorted(glob.glob(f'{arm_dir}/*/result.json')):
        task = os.path.basename(os.path.dirname(f)).replace(f'_intv_{arm_label}', '')
        r = json.load(open(f))
        evals = r['stats']['evals']
        ek = next(iter(evals))
        rs = evals[ek].get('reward_stats', {}).get('reward', {})
        rewards = []
        for reward_str, ids in rs.items():
            for _ in ids:
                rewards.append(float(reward_str))
        pa3 = 1.0 if any(r == 1.0 for r in rewards) else 0.0
        print(f"  {task}: rewards={rewards}  pass@3={pa3}")
        rows.append((task, pa3))
    if rows:
        agg = sum(p for _, p in rows) / len(rows)
        print(f"  Aggregate pass@3: {100*agg:.1f}%")
PY
