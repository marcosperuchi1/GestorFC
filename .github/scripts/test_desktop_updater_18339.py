from __future__ import annotations
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCH = HERE / "enable_desktop_updater_18339.py"
RELEASE = HERE / "make_desktop_update_release_18339.py"


def check(condition: bool, description: str) -> None:
    if not condition:
        raise AssertionError(description)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="futbr-updater-18339-") as dirname:
        p = Path(dirname)
        for directory in ("src", "src-tauri/src", "src-tauri/target/release/bundle/nsis"):
            (p / directory).mkdir(parents=True, exist_ok=True)
        (p / "src-tauri/tauri.conf.json").write_text(json.dumps({
            "version": "18.338.0", "bundle": {"windows": {"nsis": {"installMode": "currentUser"}}},
            "plugins": {} }), encoding="utf-8")
        (p / "src-tauri/Cargo.toml").write_text("[package]\nname = 'futbr-manager'\n[dependencies]\ntauri = '2'\n", encoding="utf-8")
        (p / "src-tauri/src/lib.rs").write_text(
            "use tauri::AppHandle;\nuse serde::Serialize;\n"
            "#[tauri::command]\nfn desktop_info() {}\n"
            "fn run() { let x=tauri::Builder::default(); }\n"
            "fn handlers() { let _ = ( \n            desktop_info,\n ); }\n",
            encoding="utf-8")
        (p / "src/index.html").write_text(
            "<html><head></head><body>"
            "<script>/* FUTBR_CHAMPIONS_RETIREMENT_18322 */\n"
            "/* FUTBR_LONG_CAREER_SAVE_18338_BEGIN */\n"
            "function ensureSaved(){}\n"
            "window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';\n})();\n</script>"
            "</body></html>", encoding="utf-8")
        no_keys = subprocess.run([sys.executable, str(PATCH), str(p)],
                                 env={k: v for k, v in os.environ.items()
                                      if k not in ("TAURI_SIGNING_PRIVATE_KEY", "FUTBR_UPDATER_PUBLIC_KEY")},
                                 capture_output=True, text=True)
        check(no_keys.returncode != 0, "Updater must fail closed without owner signing keys")
        check("TAURI_SIGNING_PRIVATE_KEY" in no_keys.stderr, "Missing signing key error should be actionable")
        demo_pub = base64.b64encode(("untrusted comment: minisign public key\n" + "RW" + ("A" * 65) + "\n").encode("utf-8")).decode("ascii")
        env = dict(os.environ)
        env.update({"FUTBR_UPDATER_PUBLIC_KEY": demo_pub,
                    "TAURI_SIGNING_PRIVATE_KEY": "fixture-only-never-distribute"})
        result = subprocess.run([sys.executable, str(PATCH), str(p)],
                                env=env, capture_output=True, text=True)
        check(result.returncode == 0, "Updater fixture failed: " + result.stderr)
        config = json.loads((p / "src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
        check(config["version"] == "18.339.0", "Must produce stable SemVer version 18.339.0")
        check(config["bundle"]["createUpdaterArtifacts"] is True, "Tauri must sign bundles")
        check(config["plugins"]["updater"]["pubkey"] == demo_pub, "Key must be embedded unchanged")
        check(config["plugins"]["updater"]["endpoints"] == [
            "https://futbrmanager.com.br/updates/latest.json"], "Trusted feed mismatch")
        check(config["bundle"]["windows"]["nsis"]["installMode"] == "currentUser", "Must preserve per-user install mode")
        check("fixture-only-never-distribute" not in (p / "src-tauri/tauri.conf.json").read_text(), "Private key leaked")
        rust = (p / "src-tauri/src/lib.rs").read_text(encoding="utf-8")
        check("futbr_check_update_18339" in rust and "futbr_install_update_18339" in rust,
              "Native checking/installation commands missing")
        check("download_and_install" in rust and "tauri_plugin_updater::Builder::new().build()" in rust,
              "Tauri signature verification not installed")
        html = (p / "src/index.html").read_text(encoding="utf-8")
        check("await ensureSaved();" in html and "v53Sim?.syncing" in html,
              "Career updates must never bypass active-save or season-sync guard")
        check(html.index("await window.GestorFC.prepareSignedUpdate18339();") <
              html.index("await invoke('futbr_install_update_18339');"),
              "Native installer may only start after a durable save")
        check("setTimeout(check,5000)" in html, "Startup check missing")
        check("data-v18339-later" in html, "User must be able to defer updates")
        js_match = re.search(r'<script id="futbr-desktop-update-ui-18339">([\s\S]+?)</script>', html)
        check(bool(js_match), "Signed updater UI script missing")
        jsfile = p / "updater-ui.js"
        jsfile.write_text(js_match.group(1), encoding="utf-8")
        jscheck = subprocess.run(["node", "--check", str(jsfile)], capture_output=True, text=True)
        check(jscheck.returncode == 0, "Update UI JavaScript invalid: " + jscheck.stderr)
        nsis = p / "src-tauri/target/release/bundle/nsis"
        (nsis / "futbr-manager_18.339.0_x64-setup.exe").write_bytes(b"FAKE_INSTALLER_TEST_ONLY")
        (nsis / "futbr-manager_18.339.0_x64-setup.exe.sig").write_text(
            "TEST_SIGNATURE_BASE64_ONLY_DO_NOT_DISTRIBUTE", encoding="utf-8")
        release = subprocess.run([sys.executable, str(RELEASE), str(p)],
                                 capture_output=True, text=True)
        check(release.returncode == 0, "Release manifest generation failed: " + release.stderr)
        manifest = json.loads((p / "artifacts/latest.json").read_text(encoding="utf-8"))
        check(manifest["version"] == "18.339.0", "Release manifest version mismatch")
        check(manifest["platforms"]["windows-x86_64"]["url"].startswith("https://"),
              "Unsigned HTTP installer forbidden")
        check(manifest["platforms"]["windows-x86_64"]["signature"] ==
              "TEST_SIGNATURE_BASE64_ONLY_DO_NOT_DISTRIBUTE",
              "Manifest must embed complete signature")
    print(json.dumps({
        "ok": True, "version": "18.339",
        "signatureChecks": True, "privateKeyNeverCommitted": True,
        "safeSaveBeforeInstall": True, "javascriptSyntax": True,
        "releaseManifest": True, "missingKeysRejected": True,
    }))


if __name__ == "__main__":
    main()
