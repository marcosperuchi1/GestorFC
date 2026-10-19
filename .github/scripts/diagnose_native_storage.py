from __future__ import annotations
import sys
from pathlib import Path

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: diagnose_native_storage.py <project-dir>")
    root=Path(sys.argv[1]).resolve()
    cargo=root/"src-tauri"/"Cargo.toml"
    lib=root/"src-tauri"/"src"/"lib.rs"
    print("===== Cargo.toml =====")
    print(cargo.read_text(encoding="utf-8"))
    print("\n===== lib.rs =====")
    print(lib.read_text(encoding="utf-8"))

if __name__=="__main__":
    main()
