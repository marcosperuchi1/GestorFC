from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: finalize_how_to_play.py <project-dir>')
    project = Path(sys.argv[1]).resolve()
    path = project / 'src' / 'index.html'
    html = path.read_text(encoding='utf-8')

    # Remove definitivamente a entrada da tela Como jogar do menu principal.
    nav_item = "['help','help','Como jogar']"
    if nav_item not in html:
        fail('Entrada Como jogar nao encontrada no NAV principal.')
    html = html.replace(',' + nav_item, '').replace(nav_item + ',', '').replace(nav_item, '')

    # Retira a rota da tela. Qualquer view=help passa a cair no dashboard
    # pelo fallback natural de renderPage.
    route = 'help:helpPage,'
    if route not in html:
        fail('Rota help:helpPage nao encontrada.')
    html = html.replace(route, '')

    # Evita referencias visiveis para uma tela que nao existe mais.
    html = html.replace('Regras completas em Como jogar → Disciplina.', 'Cartões, suspensões e pendências são exibidos nesta tela.')
    html = html.replace('Regras completas em Como jogar -> Disciplina.', 'Cartões, suspensões e pendências são exibidos nesta tela.')

    # Validacao: menu e rota antigos nao podem permanecer.
    if nav_item in html:
        fail('Entrada Como jogar ainda presente no NAV.')
    if 'help:helpPage,' in html:
        fail('Rota Como jogar ainda presente em renderPage.')
    path.write_text(html, encoding='utf-8')
    print('Tela Como jogar removida definitivamente do menu e da navegacao.')

if __name__ == '__main__':
    main()
