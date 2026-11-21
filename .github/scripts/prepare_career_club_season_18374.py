"""Apply the three 18.374 changes to a fully prepared 18.373 source.

The baseline remains outside src so profiling can compare the actual old engine
without shipping a second game or test fixtures in the desktop application.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_career_club_season_18374.py <project>")
    project = Path(sys.argv[1]).resolve()
    source = project / "src/index.html"
    text = source.read_text(encoding="utf-8")
    if "const EDITION='18.373.0';" not in text:
        raise RuntimeError("Expected the fully prepared 18.373 game")
    if "FUTBR_UNEMPLOYED_CALENDAR_18374" in text:
        raise RuntimeError("18.374 was already applied; do not overwrite its baseline")
    baseline_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    approved_baselines = {
        # Each is the final source tested by the corresponding 18.373 workflow.
        "5db6204396465d7d0b364743a048f832b71f40b2ec6d1b11501dc022f098a40a",
        "becd80b14f31c36d47415db8ec1a03ff04d9e0fef9354b2f76d4682c0221c356",
    }
    if baseline_sha not in approved_baselines:
        raise RuntimeError("Unexpected prepared 18.373 source: " + baseline_sha)
    baseline = project / "baseline-18373.html"
    baseline.write_text(text, encoding="utf-8")
    scripts = Path(__file__).resolve().parent
    for name in (
        "fix_season_job_offers_18374.py",
        "expand_club_management_18374.py",
        "optimize_season_rollover_18374.py",
        "finalize_career_club_season_18374.py",
    ):
        subprocess.run([sys.executable, str(scripts / name), str(project)], check=True)
    report = {
        "ok": True,
        "version": "18.374.0",
        "baselineSourceSha256": baseline_sha,
        "sourceSha256": hashlib.sha256(source.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
        "baselineOutsideShippedSource": True,
    }
    (project / "career-club-season-18374-prepare.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
