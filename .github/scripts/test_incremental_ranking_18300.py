from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def extract(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        fail(f"bloco ausente: {start_marker}")
    return text[start : end + len(end_marker)]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_incremental_ranking_18300.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    patch_script = project.parent / ".github" / "scripts" / "fix_incremental_competition_scope.py"
    if not patch_script.exists():
        patch_script = Path(__file__).resolve().parent / "fix_incremental_competition_scope.py"
    patch = subprocess.run(
        [sys.executable, str(patch_script), str(project)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    if patch.returncode:
        fail("falha ao aplicar escopo da competicao:\n" + (patch.stderr or patch.stdout)[-8000:])

    html = (project / "src" / "index.html").read_text(encoding="utf-8")

    required = [
        "FUTBR_INCREMENTAL_CLUB_RANKING_18300_START",
        "FUTBR_INCREMENTAL_CLUB_RANKING_18301_START",
        "FUTBR_INCREMENTAL_COMPETITION_SCOPE_18302",
        "persistentStore:true",
        "carryAcrossSeason:true",
        "competitionScopedUpdates:true",
        "incrementalRecordColumns:true",
        "rankWindow633:v633RankWindow",
        "Number(s?.v18300ClubRankingStore?.revision)",
        "if(!scoped&&country&&Number.isFinite(division))",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador incremental ausente: " + marker)
    if "O navegador bloqueou o salvamento automático nesta sessão." in html:
        fail("aviso de salvamento web ainda presente")

    block_300 = extract(
        html,
        "/* FUTBR_INCREMENTAL_CLUB_RANKING_18300_START */",
        "/* FUTBR_INCREMENTAL_CLUB_RANKING_18300_END */",
    )
    block_301 = extract(
        html,
        "/* FUTBR_INCREMENTAL_CLUB_RANKING_18301_START */",
        "/* FUTBR_INCREMENTAL_CLUB_RANKING_18301_END */",
    )

    js = r'''
const assert=require('assert');
global.window=global;
global.GestorFC={};
let state=null;
let persisted=0;
function persist(){persisted++;return Promise.resolve();}
const toasts=[];
function toast(message){toasts.push(String(message));}
let baseCalls=0,profileCalls=[],recordBaseCalls=0;
const E={
 country(){return {confederation:'UEFA'};},
 rankCycle633(){return [];},
 rankWindow633(s){return {start:Number(s.year)-4,end:Number(s.year)-1,includeCurrent:false};},
 rankProfile633(s,conf,id){
  profileCalls.push(id);
  const seed=Number(String(id).replace(/\D/g,''))||0,boost=Number(s.lastDay)||0;
  return {points:seed+boost,totalPoints:seed+boost,performancePoints:seed+boost,domesticPoints:boost,continentalPoints:seed,leaguePoints:boost,cupPoints:0,titlePoints:s.cupWinners?.ct0===id?7:0,titleCount:s.cupWinners?.ct0===id?1:0,bestStage:0,recentBest:0,recentTitle:s.cupWinners?.ct0===id?s.year:0,gd:0,gf:0};
 },
 clubRankingRows633(s){
  baseCalls++;
  return (s.teams||[]).map((team,index)=>({id:team.id,conf:'UEFA',points:index,totalPoints:index,performancePoints:index,domesticPoints:0,continentalPoints:index,leaguePoints:0,cupPoints:0,titlePoints:0,titleCount:0,bestStage:0,recentBest:0,recentTitle:0,gd:0,gf:0,globalRank:index+1,confRank:index+1}));
 }
};
function v657ClubRankingRecord(){recordBaseCalls++;return {games:1,wins:1,draws:0,losses:0};}
''' + block_300 + '\n' + block_301 + r'''

const teams=Array.from({length:120},(_,index)=>({id:'t'+index,name:'Clube '+index,short:'C'+index,country:'ct0',division:1,base:60+index%20}));
const participants=teams.slice(0,20).map(team=>team.id);
state={
 year:2026,day:1,lastDay:0,seasonDone:false,teams,
 schedule:[{type:'league',country:'ct0',division:1,fixtures:[{id:'f0',competition:'league1',country:'ct0',division:1,home:'t0',away:'t1',result:{home:1,away:0}}]}],
 competitions:{league1:{id:'league1',participants,standings:Object.fromEntries(participants.map(id=>[id,{}])),groups:[],rounds:{}}},
 cupWinners:{},worldHistory:[],internationalHistory:[]
};

let rows=E.clubRankingRows633(state);
assert.equal(baseCalls,1,'a base mundial deve ser calculada uma vez na migracao');
assert.equal(profileCalls.length,0,'a migracao nao deve recalcular clube por clube');
assert.equal(rows.length,120,'base persistente incompleta');
assert(state.v18300ClubRankingStore,'store persistente ausente');
assert.equal(recordBaseCalls,120,'registros iniciais nao foram consolidados uma unica vez');

rows=E.clubRankingRows633(state);
assert.equal(baseCalls,1,'reabrir a mesma jornada reconstruiu o mundo');
assert.equal(profileCalls.length,0,'reabrir a mesma jornada recalculou clubes');

state.schedule.push({type:'league',country:'ct0',division:1,fixtures:[{id:'f1',competition:'league1',country:'ct0',division:1,home:'t0',away:'t1',result:{home:2,away:2}}]});
state.day=2;state.lastDay=1;
rows=E.clubRankingRows633(state);
assert.equal(baseCalls,1,'nova jornada acionou reconstrucao mundial');
assert.equal(new Set(profileCalls).size,20,'a atualizacao nao ficou limitada a competicao afetada');
assert.equal(profileCalls.length,20,'clubes da competicao foram recalculados mais de uma vez');
const rec0=v657ClubRankingRecord(state,'t0'),rec1=v657ClubRankingRecord(state,'t1');
assert.deepEqual(rec0,{games:2,wins:1,draws:1,losses:0},'J/V/E/D do mandante nao foi atualizado incrementalmente');
assert.deepEqual(rec1,{games:2,wins:1,draws:1,losses:0},'J/V/E/D do visitante nao foi atualizado incrementalmente');

E.clubRankingRows633(state);
assert.equal(profileCalls.length,20,'segunda abertura da mesma jornada recalculou a competicao');

state.schedule.push({type:'cup',country:'ct0',fixtures:[]});
state.cupWinners.ct0='t25';state.day=3;state.lastDay=2;
E.clubRankingRows633(state);
assert.equal(profileCalls.length,21,'titulo novo nao atualizou apenas o campeao');
assert.equal(profileCalls.at(-1),'t25','clube campeao incorreto na atualizacao incremental');

const callsBeforeSeason=profileCalls.length;
state.year=2027;state.day=0;state.lastDay=-1;state.schedule=[];state.cupWinners={};
E.clubRankingRows633(state);
assert.equal(baseCalls,1,'virada de temporada reconstruiu todos os clubes');
assert.equal(profileCalls.length,callsBeforeSeason,'virada sem partidas recalculou clubes');
assert.equal(state.v18300ClubRankingStore.year,2027,'store nao acompanhou o novo ano');
assert.equal(state.v18300ClubRankingStore.rebasePending,true,'mudanca da janela do ciclo nao foi registrada para manutencao posterior');

state=JSON.parse(JSON.stringify(state));
E.clubRankingRows633(state);
assert.equal(baseCalls,1,'save recarregado perdeu a base persistente');
assert.equal(profileCalls.length,callsBeforeSeason,'save recarregado recalculou o mundo');

toast('Temporada 2027 carregada em 1,42 segundos.');
toast('A temporada 2027 comecou.');
assert.deepEqual(toasts,['A temporada 2027 comecou.'],'mensagem tecnica de tempo nao foi filtrada corretamente');

setTimeout(()=>{
 console.log(JSON.stringify({
  ok:true,
  baseWorldCalculations:baseCalls,
  sameJourneyRebuild:false,
  affectedCompetitionClubs:20,
  titleOnlyUpdate:true,
  seasonRolloverWorldRebuild:false,
  persistedAcrossReload:true,
  recordColumnsIncremental:true,
  seasonTimingMessageHidden:true,
  webSaveWarningRemoved:true,
  explicitCompetitionScope:true,
  persistCalls:persisted,
  storeRows:Object.keys(state.v18300ClubRankingStore.rows||{}).length
 }));
},0);
'''

    temp = project / ".incremental-ranking-18300-test.js"
    temp.write_text(js, encoding="utf-8")
    try:
        result = subprocess.run(["node", str(temp)], capture_output=True, text=True, timeout=45)
    finally:
        temp.unlink(missing_ok=True)
    if result.returncode:
        fail("teste incremental falhou:\n" + (result.stderr or result.stdout)[-12000:])

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        fail("teste incremental nao produziu resultado")
    payload = json.loads(lines[-1])
    if not payload.get("ok"):
        fail("resultado incremental invalido")

    output = project / "incremental-ranking-18300-tests.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
