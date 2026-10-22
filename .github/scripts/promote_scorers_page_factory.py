from __future__ import annotations
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: esperado 1, encontrado {count}')
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: promote_scorers_page_factory.py <project-dir>')
    path = Path(sys.argv[1]).resolve() / 'src' / 'index.html'
    html = path.read_text(encoding='utf-8')

    html = replace_once(
        html,
        ' const v18210BaseRenderPage=renderPage;\n\n',
        '',
        'remover wrapper de renderPage',
    )
    html = replace_once(
        html,
        " function v18210RankingsPage(){\n  const tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';\n  return '<div class=\"v677-ranking-hub\">'+tabs+'<div class=\"v677-ranking-content\"><div class=\"v615-rankings-shell\">'+v18210ScorersContent()+'</div></div></div>';\n }",
        " function v18210RankingsPage(){\n  return '<div class=\"v615-rankings-shell\">'+v18210ScorersContent()+'</div>';\n }",
        'page factory de rankings',
    )
    html = replace_once(
        html,
        " window.v18210RankingsPage=v18210RankingsPage;\n try{scorersPage=v18210ScorersContent;}catch(e){window.scorersPage=v18210ScorersContent;}\n renderPage=function(){if(view==='rankings')return v18210RankingsPage();return v18210BaseRenderPage();};\n G.scorersRoot18210={version:'18.210',singleCanonicalRoute:true,noDomOverlay:true,liveAndArchiveStats:true,preservesPerformanceArchitecture:true};",
        " window.v18210RankingsPage=v18210RankingsPage;\n try{scorersPage=v18210ScorersContent;}catch(e){window.scorersPage=v18210ScorersContent;}\n try{rankingsPage=v18210RankingsPage;}catch(e){window.rankingsPage=v18210RankingsPage;}\n G.scorersRoot18210={version:'18.210',singleCanonicalPageFactory:true,noRenderPageOverride:true,noDomOverlay:true,liveAndArchiveStats:true,preservesPerformanceArchitecture:true};",
        'ligar page factory final',
    )

    if "renderPage=function(){if(view==='rankings')" in html:
        raise RuntimeError('override de renderPage da correcao ainda presente')
    for marker in [
        'singleCanonicalPageFactory:true',
        'noRenderPageOverride:true',
        'rankingsPage=v18210RankingsPage',
    ]:
        if marker not in html:
            raise RuntimeError('marcador do page factory ausente: ' + marker)

    path.write_text(html, encoding='utf-8')
    print('Artilheiros ligado diretamente a rankingsPage; renderPage original preservado')


if __name__ == '__main__':
    main()
