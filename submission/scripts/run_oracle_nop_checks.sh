#!/bin/bash
# Run oracle (expect reward=1) and nop (expect reward=0) on every task.
set -u
cd "$(dirname "$0")/.."

mkdir -p jobs
export PYTHONIOENCODING=utf-8

PASS_ORACLE=0
PASS_NOP=0
FAIL_TASKS=()

for task_dir in samples/task_*/; do
    task=$(basename "$task_dir")
    echo "==================== $task ===================="

    # Oracle
    out_oracle="jobs/${task}_oracle"
    rm -rf "$out_oracle"
    harbor run -p "$task_dir" -a oracle -o jobs --job-name "${task}_oracle" -n 1 -y -q 2>&1 | tail -3
    oracle_reward=$(python -c "
import json
r = json.load(open('jobs/${task}_oracle/result.json'))
print(r['stats']['evals']['oracle__adhoc']['metrics'][0]['mean'])
" 2>/dev/null || echo "0")
    echo "  oracle reward: $oracle_reward"

    # Nop
    out_nop="jobs/${task}_nop"
    rm -rf "$out_nop"
    harbor run -p "$task_dir" -a nop -o jobs --job-name "${task}_nop" -n 1 -y -q 2>&1 | tail -3
    nop_reward=$(python -c "
import json
r = json.load(open('jobs/${task}_nop/result.json'))
print(r['stats']['evals']['nop__adhoc']['metrics'][0]['mean'])
" 2>/dev/null || echo "0")
    echo "  nop reward: $nop_reward"

    if [ "$oracle_reward" = "1.0" ]; then PASS_ORACLE=$((PASS_ORACLE+1)); else FAIL_TASKS+=("$task:oracle=$oracle_reward"); fi
    if [ "$nop_reward" = "0.0" ];   then PASS_NOP=$((PASS_NOP+1));   else FAIL_TASKS+=("$task:nop=$nop_reward"); fi
done

echo
echo "==================== SUMMARY ===================="
echo "Oracle passed:  $PASS_ORACLE / 10"
echo "Nop returned 0: $PASS_NOP / 10"
if [ "${#FAIL_TASKS[@]}" -gt 0 ]; then
    echo "FAILED:"
    for f in "${FAIL_TASKS[@]}"; do echo "  - $f"; done
fi
