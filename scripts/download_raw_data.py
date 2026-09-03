"""Download official CMS Florida hospital and patient-experience source extracts."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


# Why: Dataset identifiers are stable CMS references, so the downloader keeps
# working when CMS refreshes the underlying distribution files.
CMS_API_ROOT = "https://data.cms.gov/provider-data/api/1/datastore/query"
DATASETS = {
    "hospital_general_information": "xubh-q36u",
    "patient_survey_hcahps": "dgck-syfz",
}

# Why: CMS limits API responses. A 1,500-row page is the documented maximum and
# lets the script collect every Florida HCAHPS record through safe pagination.
PAGE_SIZE = 1_500

# Why: The project begins with all Florida hospitals for a valid state benchmark;
# later EDA will focus on the Miami-Dade and Broward County subset.
STATE_FILTER = "FL"

# Why: Source extracts and their provenance remain separate from later cleaned,
# local-analysis data so the project has an auditable data lineage.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_FILE = RAW_DIR / "cms_florida_hospital_raw_manifest.json"


def fetch_page(dataset_id: str, offset: int) -> dict:
    """Request one Florida-only page from the CMS Provider Data Catalog API."""
    # Why: Filtering at the official API reduces the downloaded data to the state
    # needed for this project while retaining unmodified fields returned by CMS.
    parameters = {
        "conditions[0][property]": "state",
        "conditions[0][value]": STATE_FILTER,
        "conditions[0][operator]": "=",
        "offset": offset,
        "limit": PAGE_SIZE,
    }
    url = f"{CMS_API_ROOT}/{dataset_id}/0?{urlencode(parameters)}"
    with urlopen(url, timeout=90) as response:
        return json.load(response)


def download_dataset(name: str, dataset_id: str) -> dict:
    """Download all Florida records from one CMS dataset without transformation."""
    # Why: The first response supplies both a source-controlled row count and the
    # exact field names used for the raw CSV header.
    first_page = fetch_page(dataset_id, offset=0)
    expected_count = int(first_page["count"])
    first_rows = first_page.get("results", [])
    if not first_rows:
        raise ValueError(f"CMS returned no Florida rows for {name}.")
    field_names = list(first_rows[0].keys())
    output_file = RAW_DIR / f"cms_{name}_florida_raw.csv"

    # Why: Writing source responses directly to CSV makes the raw extract easy to
    # inspect in Excel while preserving every published field for later cleaning.
    with output_file.open("w", newline="", encoding="utf-8-sig") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=field_names, extrasaction="raise")
        writer.writeheader()
        downloaded_count = 0
        for offset in range(0, expected_count, PAGE_SIZE):
            page = first_page if offset == 0 else fetch_page(dataset_id, offset)
            rows = page.get("results", [])
            writer.writerows(rows)
            downloaded_count += len(rows)
            print(f"{name}: downloaded {downloaded_count:,} of {expected_count:,} rows")

    if downloaded_count != expected_count:
        raise RuntimeError(
            f"Incomplete {name} download: expected {expected_count:,}, got {downloaded_count:,}."
        )
    return {
        "dataset_id": dataset_id,
        "file_name": output_file.name,
        "record_count": downloaded_count,
        "columns": field_names,
        "sha256": sha256(output_file),
    }


def sha256(path: Path) -> str:
    """Create a checksum so the precise raw extract can be verified later."""
    # Why: CMS refreshes its live datasets; the checksum records the exact source
    # version used for this project even after a future public-data refresh.
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """Create both raw extracts and a human-readable provenance manifest."""
    # Why: A fresh project clone should be able to reproduce the directory layout
    # without needing manual folder creation before running the downloader.
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    downloads = {
        name: download_dataset(name, dataset_id)
        for name, dataset_id in DATASETS.items()
    }

    # Why: This manifest records the publisher, API endpoints, source scope, and
    # checksums beside the raw files for portfolio transparency and reproducibility.
    manifest = {
        "publisher": "Centers for Medicare & Medicaid Services (CMS)",
        "scope": "All CMS hospital records where state = Florida",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_catalog_urls": {
            "hospital_general_information": "https://data.cms.gov/provider-data/dataset/xubh-q36u",
            "patient_survey_hcahps": "https://data.cms.gov/provider-data/dataset/dgck-syfz",
        },
        "downloads": downloads,
        "notes": (
            "The EDA stage will identify Miami-Dade and Broward records from the "
            "countyparish field while retaining the full Florida extract as a benchmark."
        ),
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved raw-data manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    # Why: This guard allows the downloader helpers to be tested without triggering
    # an API download merely by importing this file.
    main()
