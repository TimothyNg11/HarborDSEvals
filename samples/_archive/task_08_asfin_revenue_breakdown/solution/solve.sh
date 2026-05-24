#!/bin/bash
# Oracle: state vs local share of US-total tax revenue, 2021 ASLGF.
set -e

python3 - <<'PY'
import json
import openpyxl

wb = openpyxl.load_workbook("/data/21slsstab1.xlsx", data_only=True)
ws = wb.active

# Within the US block:
#   col index 2 = state+local combined
#   col index 4 = state government
#   col index 5 = local government
# (Column indices verified against the row label "Taxes" headers.)
state_tax = local_tax = total_tax = None
for row in ws.iter_rows(values_only=True):
    if row[1] is None:
        continue
    if str(row[1]).strip() == "Taxes":
        total_tax = row[2]
        state_tax = row[4]
        local_tax = row[5]
        break

out = {
    "state_share": round(100 * state_tax / total_tax, 2),
    "local_share": round(100 * local_tax / total_tax, 2),
}
with open("/output/result.json", "w") as f:
    json.dump(out, f)
print(out, "sum", sum(out.values()))
PY
