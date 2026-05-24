#!/bin/bash
# Run 3 Claude-Haiku-4.5 trials per DABstep task via Harbor's claude-code agent.
# Mirrors `run_gemini_trials.sh` so the multi-model results are directly comparable.
set -u
cd "$(dirname "$0")/.."

source scripts/load_env.sh
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY not loaded from .env}"

mkdir -p jobs/haiku
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

# Optional: pass a task name as first arg to run only that task.
if [ $# -ge 1 ]; then
    tasks=("samples/$1")
else
    tasks=(samples/task_*)
fi

for task_dir in "${tasks[@]}"; do
    task=$(basename "$task_dir")
    # Skip archive dirs (which match samples/task_* via the _archive prefix check below)
    [[ "$task" == _archive* ]] && continue
    job="${task}_haiku"
    if [ -f "jobs/haiku/${job}/result.json" ]; then
        echo "==================== $task (cached) ===================="
        continue
    fi
    echo "==================== $task ===================="
    rm -rf "jobs/haiku/${job}"
    harbor run -p "$task_dir" \
        -a claude-code \
        -m claude-haiku-4-5-20251001 \
        --ae "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" \
        -o jobs/haiku \
        --job-name "$job" \
        -k 3 -n 2 -y -q 2>&1 | tail -10
done

echo
echo "==================== SUMMARY ===================="
python - <<'PY'
import json, os, glob
results = []
for f in sorted(glob.glob('jobs/haiku/*_haiku/result.json')):
    task = os.path.basename(os.path.dirname(f)).replace('_haiku', '')
    r = json.load(open(f))
    evals = r['stats']['evals']
    ek = next(iter(evals))
    rs = evals[ek].get('reward_stats', {}).get('reward', {})
    rewards = []
    for reward_str, ids in rs.items():
        for _ in ids:
            rewards.append(float(reward_str))
    pa1 = float(rewards[0]) if rewards else 0.0
    pa3 = 1.0 if any(rewards) else 0.0
    print(f"{task}: rewards={rewards}  pass@1={pa1}  pass@3={pa3}")
    results.append(dict(task=task, rewards=rewards, pa1=pa1, pa3=pa3))

agg_pa1 = sum(r['pa1'] for r in results) / max(1, len(results))
agg_pa3 = sum(r['pa3'] for r in results) / max(1, len(results))
print(f"\nAggregate pass@1: {100*agg_pa1:.1f}%")
print(f"Aggregate pass@3: {100*agg_pa3:.1f}%")
PY
