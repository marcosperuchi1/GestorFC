from __future__ import annotations
import sys
from pathlib import Path

STYLE = """<style id="futbr-hide-how-to-play-final">
[data-action="nav"][data-view="help"],
.v558-help-btn {
  display: none !important;
}
</style>
"""

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: hide_how_to_play_ui.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    path = project / "src" / "index.html"
    html = path.read_text(encoding="utf-8")

    # Nao altera NAV, renderPage, helpPage, saves ou inicializacao.
    # Apenas oculta definitivamente qualquer entrada visual da tela de ajuda.
    if 'id="futbr-hide-how-to-play-final"' not in html:
        pos = html.lower().rfind("</head>")
        if pos < 0:
            raise RuntimeError("Fechamento </head> nao encontrado.")
        html = html[:pos] + STYLE + html[pos:]

    # O motor da versao estavel deve continuar intacto.
    required = [
        "futbr-root-18170-fixes",
        "function renderPage()",
        "function helpPage()",
        "help:helpPage",
        "window.GestorFC"
    ]
    for marker in required:
        if marker not in html:
            raise RuntimeError("Estrutura estavel ausente apos ocultar Como jogar: " + marker)

    path.write_text(html, encoding="utf-8")
    print("Como jogar ocultado somente na interface; motor e carregamento preservados.")

if __name__ == "__main__":
    main()
