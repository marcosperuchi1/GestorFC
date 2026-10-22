from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_scorers_root.py <project-dir>')
    root = Path(sys.argv[1]).resolve()
    html = (root / 'src' / 'index.html').read_text(encoding='utf-8')
    match = re.search(r'<script id="futbr-scorers-root-18210">\s*([\s\S]*?)\s*</script>', html)
    if not match:
        fail('script raiz 18.210 ausente')
    script = match.group(1)

    required = [
        'singleCanonicalPageFactory:true',
        'noRenderPageOverride:true',
        'noDomOverlay:true',
        'liveAndArchiveStats:true',
        'preservesPerformanceArchitecture:true',
        'data-v18210-scorers-root',
        'rankingsPage=v18210RankingsPage',
        'window.v18198EnforceInitialSquads',
    ]
    for marker in required:
        if marker not in html:
            fail('marcador raiz ausente: ' + marker)
    for marker in [
        'futbr-terminal-scorers-18199',
        'futbr-terminal-scorers-18202',
        'futbr-terminal-scorers-18203',
        'v18202Intent',
        'v18203Intent',
    ]:
        if marker in html:
            fail('camada antiga ainda presente: ' + marker)

    js = r'''
const assert=require('assert');
global.window=global;
global.GestorFC={};
global.view='home';
global.scorerFilter={kind:'all',country:'all',division:'all',year:'',query:'',page:0,nationality:'all'};
global.rankingsPage=()=>'<div>OLD RANKING</div>';
global.scorersPage=()=>'<div>OLD</div>';
global.renderPage=()=>view==='rankings'?rankingsPage():'<div>BASE:'+view+'</div>';
global.v677RankingTabs=()=>'<nav><button data-view="rankings">Artilheiros</button><button data-view="clubrankings">Clubes</button></nav>';
global.esc=v=>String(v??'').replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));
global.nation=code=>'<span>'+String(code||'UNK')+'</span>';
global.badge=t=>'<i>'+String(t?.short||t?.name||'')+'</i>';
global.teamButton=t=>'<button>'+String(t?.name||'')+'</button>';
global.starBadge=()=>'';
global.E={
 normName:v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),
 team:(s,id)=>(s?.teams||[]).find(t=>t.id===id)||null,
 repairLineup:()=>{}
};
global.state={
 year:2026,day:0,lastDay:38,seasonDone:false,user:'t0',
 players:{
  p1:{id:'p1',name:'Atacante Vivo',natCode:'BRA',clubId:'t0',age:25},
  p2:{id:'p2',name:'Segundo Goleador',natCode:'ARG',clubId:'t1',age:27}
 },
 teams:[
  {id:'t0',name:'Clube Teste',short:'CTE',roster:['p1'],academy:[],proReserve:[],lineup:['p1']},
  {id:'t1',name:'Rival Teste',short:'RIV',roster:['p2'],academy:[],proReserve:[],lineup:['p2']}
 ],
 competitions:{},competitionStats:{},allTimeStats:{},scorerArchive:[],v640National:null
};
''' + script + r'''

view='rankings';
let page=renderPage();
assert(page.includes('data-v18210-scorers-root="1"'),'Tela raiz vazia nao foi criada');
assert(page.includes('Nenhum artilheiro'),'Estado vazio nao foi exibido');
assert(!page.includes('OLD'),'Renderer antigo ainda foi usado');

state.competitionStats={
 'league:bra:1':{
  p1:{name:'Atacante Vivo',natCode:'BRA',goals:2,assists:1,apps:2,minutes:180,clubs:{t0:'Clube Teste'}},
  p2:{playerId:'p2',name:'Segundo Goleador',natCode:'ARG',goals:1,assists:0,apps:2,minutes:160,clubs:{t1:'Rival Teste'}}
 }
};
page=renderPage();
assert(page.includes('Atacante Vivo'),'Lider ao vivo ausente');
assert(page.includes('Segundo Goleador'),'Segundo artilheiro ao vivo ausente');
assert(page.includes('green strong">2</td>'),'Gols ao vivo incorretos');

state.competitionStats['league:bra:1'].p1.goals=4;
page=renderPage();
assert(page.includes('green strong">4</td>'),'Rodada seguinte nao atualizou gols');

view='clubrankings';
assert.equal(renderPage(),'<div>BASE:clubrankings</div>','Rota de clubes foi bloqueada');

view='rankings';
state.seasonDone=true;
state.competitionStats={};
state.scorerArchive=[{year:2026,competitions:{'league:bra:1':{p1:{id:'p1',name:'Atacante Vivo',natCode:'BRA',goals:13,assists:5,apps:18,minutes:1500,clubs:{t0:'Clube Teste'}}}}}];
page=renderPage();
assert(page.includes('Atacante Vivo'),'Artilheiro arquivado ausente');
assert(page.includes('green strong">13</td>'),'Gols arquivados incorretos');

const players={},roster=[],academy=[];
for(let i=0;i<40;i++){const id='x'+i;players[id]={id,age:i>=32?18:25,squad:i>=32?'youth':'senior',clubId:'x'};roster.push(id);}
const capState={year:2026,players,teams:[{id:'x',roster,academy,proReserve:[],lineup:roster.slice(0,11)}]};
const cap=window.v18198EnforceInitialSquads(capState);
assert.equal(capState.teams[0].roster.length,32,'Teto de 32 foi perdido');
assert.equal(new Set(capState.teams[0].roster).size,32,'IDs duplicados no elenco');
assert.equal(capState.teams[0].roster.filter(id=>capState.teams[0].academy.includes(id)).length,0,'IDs sobrepostos entre elenco e base');

console.log(JSON.stringify({
 ok:true,
 emptyScreen:true,
 liveRows:true,
 liveUpdate:true,
 archive:true,
 routeExit:true,
 noOverlayLayers:true,
 rosterCap:cap.max,
 goalsLive:4,
 goalsArchive:13
}));
'''
    tmp = root / '.scorers-root-test.js'
    tmp.write_text(js, encoding='utf-8')
    try:
        result = subprocess.run(['node', str(tmp)], capture_output=True, text=True, timeout=30)
    finally:
        tmp.unlink(missing_ok=True)
    if result.returncode:
        fail('teste raiz de Artilheiros falhou:\n' + (result.stderr or result.stdout)[-8000:])
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    (root / 'scorers-root-tests.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == '__main__':
    main()
