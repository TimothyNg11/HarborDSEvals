"""Scaffold the 10 task folders with shared files, then per-task content
must be authored manually. Runs idempotently — files already present are not
overwritten.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
CACHE = ROOT / "_data_cache"

# Map task name -> list of files to copy from cache into environment/data/
TASK_DATA = {
    "task_02_nhanes_obesity_with_ci": [
        ("NHANES_2021_2023/DEMO_L.xpt", "DEMO_L.xpt"),
        ("NHANES_2021_2023/BMX_L.xpt",  "BMX_L.xpt"),
        ("NHANES_2021_2023/DEMO_L_doc.pdf", "docs/DEMO_L.htm"),
        ("NHANES_2021_2023/BMX_L_doc.pdf",  "docs/BMX_L.htm"),
    ],
    "task_03_nhanes_obesity_by_sex": [
        ("NHANES_2021_2023/DEMO_L.xpt", "DEMO_L.xpt"),
        ("NHANES_2021_2023/BMX_L.xpt",  "BMX_L.xpt"),
        ("NHANES_2021_2023/DEMO_L_doc.pdf", "docs/DEMO_L.htm"),
        ("NHANES_2021_2023/BMX_L_doc.pdf",  "docs/BMX_L.htm"),
    ],
    "task_04_cps_median_income": [
        ("CPS_ASEC_2024/tableA1.xlsx", "tableA1.xlsx"),
    ],
    "task_05_nhis_chronic_pain_test": [
        ("NHIS_2023/adult23csv.zip", "adult23csv.zip"),
    ],
    "task_06_nhanes_sex_comparison": [
        ("NHANES_2021_2023/DEMO_L.xpt", "DEMO_L.xpt"),
        ("NHANES_2021_2023/BMX_L.xpt",  "BMX_L.xpt"),
        ("NHANES_2021_2023/DEMO_L_doc.pdf", "docs/DEMO_L.htm"),
        ("NHANES_2021_2023/BMX_L_doc.pdf",  "docs/BMX_L.htm"),
    ],
    "task_07_nsf_sdr_sector_trend": [
        ("NSF_SDR_2023/nsf25321-tab012-001.xlsx", "nsf25321-tab012-001.xlsx"),
    ],
    "task_08_asfin_revenue_breakdown": [
        ("ASFIN_2021/21slsstab1.xlsx", "21slsstab1.xlsx"),
        ("ASFIN_2021/2021_methodology.pdf", "docs/2021_methodology.pdf"),
        ("ASFIN_2021/2021alfinsummarybrief.pdf", "docs/2021alfinsummarybrief.pdf"),
    ],
    "task_09_nhanes_dietary_weights": [
        ("NHANES_2021_2023/DEMO_L.xpt", "DEMO_L.xpt"),
        ("NHANES_2021_2023/DR1TOT_L.xpt", "DR1TOT_L.xpt"),
        ("NHANES_2021_2023/DEMO_L_doc.pdf", "docs/DEMO_L.htm"),
        ("NHANES_2021_2023/DR1TOT_L_doc.pdf", "docs/DR1TOT_L.htm"),
    ],
    "task_10_nhanes_compound_subgroups": [
        ("NHANES_2021_2023/DEMO_L.xpt", "DEMO_L.xpt"),
        ("NHANES_2021_2023/BMX_L.xpt",  "BMX_L.xpt"),
        ("NHANES_2021_2023/DEMO_L_doc.pdf", "docs/DEMO_L.htm"),
        ("NHANES_2021_2023/BMX_L_doc.pdf",  "docs/BMX_L.htm"),
    ],
}


def main():
    for task, files in TASK_DATA.items():
        tdir = SAMPLES / task
        (tdir / "environment" / "data" / "docs").mkdir(parents=True, exist_ok=True)
        (tdir / "solution").mkdir(parents=True, exist_ok=True)
        (tdir / "tests").mkdir(parents=True, exist_ok=True)
        for src, dst in files:
            src_p = CACHE / src
            dst_p = tdir / "environment" / "data" / dst
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            if not dst_p.exists() and src_p.exists():
                shutil.copy(src_p, dst_p)
                print(f"  copied {src_p.name} -> {task}/environment/data/{dst}")
    print("scaffold complete")


if __name__ == "__main__":
    main()
