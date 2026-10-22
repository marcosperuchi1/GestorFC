from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: strip_legacy_save_warning.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    message = "O navegador bloqueou o salvamento automático nesta sessão."
    patterns = [
        re.compile(r"if\s*\(\s*!saveOK\s*\)\s*h\s*\+=\s*'<div class=\"notice mb16\">" + re.escape(message) + r"</div>'\s*;"),
        re.compile(r"if\s*\(\s*!saveOK\s*\)\s*h\s*\+=\s*\`<div class=\"notice mb16\">" + re.escape(message) + r"</div>\`\s*;"),
    ]

    removed = 0
    for pattern in patterns:
        html, count = pattern.subn("", html)
        removed += count

    # A versao protegida por FutBRDesktop e removida pelo estabilizador seguinte.
    guarded = "if(!saveOK&&!window.FutBRDesktop?.available)h+='<div class=\"notice mb16\">" + message + "</div>';"
    if guarded not in html:
        raise RuntimeError("aviso desktop protegido ausente antes da estabilizacao")

    index_path.write_text(html, encoding="utf-8")
    report = {
        "ok": True,
        "legacyClausesRemoved": removed,
        "guardedClausePreservedForFinalRemoval": True,
    }
    (project / "legacy-save-warning-strip.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
