#!/bin/bash
# Oracle: Asian / White-non-Hispanic median household income ratio in 2023.
set -e

python3 - <<'PY'
import openpyxl

wb = openpyxl.load_workbook("/data/tableA1.xlsx", data_only=True)
ws = wb.active

asian = white_nh = None
for row in ws.iter_rows(values_only=True):
    if row[0] is None:
        continue
    s = str(row[0]).lstrip(".").strip().lower()
    # Match the indented sub-categories exactly.
    if s == "asian":
        asian = row[5]
    elif s == "white, not hispanic":
        white_nh = row[5]

ratio = 100 * asian / white_nh
with open("/output/result.txt", "w") as f:
    f.write(f"{round(ratio, 2)}")
print(f"Asian {asian} / White-NH {white_nh} = {round(ratio, 2)}%")
PY
