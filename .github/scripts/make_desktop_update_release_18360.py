from __future__ import annotations
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

VERSION = "18.360.0"
INSTALLER_NAME = "FutBR-Manager-18.360-Windows.exe"
FEED_URL = "https://futbrmanager.com.br/updates/latest.json"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_desktop_update_release_18360.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    nsis = project / "src-tauri" / "target" / "release" / "bundle" / "nsis"
    installers = sorted([p for p in nsis.glob("*.exe") if p.with_name(p.name + ".sig").is_file()])
    if len(installers) != 1:
        raise RuntimeError("Expected exactly one signed NSIS installer, found " + str(len(installers)))
    source = installers[0]
    sig = Path(str(source) + ".sig").read_text(encoding="utf-8").strip()
    if len(sig) < 32:
        raise RuntimeError("Tauri signature missing or invalid")
    target = project / "artifacts"
    target.mkdir(parents=True, exist_ok=True)
    installer = target / INSTALLER_NAME
    shutil.copy2(source, installer)
    (target / (INSTALLER_NAME + ".sig")).write_text(sig + "\n", encoding="utf-8")
    base = (os.environ.get("FUTBR_UPDATE_ASSET_BASE_URL") or "https://futbrmanager.com.br/updates").strip().rstrip("/")
    if not base.startswith("https://"):
        raise RuntimeError("Updates must be published over HTTPS")
    file_url = base + "/" + INSTALLER_NAME
    manifest = {
        "version": VERSION,
        "notes": "18.360: encerramento das férias com limpeza de checkpoints não bloqueante, sincronização de jogadores por lotes menores e progresso visível, preservando históricos e saves.",
        "platforms": {
            "windows-x86_64": {
                "signature": sig,
                "url": file_url,
            }
        },
    }
    (target / "latest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    (target / "SHA256SUMS.txt").write_text(
        digest + "  " + INSTALLER_NAME + "\n", encoding="ascii")
    report = {
        "ok": True, "version": VERSION, "signed": True,
        "feed": (os.environ.get("FUTBR_UPDATE_FEED_URL") or FEED_URL).strip(), "asset": file_url,
        "signatureEmbeddedInManifest": True, "sha256": digest,
        "publishAfterAllChecks": True,
    }
    (target / "desktop-update-release-18360.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
