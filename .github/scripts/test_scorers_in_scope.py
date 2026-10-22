from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def extract_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        fail(f"bloco ausente: {start_marker} ... {end_marker}")
    return text[start : end + len(end_marker)]


def extract_function(text: str, name: str) -> str:
    matches = list(re.finditer(r"function\s+" + re.escape(name) + r"\s*\(", text))
    if not matches:
        fail("funcao ausente: " + name)
    match = matches[-1]
    brace = text.find("{", match.end())
    if brace < 0:
        fail("abertura ausente: " + name)
    depth = 0
    quote: str | None = None
    escaped = False
    template_depth = 0
    for index in range(brace, len(text)):
        ch = text[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif quote == "`" and ch == "$" and index + 1 < len(text) and text[index + 1] == "{":
                template_depth += 1
            elif quote == "`" and ch == "}" and template_depth:
                template_depth -= 1
            elif ch == quote and template_depth == 0:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    fail("funcao nao fechada: " + name)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_scorers_in_scope.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    html = (project / "src" / "index.html").read_text(encoding="utf-8")

    required = [
        "FUTBR_SCORERS_IN_SCOPE_18220_START",
        "sameEngineScope:true",
        "data-v18220-rankings-page",
        "data-v18220-scorers-root",
        "FUTBR_RANKING_CACHE_18221_START",
        "boundedSingleSnapshot:true",
        "idlePrewarm:true",
        "window.v18198EnforceInitialSquads=v18198EnforceInitialSquads",
        "else if(view==='clubrankings')v18220PageHTML=v18221ClubRankPage()",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador in-scope ausente: " + marker)

    forbidden_ids = [
        "futbr-final-integrity-18198",
        "futbr-terminal-scorers-18199",
        "futbr-terminal-scorers-18202",
        "futbr-terminal-scorers-18203",
        "futbr-scorers-root-18210",
        "futbr-scorers-render-root-18211",
    ]
    for script_id in forbidden_ids:
        if f'id="{script_id}"' in html or f"id='{script_id}'" in html:
            fail("camada externa antiga ainda executavel: " + script_id)

    marker_pos = html.find("FUTBR_SCORERS_IN_SCOPE_18220_START")
    script_open = html.rfind("<script", 0, marker_pos)
    script_close = html.find("</script>", marker_pos)
    render_pos = html.find("function renderPage()")
    if min(marker_pos, script_open, script_close, render_pos) < 0:
        fail("script principal ou renderPage ausente")
    if not script_open < marker_pos < script_close or not script_open < render_pos < script_close:
        fail("Artilheiros e renderPage nao compartilham o mesmo script principal")

    scorer_block = extract_between(
        html,
        "/* FUTBR_SCORERS_IN_SCOPE_18220_START */",
        "/* FUTBR_SCORERS_IN_SCOPE_18220_END */",
    )
    cache_block = extract_between(
        html,
        "/* FUTBR_RANKING_CACHE_18221_START */",
        "/* FUTBR_RANKING_CACHE_18221_END */",
    )
    cap_function = extract_function(html, "v18198EnforceInitialSquads")

    js = r'''
const assert=require('assert');
global.window=global;
global.GestorFC={};
global.document={addEventListener(){},querySelector(){return null;}};
let view='rankings';
let state=null;
let scorerFilter={kind:'all',country:'all',division:'all',year:'',query:'',nationality:'all',page:0};
let v53Creating=false;
let v53Sim={active:false,starting:false};
const C=[{id:'bra',name:'Brasil'},{id:'arg',name:'Argentina'}];
const NAT={BRA:['Brasil'],ARG:['Argentina']};
const WorldCatalog={countries:C};
const E={
 normName:value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),
 team:(s,id)=>(s?.teams||[]).find(team=>team.id===id)||null,
 repairLineup(){}
};
function esc(value){return String(value??'').replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));}
function icon(name){return '<i>'+esc(name)+'</i>';}
function nation(code){return '<span class="nation">'+esc(code)+'</span>';}
function badge(team){return '<i>'+esc(team?.short||team?.name||'')+'</i>';}
function teamButton(team){return '<button>'+esc(team?.name||'')+'</button>';}
function v640Flag(code){return '['+esc(code)+']';}
function v320Players(s){return Object.values(s?.players||{});}
function v677RankingTabs(){
 const items=[['clubrankings','trophy','Clubes'],['nationalrankings','flag','Selecoes'],['rankings','trophy','Artilheiros'],['coaches','users','Tecnicos']];
 return '<div class="v677-ranking-tabs">'+items.map(([route,ic,label])=>'<button data-view="'+route+'">'+icon(ic)+label+'</button>').join('')+'</div>';
}
let renderCalls=0;
function renderPage(){renderCalls++;return '<section class="club-rank">'+('R'.repeat(140))+renderCalls+'</section>';}
''' + scorer_block + '\n' + cap_function + r'''
window.v18198EnforceInitialSquads=v18198EnforceInitialSquads;
''' + cache_block + r'''

const filter={kind:'all',country:'all',division:'all',year:'',query:'',nationality:'all',page:0};
const liveState={
 year:2026,day:11,seasonDone:false,user:'t0',
 players:{
  p1:{id:'p1',name:'Artilheiro Real',natCode:'BRA',clubId:'t0',goals:5,assists:2,apps:8,minutes:700},
  p2:{id:'p2',name:'Segundo Goleador',natCode:'ARG',clubId:'t1',goals:3,assists:1,apps:8,minutes:650}
 },
 teams:[
  {id:'t0',name:'Flamengo Teste',short:'FLA',country:'bra',roster:['p1'],academy:[],proReserve:[],lineup:['p1']},
  {id:'t1',name:'Rival Teste',short:'RIV',country:'arg',roster:['p2'],academy:[],proReserve:[],lineup:['p2']}
 ],
 competitions:{},allTimeStats:{},scorerArchive:[],v640National:null,
 competitionStats:{
  'league:bra:1':{
   p1:{name:'Artilheiro Real',natCode:'BRA',goals:5,assists:2,apps:8,minutes:700,clubs:{t0:'Flamengo Teste'}},
   p2:{playerId:'p2',name:'Segundo Goleador',natCode:'ARG',goals:3,assists:1,apps:8,minutes:650,clubs:{t1:'Rival Teste'}}
  }
 }
};
const scorerApi=window.GestorFC.scorersInScope18220;
const clubApi=window.GestorFC.clubRankingCache18221;
assert(scorerApi&&typeof scorerApi.renderWith==='function','API 18.220 ausente');
assert(clubApi&&typeof clubApi.probe==='function','API 18.221 ausente');

const live=scorerApi.renderWith(liveState,{...filter});
assert(live.includes('v677-ranking-tabs'),'cabecalho de abas ausente');
assert(live.includes('Artilheiros')&&live.includes('Clubes'),'abas de ranking incompletas');
assert(live.includes('Ranking de Artilheiros'),'titulo de artilheiros ausente');
assert(live.includes('Artilheiro Real')&&live.includes('Segundo Goleador'),'jogadores ao vivo ausentes');
assert(live.includes('green strong">5</td>'),'gols ao vivo incorretos');
assert(!live.includes('Nenhum artilheiro registrado'),'estado ao vivo foi tratado como vazio');

liveState.day=12;
liveState.competitionStats['league:bra:1'].p1.goals=6;
const updated=scorerApi.renderWith(liveState,{...filter});
assert(updated.includes('green strong">6</td>'),'nova jornada nao atualizou a artilharia');

const archived={...liveState,day:156,seasonDone:true,competitionStats:{},scorerArchive:[{year:2026,competitions:{'league:bra:1':{p1:{id:'p1',name:'Artilheiro Real',natCode:'BRA',goals:18,assists:7,apps:30,minutes:2500,clubs:{t0:'Flamengo Teste'}}}}}]};
const archive=scorerApi.renderWith(archived,{...filter});
assert(archive.includes('green strong">18</td>'),'historico encerrado nao foi carregado');

let cacheCalls=0;
const htmlA='<div>'+('A'.repeat(150))+'</div>';
const htmlB='<div>'+('B'.repeat(150))+'</div>';
const htmlC='<div>'+('C'.repeat(150))+'</div>';
const first=clubApi.probe('journey-11',()=>{cacheCalls++;return htmlA;});
const second=clubApi.probe('journey-11',()=>{cacheCalls++;return htmlB;});
const third=clubApi.probe('journey-12',()=>{cacheCalls++;return htmlC;});
assert.equal(cacheCalls,2,'cache de clubes recalculou a mesma jornada');
assert.equal(first,second,'snapshot da mesma jornada nao foi reutilizado');
assert.notEqual(third,second,'mudanca de jornada nao invalidou o snapshot');

const capPlayers={},capRoster=[];
for(let i=0;i<40;i++){const id='x'+i;capPlayers[id]={id,age:i>=32?18:25,squad:i>=32?'youth':'senior',clubId:'x'};capRoster.push(id);}
const capState={year:2026,players:capPlayers,teams:[{id:'x',roster:capRoster,academy:[],proReserve:[],lineup:capRoster.slice(0,11)}]};
const cap=window.v18198EnforceInitialSquads(capState);
assert.equal(capState.teams[0].roster.length,32,'teto de 32 foi perdido');
assert.equal(cap.max,32,'maximo reportado diferente de 32');
assert.equal(capState.teams[0].roster.filter(id=>capState.teams[0].academy.includes(id)).length,0,'sobreposicao elenco/base');

console.log(JSON.stringify({
 ok:true,
 sameMainScriptScope:true,
 tabsAndHeader:true,
 livePlayers:true,
 goalsLive:5,
 goalsNextRound:6,
 goalsArchive:18,
 clubRankingCacheCalls:cacheCalls,
 clubRankingSameJourneyHit:true,
 clubRankingNewJourneyInvalidated:true,
 clubRankingBoundedSingleSnapshot:clubApi.boundedSingleSnapshot===true,
 roster:capState.teams[0].roster.length,
 academy:capState.teams[0].academy.length,
 capMax:cap.max
}));
'''

    temp = project / ".scorers-in-scope-test.js"
    temp.write_text(js, encoding="utf-8")
    try:
        result = subprocess.run(["node", str(temp)], capture_output=True, text=True, timeout=45)
    finally:
        temp.unlink(missing_ok=True)
    if result.returncode:
        fail("teste in-scope falhou:\n" + (result.stderr or result.stdout)[-10000:])

    payload = json.loads(result.stdout.strip().splitlines()[-1])
    payload["structuralMainScriptScope"] = True
    payload["externalOverlayLayers"] = 0
    output = project / "scorers-in-scope-tests.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
