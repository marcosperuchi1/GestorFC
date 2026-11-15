#!/usr/bin/env python3
"""FutBR Manager Android alpha: adapt an extracted Windows-patched web build.

Only modifies a temporary Android build directory, never the Windows source.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

MARKER = "futbr-android-alpha-bootstrap-v1"


def prepare(project: Path):
    project = project.resolve()
    index = project / "src" / "index.html"
    html = index.read_text(encoding="utf-8")
    if MARKER in html: raise RuntimeError("Android patch applied twice")
    asset = project / "src" / "assets" / "data" / "rosters.v310.bin"
    if not asset.exists() or asset.stat().st_size < 2_000_000:
        raise RuntimeError("Missing precompiled roster base; abort before APK")

    # Android uses its own WebView; no Windows SQLite or desktop commands.
    html, bridges = re.subn(
        r'<script\b[^>]*\bid=["\']futbr-desktop-native-bridge["\'][^>]*>.*?</script>',
        "", html, flags=re.S | re.I
    )
    if bridges != 1:
        raise RuntimeError(f"Expected one Windows bridge; found {bridges}")

    preload = """<script id="futbr-android-alpha-bootstrap-v1">
(function(){
 document.documentElement.classList.add('futbr-android-alpha');
 window.__FUTBR_ROSTER_PRELOAD__ = fetch('./assets/data/rosters.v310.bin')
  .then(function(r){ if(!r.ok)throw Error('Base offline indisponivel: '+r.status);return r.text(); });
 window.__FUTBR_ROSTER_PRELOAD__.catch(function(err){console.error('[FutBR Android] base offline',err);});
})();
</script>
"""
    if html.count("</head>") != 1:
        raise RuntimeError("Invalid HTML head")
    html = html.replace("</head>", preload + "\n</head>", 1)
    if "connect-src 'self'" not in html:
        html = re.sub(r'(connect-src )', r"\1'self' ", html, count=1)
    if "img-src 'self'" not in html:
        html = re.sub(r'(img-src )', r"\1'self' ", html, count=1)
    html = re.sub(
        r'(<meta\s+name="viewport"\s+content=")[^"]+(">)',
        r'\1width=device-width,initial-scale=1,viewport-fit=cover\2',
        html, count=1
    )

    style = """<style id="futbr-android-alpha-css">
html.futbr-android-alpha,html.futbr-android-alpha body {
  min-height:100dvh; overscroll-behavior:contain;
  -webkit-tap-highlight-color:transparent;
}
html.futbr-android-alpha button,html.futbr-android-alpha select,
html.futbr-android-alpha input,html.futbr-android-alpha [data-action] {
  touch-action:manipulation;
}
html.futbr-android-alpha .table-scroll,
html.futbr-android-alpha [class*="scroll"] {
  -webkit-overflow-scrolling:touch;
}
@media (max-width:1050px) and (orientation:landscape) {
 html.futbr-android-alpha .main{min-width:0!important;overflow:auto!important;padding:8px 12px!important}
 html.futbr-android-alpha .main-wrap{min-height:100dvh!important;max-width:100vw!important}
 html.futbr-android-alpha .sidebar{max-width:190px!important}
 html.futbr-android-alpha .topbar{padding:4px 8px!important}
 html.futbr-android-alpha .btn{min-height:35px}
 html.futbr-android-alpha .modal{max-height:calc(100dvh - 16px)!important}
 html.futbr-android-alpha .overlay{align-items:center!important}
}
</style>
"""
    if html.count("</body>") != 1:
        raise RuntimeError("Invalid HTML body")
    html = html.replace("</body>", style + "\n</body>", 1)
    index.write_text(html, encoding="utf-8")

    config_file = project / "src-tauri" / "tauri.conf.json"
    config = json.loads(config_file.read_text(encoding="utf-8-sig"))
    config["productName"] = "FutBR Manager Android Alpha"
    config["identifier"] = "com.futbrmanager.android"
    config["version"] = "1.0.0"
    config.setdefault("build", {})["frontendDist"] = "../src"
    config.setdefault("app", {})["withGlobalTauri"] = False
    config["app"]["windows"] = [
        {"label":"main","title":"FutBR Manager","fullscreen":True,
         "decorations":False,"width":1200,"height":720,"resizable":True}
    ]
    bundle = config.setdefault("bundle", {})
    for key in ("windows", "resources", "targets"):
        bundle.pop(key, None)
    bundle["android"] = {"minSdkVersion":26,"versionCode":1}
    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    (project / "src-tauri" / "Cargo.toml").write_text("""[package]
name = "futbr-manager"
version = "1.0.0"
description = "FutBR Manager Android Alpha"
authors = ["FutBR Manager"]
edition = "2021"
rust-version = "1.77.2"

[lib]
name = "futbr_manager_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[[bin]]
name = "futbr-manager"
path = "src/main.rs"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = [] }
""", encoding="utf-8")
    (project / "src-tauri" / "src" / "lib.rs").write_text("""#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("FutBR Manager Android initialization failed");
}
""", encoding="utf-8")

    report = {"flavor":"android-alpha","desktopBridgeRemoved":bridges,
              "rosterAssetBytes":asset.stat().st_size,
              "indexHtmlBytes":index.stat().st_size,
              "identifier":config["identifier"],"version":config["version"],
              "desktopBuildModified":False,
              "gameplayPort":"latest web payload from 18.331 pipeline"}
    (project/"android-alpha-report.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print("ANDROID_PREPARED", json.dumps(report,ensure_ascii=False),flush=True)


def manifest(project: Path):
    p = (project/"src-tauri"/"gen"/"android"/"app"/"src"/"main"/"AndroidManifest.xml")
    if not p.exists(): raise RuntimeError("Tauri Android init did not generate AndroidManifest")
    html = p.read_text(encoding="utf-8")
    if 'android:screenOrientation=' not in html:
        html, n = re.subn(r'(<activity\b)', r'\1 android:screenOrientation="sensorLandscape"',html,count=1)
        if n != 1: raise RuntimeError("Cannot set landscape orientation")
    if 'android.permission.INTERNET' not in html:
        html=html.replace("<application",'<uses-permission android:name="android.permission.INTERNET" />\n    <application',1)
    p.write_text(html,encoding="utf-8")
    print("ANDROID_MANIFEST_READY",flush=True)


if __name__ == "__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: prepare_android_alpha.py prepare|manifest <project>")
    if sys.argv[1]=="prepare": prepare(Path(sys.argv[2]))
    elif sys.argv[1]=="manifest": manifest(Path(sys.argv[2]))
    else: raise SystemExit("Unknown command")
