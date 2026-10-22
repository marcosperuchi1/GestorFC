from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def die(msg):
    raise RuntimeError(msg)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: test_final_ui_integrity.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src'/'index.html').read_text(encoding='utf-8')

    m=re.search(r'<script id="futbr-final-integrity-18198">\s*([\s\S]*?)\s*</script>',html)
    if not m:
        die('Script final 18.198 ausente')
    final_script=m.group(1)

    forbidden=[
        "try{v582RepairFreshProtectedCareer?.(out);}catch(e){}",
        "const V579_VERSION='5.79',V579_INITIAL_MAIN=35;",
        "const V582_VERSION='5.82',V582_MAX_INITIAL_SENIORS=60;",
        "futbr-ranking-route-18197",
    ]
    for marker in forbidden:
        if marker in html:
            die('Compatibilidade obsoleta ainda ativa: '+marker)

    required=[
        "const V579_VERSION='5.79',V579_INITIAL_MAIN=32;",
        "const V582_VERSION='5.82',V582_MAX_INITIAL_SENIORS=32;",
        "out.v582InitialRosterSource='prebuilt-consolidated'",
        "window.v18198EnforceInitialSquads?.(out)",
        "window.v18198ScorersPage=v18198ScorersPage;",
        "directScorerRenderer:true",
        "initialSeniorCap:32",
        "futbr-terminal-scorers-18199",
        "futbr-terminal-scorers-18202",
        "futbr-terminal-scorers-18203",
        "postSeasonArchiveFallback:true",
        "allNavigationPaths:true",
        "staleContentObserver:true",
        "liveSeason:true",
        "safeNationalityLookup:true",
        "defensiveLiveRows:true",
        "captureNavigation:true",
        "directPagePaint:true",
        "window.v18199PaintScorers=v18199Paint",
        "window.v18202PaintScorers=v18202Paint",
        "window.v18203PaintScorers=v18203Paint",
        ".v677-ranking-tab[data-view=\"rankings\"]",
        "e.stopImmediatePropagation()",
    ]
    for marker in required:
        if marker not in html:
            die('Marcador final ausente: '+marker)

    # A camada 18.203 e a barreira final para estatisticas ao vivo. Ela precisa
    # ficar depois das camadas 18.199 e 18.202 e de todos os patches historicos.
    terminal_pos=html.rfind('futbr-terminal-scorers-18203')
    if terminal_pos < 0:
        die('Camada terminal de Artilheiros 18.203 ausente')
    if terminal_pos <= html.rfind('futbr-terminal-scorers-18202',0,terminal_pos):
        die('Camada 18.203 nao ficou depois da 18.202')
    trailing=html[terminal_pos:]
    if 'futbr-root-18170-fixes' in trailing or 'futbr-v18164-national-match-parity' in trailing:
        die('Existe patch historico depois da camada terminal de Artilheiros')
    terminal_base=html.rfind("const v18203BaseRenderPage=renderPage")
    terminal_render=html.find("renderPage=function",terminal_base)
    if terminal_base < 0 or terminal_render < 0:
        die('Definicao terminal 18.203 de renderPage ausente')
    if html.find("renderPage=function",terminal_render+1) >= 0:
        die('Outra definicao de renderPage ficou depois da camada terminal 18.203')

    js=r"""
const assert=require('assert');
global.window=global;
global.C=[{id:'bra',name:'Brasil'}];
global.NAT={BRA:['Brasil']};
global.scorerFilter={kind:'all',country:'all',division:'all',year:'',query:'',page:0,nationality:'all'};
global.view='clubrankings';
global.renderPage=()=>'<section id="previous">Ranking de Clubes antigo</section>';
global.v677RankingTabs=()=>'<nav>Artilheiros</nav>';
global.coachesPage=()=>'<div>TECNICOS</div>';
global.esc=v=>String(v??'').replace(/[&<>"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
global.starBadge=()=>'';global.nation=code=>'<span>'+String(code||'UNK')+'</span>';
global.badge=t=>'<i>'+String(t?.short||t?.name||'')+'</i>';
global.teamButton=t=>'<button>'+String(t?.name||'')+'</button>';
global.v640Flag=code=>'['+code+']';
global.E={
 normName:v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),
 team:(s,id)=>(s?.teams||[]).find(t=>t.id===id)||null,
 repairLineup:(s,t)=>{t.lineup=(t.lineup||[]).map(id=>t.roster.includes(id)?id:null);}
};
global.state={
 year:2026,day:11,lastDay:10,seasonDone:false,user:'t0',
 players:{p1:{id:'p1',name:'Artilheiro Teste',natCode:'BRA',clubId:'t0',pos:'ATA',age:24}},
 teams:[{id:'t0',name:'Flamengo',short:'FLA',country:'bra',division:1,roster:['p1'],academy:[],proReserve:[],lineup:['p1']}],
 competitions:{},
 competitionStats:{'league:bra:1':{p1:{id:'p1',name:'Artilheiro Teste',natCode:'BRA',goals:7,assists:3,apps:8,minutes:720,clubs:{t0:'Flamengo'}}}},
 allTimeStats:{},scorerArchive:[],v640National:null
};
"""+final_script+r"""
view='rankings';
const rendered=renderPage();
assert(rendered.includes('Buscar atleta'),'Artilheiros nao montou filtros');
assert(rendered.includes('Artilheiro Teste'),'Artilheiros nao montou dados');
assert(rendered.includes('7'),'Artilheiros perdeu gols');
assert(!rendered.includes('Ranking de Clubes antigo'),'Conteudo anterior ficou sobreposto');

const players={};const roster=[];const academy=['p40','p41'];
for(let i=0;i<42;i++){const id='p'+i;players[id]={id,name:'P'+i,age:i>=32?18:25,squad:i>=40?'youth':'senior',clubId:'t0',proReserve:false};if(i<40)roster.push(id);}
const s2={year:2026,players,teams:[{id:'t0',name:'Teste',roster:[...roster],academy:[...academy],proReserve:[],lineup:roster.slice(0,11)}]};
const cap=window.v18198EnforceInitialSquads(s2),t=s2.teams[0];
assert.equal(t.roster.length,32,'Elenco principal nao ficou em 32');
assert.equal(new Set(t.roster).size,32,'IDs repetidos no profissional');
assert.equal(new Set(t.academy).size,t.academy.length,'IDs repetidos na base');
assert.equal(t.roster.filter(id=>t.academy.includes(id)).length,0,'Mesmo ID ficou no elenco e na base');
for(const id of t.roster)assert.equal(players[id].squad,'senior');
for(const id of t.academy)assert.equal(players[id].squad,'youth');
assert(cap.max<=32,'Guard reportou elenco acima de 32');

console.log(JSON.stringify({
 ok:true,
 scorersMounted:true,
 stalePageRemoved:true,
 terminalLayer:true,
 terminalVersion:'18.203',
 captureNavigation:true,
 roster:t.roster.length,
 academy:t.academy.length,
 overlaps:0,
 moved:cap.moved
}));
"""
    tmp=root/'.final-ui-integrity.js'
    tmp.write_text(js,encoding='utf-8')
    try:
        r=subprocess.run(['node',str(tmp)],capture_output=True,text=True,timeout=30)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode:
        die('Teste final de UI/integridade falhou: '+(r.stderr or r.stdout)[-4000:])
    result=json.loads(r.stdout.strip().splitlines()[-1])
    if not result.get('scorersMounted') or not result.get('stalePageRemoved'):
        die('Artilheiros nao substituiu a pagina anterior')
    if result.get('roster')!=32 or result.get('overlaps')!=0:
        die('Teto de elenco/base falhou')
    (root/'final-ui-integrity-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    main()
