"""Download federal survey data and documentation for the Abundant eval.

Run from repo root: python scripts/download_federal_data.py
Downloads are cached in _data_cache/ and copied into each task's environment/data/
folder via prepare_task_data.py.
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parent.parent / "_data_cache"
CACHE_DIR.mkdir(exist_ok=True)

DATA_SOURCES = {
    "NHANES_2021_2023": {
        "DEMO_L.xpt": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.xpt",
        "BMX_L.xpt":  "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.xpt",
        "DR1TOT_L.xpt": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DR1TOT_L.xpt",
        "DR1IFF_L.xpt": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DR1IFF_L.xpt",
        "DEMO_L_doc.pdf": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm",
        "BMX_L_doc.pdf":  "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.htm",
        "DR1TOT_L_doc.pdf": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DR1TOT_L.htm",
    },
    "NHIS_2023": {
        "adult23.csv":  "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2023/adult23csv.zip",
    },
    "CPS_ASEC_2024": {
        "h08ar.xlsx": "https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-income-households/h08ar.xlsx",
    },
    "NSF_SDR_2023": {
        "nsf25320_tab001.xlsx": "https://ncses.nsf.gov/pubs/nsf25320/assets/data-tables/tables/nsf25320-tab001.xlsx",
        "nsf25320_tab002.xlsx": "https://ncses.nsf.gov/pubs/nsf25320/assets/data-tables/tables/nsf25320-tab002.xlsx",
    },
    "ASFIN_2021": {
        "asfin_2021.csv": "https://www2.census.gov/programs-surveys/state/datasets/2021/2021-asfin-summary-table.xlsx",
    },
}

USER_AGENT = "AbundantResearchEvalBot/1.0 (research; contact: takehome)"


def fetch(url: str, dest: Path, retries: int = 3) -> bool:
    """Fetch a URL with retries; return True on success."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=120) as r:
                data = r.read()
            dest.write_bytes(data)
            print(f"  OK ({len(data)/1024:.1f} KB) -> {dest.name}")
            return True
        except Exception as e:
            print(f"  attempt {attempt+1}/{retries} failed: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    return False


def main() -> int:
    failures = []
    for survey, files in DATA_SOURCES.items():
        survey_dir = CACHE_DIR / survey
        survey_dir.mkdir(exist_ok=True)
        print(f"\n== {survey} ==")
        for fname, url in files.items():
            dest = survey_dir / fname
            if dest.exists() and dest.stat().st_size > 0:
                print(f"  cached: {fname}")
                continue
            print(f"  fetching {fname} from {url}")
            if not fetch(url, dest):
                failures.append(f"{survey}/{fname}")
    if failures:
        print("\nFAILED downloads:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nAll downloads complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
