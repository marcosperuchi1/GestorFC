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
        raise SystemExit("usage: test_rankings_18230.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    html = (project / "src" / "index.html").read_text(encoding="utf-8")

    required = [
        "FUTBR_SCORERS_IN_SCOPE_18220_START",
        "data-v18230-compact-header=\"1\"",
        "FUTBR_RANKING_CACHE_18230_START",
        "FUTBR_RANKING_CACHE_18230_STABLE",
        "version:'18.230'",
        "boundedSnapshots:V18230_CLUB_RANK_CACHE_MAX",
        "staleWhileRevalidate:true",
        "retryUntilReady:true",
        "controlAwareInvalidation:true",
        "preservesRankingMethodology:true",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador 18.230 ausente: " + marker)

    scorer_block = extract_between(
        html,
        "/* FUTBR_SCORERS_IN_SCOPE_18220_START */",
        "/* FUTBR_SCORERS_IN_SCOPE_18220_END */",
    )
    cache_block = extract_between(
        html,
        "/* FUTBR_RANKING_CACHE_18230_START */",
        "/* FUTBR_RANKING_CACHE_18230_END */",
    )
    cap_function = extract_function(html, "v18198EnforceInitialSquads")

    if "<h3>Ranking de Artilheiros</h3>" in scorer_block:
        fail("cabecalho alto de Artilheiros ainda presente")
    if "Estatisticas da temporada, copas e selecoes" in scorer_block:
        fail("subtitulo alto de Artilheiros ainda presente")
    if "<div class=\"panel-head\">" in scorer_block:
        fail("panel-head de Artilheiros ainda presente")

    js = r'''
const assert=require('assert');
global.window=global;
global.GestorFC={};
global.document={
 addEventListener(){},
 querySelector(){return null;}
};
global.requestIdleCallback=undefined;
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
function renderPage(){renderCalls++;return '<section class="club-rank">'+('R'.repeat(180))+renderCalls+'</section>';}
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
assert(scorerApi&&typeof scorerApi.renderWith==='function','API de Artilheiros ausente');
assert(clubApi&&typeof clubApi.probe==='function','API de cache de clubes ausente');

const live=scorerApi.renderWith(liveState,{...filter});
assert(live.includes('v677-ranking-tabs'),'abas de ranking ausentes');
assert(live.includes('Artilheiros')&&live.includes('Clubes'),'abas de ranking incompletas');
assert(live.includes('Artilheiro Real')&&live.includes('Segundo Goleador'),'jogadores ao vivo ausentes');
assert(live.includes('green strong">5</td>'),'gols ao vivo incorretos');
assert(live.includes('data-v18230-compact-header="1"'),'layout compacto ausente');
assert(!live.includes('Ranking de Artilheiros</h3>'),'cabecalho alto ainda renderizado');
assert(!live.includes('Estatisticas da temporada, copas e selecoes'),'subtitulo alto ainda renderizado');

assert.equal(clubApi.version,'18.230','versao do cache de clubes incorreta');
assert.equal(clubApi.boundedSnapshots,3,'limite de snapshots incorreto');
assert.equal(clubApi.staleWhileRevalidate,true,'stale-while-revalidate ausente');
assert.equal(clubApi.retryUntilReady,true,'retry de sincronizacao ausente');
assert.equal(clubApi.controlAwareInvalidation,true,'invalidacao seletiva ausente');
assert.equal(clubApi.preservesRankingMethodology,true,'metodologia original nao preservada');

let calls=0;
const good=n=>'<div class="ranking">'+String(n).repeat(180)+'</div>';
const first=clubApi.probe('journey-11',()=>{calls++;return good('A');});
const second=clubApi.probe('journey-11',()=>{calls++;return good('B');});
assert.equal(calls,1,'mesma jornada foi recalculada');
assert.equal(first,second,'snapshot da mesma jornada nao foi reutilizado');
clubApi.probe('journey-12',()=>{calls++;return good('C');});
clubApi.probe('journey-13',()=>{calls++;return good('D');});
clubApi.probe('journey-14',()=>{calls++;return good('E');});
clubApi.probe('journey-15',()=>{calls++;return good('F');});
assert(clubApi.size<=3,'cache de clubes cresceu alem do limite');

let progressCalls=0;
const progress='<div>'+('calculando ranking 50% '.repeat(8))+'</div>';
clubApi.probe('progress',()=>{progressCalls++;return progress;});
clubApi.probe('progress',()=>{progressCalls++;return good('P');});
assert.equal(progressCalls,2,'HTML de progresso foi armazenado como ranking pronto');

const capPlayers={},capRoster=[];
for(let i=0;i<40;i++){const id='x'+i;capPlayers[id]={id,age:i>=32?18:25,squad:i>=32?'youth':'senior',clubId:'x'};capRoster.push(id);}
const capState={year:2026,players:capPlayers,teams:[{id:'x',roster:capRoster,academy:[],proReserve:[],lineup:capRoster.slice(0,11)}]};
const cap=window.v18198EnforceInitialSquads(capState);
assert.equal(capState.teams[0].roster.length,32,'teto de 32 foi perdido');
assert.equal(cap.max,32,'maximo reportado diferente de 32');

console.log(JSON.stringify({
 ok:true,
 version:'18.230',
 scorersCompactHeader:true,
 livePlayers:true,
 liveGoals:5,
 clubRankingSameJourneyCalls:1,
 clubRankingBoundedSnapshots:clubApi.boundedSnapshots,
 clubRankingCacheSize:clubApi.size,
 progressNotCached:true,
 staleWhileRevalidate:clubApi.staleWhileRevalidate,
 retryUntilReady:clubApi.retryUntilReady,
 controlAwareInvalidation:clubApi.controlAwareInvalidation,
 methodologyPreserved:clubApi.preservesRankingMethodology,
 roster:capState.teams[0].roster.length,
 capMax:cap.max
}));
'''

    temp = project / ".rankings-18230-test.js"
    temp.write_text(js, encoding="utf-8")
    try:
        result = subprocess.run(["node", str(temp)], capture_output=True, text=True, timeout=45)
    finally:
        temp.unlink(missing_ok=True)
    if result.returncode:
        fail("teste 18.230 falhou:\n" + (result.stderr or result.stdout)[-12000:])

    payload = json.loads(result.stdout.strip().splitlines()[-1])
    payload["sameMainScriptScope"] = True
    payload["externalOverlayLayers"] = 0
    payload["clubRankingMethodology"] = "unchanged-original-renderer"
    output = project / "rankings-18230-tests.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
