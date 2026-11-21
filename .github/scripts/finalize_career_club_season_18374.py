"""Check the integrated release and identify the exact source being tested."""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

VERSION = "18.374.0"
MARKERS = (
    "FUTBR_UNEMPLOYED_CALENDAR_18374",
    "FUTBR_CLUB_MANAGEMENT_18374",
    "FUTBR_CLUB_MANAGEMENT_UI_18374",
    "FUTBR_SEASON_RANK_BATCH_18374",
    "FUTBR_PLAYER_FAST_SHAPES_18373",
    "FUTBR_PLAYER_CHECKPOINT_REUSE_18373",
    "FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN",
    "FUTBR_JOBWAIT_SINGLE_OWNER_18373",
    "FUTBR_VACATION_BOUNDED_BOOT_18373",
    "FUTBR_VACATION_DURABLE_CHECKPOINT_18373",
    "FUTBR_CAREER_PROMOTION_OFFERS_18372",
    "FUTBR_NATIVE_CONFIRMATIONS_18372_BEGIN",
)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: finalize_career_club_season_18374.py <project>")
    root = Path(sys.argv[1]).resolve()
    path = root / "src/index.html"
    source = path.read_text(encoding="utf-8")
    for marker in MARKERS:
        if marker not in source:
            raise RuntimeError("Missing integrated correction: " + marker)
    for old, new in (
        ("const EDITION='18.373.0';", "const EDITION='18.374.0';"),
        ("window.GestorFC.version='18.373.0';window.GestorFC.visualVersion='18.373.0';",
         "window.GestorFC.version='18.374.0';window.GestorFC.visualVersion='18.374.0';"),
    ):
        if source.count(old) != 1:
            raise RuntimeError("Expected the approved 18.373 edition before finalization")
        source = source.replace(old, new, 1)
    if re.search(r"TEST_ONLY_[A-Z0-9_]*1837[234]", source):
        raise RuntimeError("A test fixture must never be shipped")
    engine_start = source.index("const Engine = (() => {")
    ui_start = source.index("let state=null,saved=null")
    ui_end = source.index("</script>", ui_start)
    for marker in ("FUTBR_UNEMPLOYED_CALENDAR_18374", "FUTBR_CLUB_MANAGEMENT_18374", "FUTBR_SEASON_RANK_BATCH_18374"):
        if not engine_start < source.index(marker) < ui_start:
            raise RuntimeError("Engine correction is outside the actual Engine: " + marker)
    if not ui_start < source.index("FUTBR_CLUB_MANAGEMENT_UI_18374") < ui_end:
        raise RuntimeError("Club management UI is outside the active game closure")
    scripts = [body for attrs, body in re.findall(r"<script\b([^>]*)>([\s\S]*?)</script>", source, flags=re.I)
               if body.strip() and not re.search(r"type\s*=\s*['\"](?:application/(?:json|ld\+json|octet-stream)|importmap)", attrs, re.I)]
    check = subprocess.run(
        ["node", "-e", "const vm=require('vm'),fs=require('fs'),s=JSON.parse(fs.readFileSync(0,'utf8'));"
         "s.forEach((code,i)=>new vm.Script(code,{filename:'inline-'+i+'.js'}));"
         "process.stdout.write(JSON.stringify({parsedScripts:s.length}));"],
        input=json.dumps(scripts), text=True, capture_output=True, timeout=90,
    )
    if check.returncode:
        raise RuntimeError("Integrated JavaScript syntax check failed:\n" + check.stderr)
    path.write_text(source, encoding="utf-8")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    report = {
        "ok": True, "version": VERSION, "sourceSha256": digest,
        "allCorrectionsIntegrated": True, "actualEngineAndUiScopesVerified": True,
        "priorMemoryCareerAndDialogCorrectionsPreserved": True,
        "testHooksNotShipped": True, "editionUpdated": True,
        **json.loads(check.stdout),
    }
    (root / "career-club-season-18374-install.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts = root / "artifacts"
    artifacts.mkdir(exist_ok=True)
    (artifacts / "prepared-source-18374.html.gz").write_bytes(gzip.compress(source.encode("utf-8"), mtime=0))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
