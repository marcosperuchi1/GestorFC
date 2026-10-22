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
    guarded = "if(!saveOK&&!window.FutBRDesktop?.available)h+='<div class=\"notice mb16\">" + message + "</div>';"
    if guarded not in html:
        raise RuntimeError("aviso desktop protegido ausente antes da estabilizacao")

    # Preserva temporariamente a unica clausula final que sera removida pelo
    # estabilizador seguinte. Todas as copias historicas/literais deixam de fazer
    # parte do executavel e nao podem reaparecer por outro renderer antigo.
    sentinel = "/* FUTBR_FINAL_SAVE_WARNING_GUARD */"
    html = html.replace(guarded, sentinel, 1)

    patterns = [
        re.compile(r"if\s*\(\s*!saveOK\s*\)\s*h\s*\+=\s*'<div class=\"notice mb16\">" + re.escape(message) + r"</div>'\s*;"),
        re.compile(r"if\s*\(\s*!saveOK\s*\)\s*h\s*\+=\s*\`<div class=\"notice mb16\">" + re.escape(message) + r"</div>\`\s*;"),
    ]

    removed_clauses = 0
    for pattern in patterns:
        html, count = pattern.subn("", html)
        removed_clauses += count

    literal_copies = html.count(message)
    html = html.replace(message, "")
    html = html.replace(sentinel, guarded, 1)

    if html.count(guarded) != 1:
        raise RuntimeError("a clausula final do aviso nao foi preservada de forma unica")
    if html.count(message) != 1:
        raise RuntimeError("referencias historicas do aviso ainda permanecem")

    index_path.write_text(html, encoding="utf-8")
    report = {
        "ok": True,
        "legacyClausesRemoved": removed_clauses,
        "literalCopiesRemoved": literal_copies,
        "guardedClausePreservedForFinalRemoval": True,
    }
    (project / "legacy-save-warning-strip.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
