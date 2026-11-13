from pathlib import Path
import json
import sys

VERSION='18.321'
MARK='FUTBR_RANK_UI_18321'

def once(html, old, new, name):
    n=html.count(old)
    if n!=1:
        raise RuntimeError(f'{name}: esperado 1 ponto de alteracao; encontrados {n}')
    return html.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: fix_rankings_ui_18321.py <project-dir>')
    root=Path(sys.argv[1]);target=root/'src'/'index.html'
    html=target.read_text(encoding='utf-8')
    if MARK in html:
        print('18.321 already applied')
        return
    if 'FUTBR_RANK_CORE_18320_START' not in html:
        raise RuntimeError('Motor limpo 18.320 ausente')
    # A tela de clubes nao usa renderPage(), portanto pulava o wrapper
    # que inclui as abas de Clubes, Selecoes, Artilheiros e Tecnicos.
    html=once(
        html,
        "else if(view==='clubrankings')v18220PageHTML=v86ClubRankingPage();",
        "else if(view==='clubrankings')v18220PageHTML='<div class=\"v677-ranking-hub\" data-v18321-club-rank=\"1\">'+v677RankingTabs()+'<div class=\"v677-ranking-content\">'+v86ClubRankingPage()+'</div></div>';",
        'Insercao das quatro abas no caminho real do renderizador'
    )
    # O motor dinamico 8.6/18.312 so era necessario para a tela antiga.
    # Apos a 18.320 o novo snapshot e imediato e independente.
    # Desliga o gatilho de rebuild em todo render da carreira.
    html=once(
        html,
        'v81BootstrapRank=v127ScheduleRankWarm;',
        'v81BootstrapRank=function(){return false;}; /* FUTBR_RANK_UI_18321: old warm-up disabled */',
        'Desabilitar warm-up automatico antigo'
    )
    # A virada de temporada nao pode religar o motor antigo.
    # A funcao atual usa o novo snapshot e devolve {ready:true}.
    html=once(
        html,
        'c=window.GestorFC?.v18312?.ensure?.()||v86EnsureBuild(false);',
        'c=v18320EnsureRanking(state);',
        'Preparacao da nova temporada via snapshot novo'
    )
    # Defesa adicional: mesmo que uma tarefa antiga seja iniciada por outro
    # recurso, ela nao pode sobrescrever o titulo de status do ranking novo.
    html=once(
        html,
        'id="v86-rank-progress" class="tiny muted"',
        'id="v18321-rank-ready" class="tiny muted"',
        'Isolamento do indicador de progresso visual'
    )
    html=once(html,'Motor limpo 18.320 ·','Motor limpo 18.321 ·','Identificacao do novo instalador')
    checks={
      'navigation':'data-v18321-club-rank="1"',
      'newSeason':'c=v18320EnsureRanking(state);',
      'oldTimerDisabled':'v81BootstrapRank=function(){return false;};',
      'freshStatus':'Motor limpo 18.321 ·',
      'progressIsolated':'id="v18321-rank-ready"'
    }
    for name,needle in checks.items():
        if needle not in html:raise RuntimeError('Falha de verificacao: '+name)
    target.write_text(html,encoding='utf-8')
    report={'version':VERSION,'ok':True,'fourTabsRestored':True,
      'legacyWarmupDisabled':True,'newSeasonUsesCurrentRank':True,
      'oldProgressCannotOverwriteNewStatus':True,
      'rankingCoreUnchanged':True,'marker':MARK}
    (root/'ranking-ui-18321-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
