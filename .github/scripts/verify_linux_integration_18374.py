"""Allow parallel builds; publish only after the same commit passes Linux CI."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY = "marcosperuchi1/GestorFC"
WORKFLOW = "test-career-club-season-18374.yml"
VERSION = "18.374.0"


def newest_matching_run(payload: dict, commit: str) -> dict | None:
    runs = [r for r in payload.get("workflow_runs", [])
            if r.get("head_sha") == commit
            and r.get("repository", {}).get("full_name") == REPOSITORY
            and r.get("event") in ("push", "workflow_dispatch")]
    return max(runs, key=lambda r: int(r["id"])) if runs else None


def completed_success(run: dict) -> bool:
    if run.get("status") != "completed":
        return False
    if run.get("conclusion") != "success":
        raise RuntimeError("Linux integration did not pass for this commit: "
                           + str(run.get("conclusion")) + " (run " + str(run.get("id")) + ")")
    return True


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_linux_integration_18374.py <project>")
    project = Path(sys.argv[1]).resolve()
    commit = os.environ.get("GITHUB_SHA", "")
    token = os.environ.get("GH_TOKEN", "")
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or not re.fullmatch(r"[0-9a-f]{40}", commit) or not token:
        raise RuntimeError("The exact repository, CI commit and read-only Actions token are required")
    url = f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{WORKFLOW}/runs?head_sha={commit}&per_page=30"
    deadline = time.monotonic() + 1800
    run = None
    while time.monotonic() < deadline:
        request = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "FutBR-18.374-release-gate",
        })
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.load(response)
        run = newest_matching_run(payload, commit)
        if run and completed_success(run):
            break
        print("Waiting for same-commit Linux integration: "
              + (str(run.get("status")) if run else "not yet listed"), flush=True)
        time.sleep(20)
    else:
        raise RuntimeError("Timed out waiting for mandatory same-commit Linux integration; publication remains blocked")

    source = (project / "src/index.html").read_text(encoding="utf-8")
    result = {
        "ok": True, "version": VERSION, "repository": REPOSITORY,
        "workflow": WORKFLOW, "headSha": commit, "linuxHeadSha": run["head_sha"],
        "linuxRunId": run["id"], "linuxRunAttempt": run.get("run_attempt", 1),
        "linuxRunUrl": run["html_url"], "linuxConclusion": run["conclusion"],
        "sameCommitVerified": True,
        "sourceSha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }
    (project / "artifacts/linux-integration-18374-tests.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
