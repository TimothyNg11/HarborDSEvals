#!/bin/bash
# Oracle: share of industry-employed doctorate-holders in CS, using the
# chart's "industry" definition (Private for-profit + Self-employed).
set -e

python3 - <<'PY'
import openpyxl

wb = openpyxl.load_workbook("/data/nsf25321-tab012-001.xlsx")
ws = wb.active

# Find the "All fields" row and the "Computer and information sciences" row.
all_fields = cs = None
for row in ws.iter_rows(values_only=True):
    if row[0] == "All fields":
        all_fields = row
    elif row[0] and "Computer and information" in str(row[0]):
        cs = row

# Per the chart, industry = Private-for-profit (col index 7, 1-based)
# + Self-employed (col index 15). 0-based: 6 and 14.
ind_all = (all_fields[7] or 0) + (all_fields[15] or 0)
ind_cs  = (cs[7] or 0) + (cs[15] or 0)
share = 100 * ind_cs / ind_all

with open("/output/result.txt", "w") as f:
    f.write(f"{round(share, 2)}")
print(f"CS in industry: {ind_cs} / industry total {ind_all} = {round(share, 2)}%")
PY
