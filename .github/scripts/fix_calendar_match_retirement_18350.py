from __future__ import annotations
import json
import sys
from pathlib import Path

MARK = 'FUTBR_CALENDAR_MATCH_RETIRE_18350'
VERSION = '18.350.0'

NEW_MANAGER = r'''/* FUTBR_CALENDAR_MATCH_RETIRE_18350: preserve manager, omit retired-player history UI. */
function v18322RetirementPage(){
 const veterans=v18324EligibleVeterans();
 const content=veterans.length
  ?'<h3>Veteranos do seu clube</h3><div class="v18322-scroller"><table><thead><tr><th>Jogador</th><th>Idade</th><th>OVR</th><th>Decisão</th></tr></thead><tbody>'+
   veterans.sort((a,b)=>v18322N(b.age)-v18322N(a.age)).map(p=>'<tr><td>'+v18322Esc(p.name)+'</td><td>'+p.age+'</td><td>'+E.overall(p)+'</td><td><button class="btn small" data-action="v18322-retire" data-player="'+v18322Esc(p.id)+'">'+
   (p.v579ManualRetire?'Cancelar aposentadoria':'Aposentar ao fim da temporada')+'</button></td></tr>').join('')+'</tbody></table></div>'
  :'<p class="tiny muted">Não há jogadores elegíveis no seu clube. A aposentadoria manual fica disponível a partir dos 35 anos.</p>';
 return '<section class="v18322-panel v18350-retirement-manager"><h2>Gerenciador de aposentadorias</h2>'+
 '<p class="tiny muted">Gerencie as aposentadorias anunciadas pelos jogadores elegíveis. A confirmação ou o cancelamento ocorre dentro do jogo.</p>'+
 content+'</section>';
}'''

CSS = r'''<style id="futbr18350-calendar-match-layout">
/* Equipes lado a lado e sempre encostadas ao placar, sem preencher espacos vazios. */
.v18347-calendar .v18347-match{
 display:grid;grid-template-columns:minmax(0,1fr) max-content minmax(0,1fr);
 align-items:center;gap:7px;width:100%;min-width:0
}
.v18347-calendar .v18347-team{
 display:flex;align-items:center;flex:initial;min-width:0;gap:5px
}
.v18347-calendar .v18350-home{justify-content:flex-end;text-align:right}
.v18347-calendar .v18350-away{justify-content:flex-start;text-align:left}
.v18347-calendar .v18347-score{min-width:14px;text-align:center}
.v18347-calendar .v18347-team strong{min-width:0;overflow-wrap:anywhere}
@media(max-width:540px){
 .v18347-calendar .v18347-match{gap:4px}
 .v18347-calendar .v18347-team{gap:3px}
}
</style>
'''

def once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    if count != 1:
        raise RuntimeError('18.350 ' + label + ': expected one anchor, got ' + str(count))
    return src.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: fix_calendar_match_retirement_18350.py <project>')
    root = Path(sys.argv[1]).resolve()
    cfg = json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    if cfg.get('version') != VERSION:
        raise RuntimeError('Signed Windows version must be 18.350.0 before applying UI changes')
    path = root/'src/index.html'
    src = path.read_text(encoding='utf-8')
    if MARK in src:
        raise RuntimeError('18.350 already applied')
    for marker in ('FUTBR_CALENDAR_LIST_18347', 'FUTBR_CALENDAR_NAV_VERSION_18348',
                   'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349', 'function v18322RetirementPage(){',
                   'data-action="v18324-open-retirements"', 'function v18328OpenRetireModal(id)'):
        if marker not in src:
            raise RuntimeError('Missing preserved game feature: ' + marker)

    # 18.347 accidentally removed the manager's own Elenco entry along with
    # the retired-player history, resetting the open state on every render.
    wrapper_start = ' const previousSquadPage=squadPage;\n squadPage=function(){\n'
    wrapper_end = " document.addEventListener('change',function(event){\n"
    if src.count(wrapper_start) != 1:
        raise RuntimeError('Calendar retirement-hiding wrapper not found exactly once')
    a = src.index(wrapper_start)
    b = src.find(wrapper_end, a)
    if b < 0 or 'v18324RetirementOpen=false' not in src[a:b] or 'v18324-retirement-access' not in src[a:b]:
        raise RuntimeError('Unexpected retirement wrapper: refusing unsafe removal')
    src = src[:a] + ' /* 18.350: original Elenco retirement manager remains accessible. */\n' + src[b:]

    # Keep the same action and modal handlers while removing only the rendered
    # archive table, not s.retirements or player career data.
    page_start = 'function v18322RetirementPage(){'
    page_end = '\n}\n\n'
    if src.count(page_start) != 1:
        raise RuntimeError('Retirement manager renderer not uniquely located')
    a = src.index(page_start)
    b = src.find(page_end, a)
    if b < 0 or 'Histórico de aposentadorias' not in src[a:b]:
        raise RuntimeError('Cannot distinguish historical list from manager')
    src = src[:a] + NEW_MANAGER + src[b+2:]

    old_home = '"<span class=\x27v18347-team\x27>"+badge(h,\x27small\x27)+"<strong>"+safe(h.name)+"</strong></span>",'
    new_home = '"<span class=\x27v18347-team v18350-home\x27><strong>"+safe(h.name)+"</strong>"+badge(h,\x27small\x27)+"</span>",'
    old_away = '"<span class=\x27v18347-team\x27>"+badge(a,\x27small\x27)+"<strong>"+safe(a.name)+"</strong></span>",'
    new_away = '"<span class=\x27v18347-team v18350-away\x27>"+badge(a,\x27small\x27)+"<strong>"+safe(a.name)+"</strong></span>",'
    src = once(src, old_home, new_home, 'home name and crest near score')
    src = once(src, old_away, new_away, 'away crest and name near score')
    src = once(src, "const EDITION='18.349.0';", "const EDITION='18.350.0';", 'visible edition')
    src = once(src,
      "window.GestorFC.version='18.349.0';window.GestorFC.visualVersion='18.349.0';",
      "window.GestorFC.version='18.350.0';window.GestorFC.visualVersion='18.350.0';",
      'runtime edition')
    end = src.rfind('</body>')
    if end < 0:
        raise RuntimeError('Closing game document body missing')
    src = src[:end] + CSS + src[end:]

    for required in ('v18324RetirementOpen=!v18324RetirementOpen',
                     'v18328OpenRetireModal(el.dataset.player)',
                     'v579ToggleRetirement(state,id)',
                     's.retirements=[...newRetirements',
                     'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349'):
        if required not in src:
            raise RuntimeError('Retirement or historical persistence would be lost: ' + required)
    path.write_text(src, encoding='utf-8')
    report = dict(ok=True, version=VERSION, calendarNamesAndCrestsTouchScore=True,
                  responsiveCompactMatch=True, retirementManagerButtonRestored=True,
                  retirementHistoryScreenRemoved=True, manualConfirmationPreserved=True,
                  retirementRecordsAndCareerPreserved=True,
                  fullSeasonScrollPreserved=True, incrementalSavesPreserved=True,
                  versionVisibleAndSignedMatch=True, saveMigrationRequired=False)
    (root/'calendar-retirement-18350-install.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
