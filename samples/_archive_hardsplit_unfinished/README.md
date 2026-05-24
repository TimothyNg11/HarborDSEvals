# Archive: unfinished DABstep hard-split tasks (T11–T25)

These 15 task directories were scaffolded by
[`scripts/build_dabstep_full_hardsplit.py`](../../scripts/build_dabstep_full_hardsplit.py)
as the start of an intended 25-task reproduction. They were **never
completed** — the DABstep `default` (hard) split has no public ground-truth
answers, and the fee-engine effort to compute substitute ground truth was
descoped before the verifiers could be filled in.

**Each verifier here has `GROUND_TRUTH = ''`** — every run fails the
verifier regardless of the agent's answer. Do not run these as a baseline.

The final repo scope is the 10 DABstep dev-split tasks in `../task_NN_*`
(which have published answers). If a future reviewer wants to extend the
reproduction to the hard split, they can:

1. Compute ground truth via the fee engine for the deterministic-math tasks
   (see [`../../ENGINE.md`](../../ENGINE.md)).
2. Embed the computed answers into each verifier's `GROUND_TRUTH` constant.
3. Move the resulting tasks back into `samples/`.
