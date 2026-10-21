from __future__ import annotations
import re, sys
from pathlib import Path


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


def function_bounds(src: str, name: str) -> tuple[int, int]:
    match = re.search(r"function\s+" + re.escape(name) + r"\s*\(", src)
    if not match:
        fail(f"funcao JS ausente: {name}")
    brace = src.find("{", match.end())
    if brace < 0:
        fail(f"abertura da funcao ausente: {name}")
    depth = 0
    quote = None
    escaped = False
    for index in range(brace, len(src)):
        ch = src[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
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
                return match.start(), index + 1
    fail(f"funcao JS nao fechada: {name}")


def replace_function(src: str, name: str, replacement: str) -> str:
    start, end = function_bounds(src, name)
    return src[:start] + replacement + src[end:]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_mls_vacation.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    helpers_and_prepare = r'''function v18200MLSResultWinner(s,f,r){
    if(!r)return null;
    let winner=r.winner||null;
    if(!winner&&Array.isArray(r.pens)&&Number(r.pens[0])!==Number(r.pens[1]))winner=Number(r.pens[0])>Number(r.pens[1])?f.home:f.away;
    if(!winner&&Number(r.home)!==Number(r.away))winner=Number(r.home)>Number(r.away)?f.home:f.away;
    if(!winner){
      const text=[s?.seed,s?.year,f?.id||'',f?.phase||'',f?.tieIndex??'',f?.home||'',f?.away||'',r.home,r.away].join('|');
      const h=typeof hash5==='function'?hash5(text):[...text].reduce((n,ch)=>((n*33)^ch.charCodeAt(0))>>>0,5381);
      winner=(h&1)?f.home:f.away;r.pens=winner===f.home?[5,4]:[4,5];r.winner=winner;r.mlsShootoutRepair=true;
    }else r.winner=winner;
    return winner;
  }
  function v18200EnsureMLSMatchWinner(s,f,m){
    if(!m)return null;
    const hg=Number(m.sides?.[0]?.goals)||0,ag=Number(m.sides?.[1]?.goals)||0;
    if(hg!==ag)return hg>ag?f.home:f.away;
    if(!m.pens?.winner){try{shootout(s,m);}catch(e){console.warn('[FutBR] desempate MLS:',e?.message||e);}}
    if(!m.pens?.winner){
      const text=[s?.seed,s?.year,f?.id||'',f?.phase||'',f?.tieIndex??'',f?.home||'',f?.away||'',hg,ag].join('|');
      const h=typeof hash5==='function'?hash5(text):[...text].reduce((n,ch)=>((n*33)^ch.charCodeAt(0))>>>0,5381),winner=(h&1)?f.home:f.away;
      m.pens={score:winner===f.home?[5,4]:[4,5],kicks:[],winner};m.v18200MLSShootoutRepair=true;
    }
    return m.pens.winner;
  }
  function v18200MLSFinalizeChampion(s,c,winner,tie){
    if(!winner||!c)return false;c.mls??={};c.mls.cupRunner=winner===tie?.a?tie?.b:tie?.a;
    if(c.champion)return false;c.champion=winner;
    if(!c.mls.v18200Awarded){const champ=team(s,winner);if(champ){ledger(s,champ,'MLS Cup',Math.round(22000000*financeFactor58(champ)),'Campeao dos playoffs');news(s,'Titulo: MLS Cup',champ.name+' conquistou a MLS Cup '+s.year+'.',winner===s.user?'good':'info');}c.mls.v18200Awarded=true;}
    return true;
  }
  function v18200MLSRepairState(s,c){
    if(!s||!c?.rounds)return 0;const fixtures=[];
    for(let di=0;di<(s.schedule||[]).length;di++){const d=s.schedule[di];if(d?.type!=='mlsplayoff')continue;for(const f of d.fixtures||[])if(f?.result&&f.phase!=null&&f.tieIndex!=null)fixtures.push({di,f});}
    let repaired=0;
    for(const [phase,ties] of Object.entries(c.rounds||{}))for(const [index,tie] of (ties||[]).entries()){
      const fs=fixtures.filter(x=>x.f.phase===phase&&Number(x.f.tieIndex)===Number(index)).sort((a,b)=>a.di-b.di||Number(a.f.leg||1)-Number(b.f.leg||1));if(!fs.length)continue;
      const series=fs.some(x=>x.f.mlsSeries)||!!tie.wins,wins={[tie.a]:0,[tie.b]:0},rows=[];
      for(const {f} of fs){const r=f.result,winner=v18200MLSResultWinner(s,f,r);if(!winner)continue;if(series)wins[winner]=(wins[winner]||0)+1;rows.push({fixtureId:f.id,home:f.home,away:f.away,...r});}
      tie.results=rows;
      if(series){tie.wins=wins;tie.winner=wins[tie.a]>=2?tie.a:wins[tie.b]>=2?tie.b:null;}else tie.winner=rows.length?v18200MLSResultWinner(s,fs.at(-1).f,fs.at(-1).f.result):tie.winner;
      if(tie.winner){for(const {f} of fs)f.result.qualifier=tie.winner;}
      repaired++;
    }
    c.played=Math.max(Number(c.played)||0,fixtures.length);c.mls??={};c.mls.conferenceChampions??={};
    const east=c.rounds.conf_east?.[0]?.winner,west=c.rounds.conf_west?.[0]?.winner;if(east)c.mls.conferenceChampions.east=east;if(west)c.mls.conferenceChampions.west=west;
    const final=c.rounds.mls_cup?.[0];if(final?.winner)v18200MLSFinalizeChampion(s,c,final.winner,final);
    c.mls.v18200Reconciled=true;return repaired;
  }
  function v18200MLSNormalizeSchedule(s){
    if(!Array.isArray(s?.schedule))return 0;const old=s.schedule,oldDay=Math.max(0,Number(s.day)||0),groups=new Map();
    old.forEach((d,i)=>{if(d?.type!=='mlsplayoff')return;const key=Number(d.round);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(i);});
    const keep=new Set();for(const indexes of groups.values()){
      const past=indexes.filter(i=>i<=oldDay&&(old[i].fixtures||[]).some(f=>f.result));
      const any=indexes.filter(i=>(old[i].fixtures||[]).some(f=>f.result));
      keep.add(past.at(-1)??(indexes.includes(oldDay)&&any.includes(oldDay)?oldDay:null)??any[0]??indexes[0]);
    }
    let removed=0,before=0;s.schedule=old.filter((d,i)=>{if(d?.type!=='mlsplayoff'||keep.has(i))return true;removed++;if(i<oldDay)before++;return false;});s.day=Math.max(0,oldDay-before);return removed;
  }
  function v18200MLSStageLabel(round){return ({0:'MLS Cup Playoffs - Wild Card',1:'MLS Cup Playoffs - Round One / jogo 1',2:'MLS Cup Playoffs - Round One / jogo 2',3:'MLS Cup Playoffs - Round One / jogo 3',4:'MLS Cup Playoffs - Semifinais de Conferencia',5:'MLS Cup Playoffs - Finais de Conferencia',6:'MLS Cup'}[Number(round)]||'MLS Cup Playoffs');}
  function v18200MLSEnsureStage(s,round){
    const existing=(s.schedule||[]).findIndex(d=>d?.type==='mlsplayoff'&&Number(d.round)===Number(round));if(existing>=0)return existing;
    const stage=v629MLSStage(Number(round),v18200MLSStageLabel(round));let at=(s.schedule||[]).findIndex((d,i)=>i>=Number(s.day||0)&&d?.type==='mlsplayoff'&&Number(d.round)>Number(round));if(at<0)at=(s.schedule||[]).length;s.schedule.splice(at,0,stage);
    if(s.vacation?.active){if(s.vacation.untilSeason)s.vacation.remaining=Math.max(1,s.schedule.length-(Number(s.day)||0));else s.vacation.remaining=(Number(s.vacation.remaining)||0)+1;}return at;
  }
  function v18200MLSRequiredRound(s,c){
    if(!c?.mls?.seeded||!c.rounds?.wild_east||!c.rounds?.wild_west||!c.rounds.wild_east[0]?.winner||!c.rounds.wild_west[0]?.winner)return 0;
    const all=[...(c.rounds.r1_east||[]),...(c.rounds.r1_west||[])];if(all.length<8)return 1;
    const games=t=>Array.isArray(t.results)?t.results.length:0;if(all.some(t=>games(t)<1))return 1;if(all.some(t=>games(t)<2))return 2;if(all.some(t=>!t.winner))return 3;
    const semis=[...(c.rounds.semi_east||[]),...(c.rounds.semi_west||[])];if(semis.length<4||semis.some(t=>!t.winner))return 4;
    const conf=[...(c.rounds.conf_east||[]),...(c.rounds.conf_west||[])];if(conf.length<2||conf.some(t=>!t.winner))return 5;
    if(!c.champion)return 6;return null;
  }
  function v18200MLSPruneObsoleteFuture(s,required){
    if(required==null||!Array.isArray(s?.schedule))return 0;const day=Math.max(0,Number(s.day)||0),old=s.schedule;let before=0,removed=0,keptRequired=false;
    s.schedule=old.filter((d,i)=>{if(i<day||d?.type!=='mlsplayoff')return true;const r=Number(d.round);if(r<Number(required)){removed++;if(i<day)before++;return false;}if(r===Number(required)){if(keptRequired){removed++;return false;}keptRequired=true;}return true;});s.day=Math.max(0,day-before);return removed;
  }
  function v18200MLSEnsureResolutionStages(s,c){
    const all=[...(c?.rounds?.r1_east||[]),...(c?.rounds?.r1_west||[])];if(!all.length)return false;
    const round2=s.schedule?.find(d=>d?.type==='mlsplayoff'&&Number(d.round)===2),twoDone=all.every(t=>(t.results||[]).length>=2)||!!(round2?.prepared&&round2.fixtures?.length&&round2.fixtures.every(f=>f.result));if(!twoDone)return false;
    const needs=all.some(t=>!t.winner);if(needs)v18200MLSEnsureStage(s,3);v18200MLSEnsureStage(s,4);c.mls??={};c.mls.r1Scheduled=true;return true;
  }
  function v18200MLSRecover(s){
    const c=s?.competitions?.mls;if(!c)return false;v18200MLSNormalizeSchedule(s);v18200MLSRepairState(s,c);v18200MLSEnsureResolutionStages(s,c);const required=v18200MLSRequiredRound(s,c);v18200MLSPruneObsoleteFuture(s,required);if(required!=null){const at=v18200MLSEnsureStage(s,required);if(Number(s.day)>=s.schedule.length)s.day=at;}c.mls.v18200RequiredRound=required;c.mls.v18200Recovery=true;return true;
  }
  function v629MLSPreparePlayoffStage(s,d){
    d.prepared=true;const c=s.competitions.mls;if(!c)return;v18200MLSRepairState(s,c);v629MLSSeed(s,c);
    const makeSingles=(key,pairs,final=false)=>{c.rounds[key]??=pairs.map(([a,b])=>v629MLSTie(a,b));c.rounds[key].forEach((tie,i)=>{if(tie.a&&tie.b&&!tie.winner)d.fixtures.push(v629MLSFixture(s,d,key,i,tie,1,false,final));});};
    if(d.round===0){makeSingles('wild_east',[[c.mls.seeds.east[7],c.mls.seeds.east[8]]]);makeSingles('wild_west',[[c.mls.seeds.west[7],c.mls.seeds.west[8]]]);return;}
    if(d.round===1){for(const conf of ['east','west']){const wild=c.rounds['wild_'+conf]?.[0]?.winner,seeds=c.mls.seeds[conf],key='r1_'+conf;if(!wild)throw Error('Wild Card da MLS ainda sem vencedor.');c.rounds[key]??=[v629MLSTie(seeds[0],wild,{wins:{}}),v629MLSTie(seeds[1],seeds[6],{wins:{}}),v629MLSTie(seeds[2],seeds[5],{wins:{}}),v629MLSTie(seeds[3],seeds[4],{wins:{}})];c.rounds[key].forEach((tie,i)=>{tie.wins[tie.a]??=0;tie.wins[tie.b]??=0;if(!tie.winner)d.fixtures.push(v629MLSFixture(s,d,key,i,tie,1,true,false));});}return;}
    if(d.round===2||d.round===3){const game=d.round===2?2:3;for(const conf of ['east','west']){const key='r1_'+conf;for(const [i,tie] of (c.rounds[key]||[]).entries())if(!tie.winner)d.fixtures.push(v629MLSFixture(s,d,key,i,tie,game,true,false));}return;}
    if(d.round===4){for(const conf of ['east','west']){const r1=c.rounds['r1_'+conf]||[];if(r1.length!==4||r1.some(t=>!t.winner))throw Error('Round One da MLS ainda nao concluida.');const pairs=[[r1[0].winner,r1[3].winner],[r1[1].winner,r1[2].winner]].map(([a,b])=>v629MLSHigherSeed(c,a,b));makeSingles('semi_'+conf,pairs);}return;}
    if(d.round===5){for(const conf of ['east','west']){const semis=c.rounds['semi_'+conf]||[];if(semis.length!==2||semis.some(t=>!t.winner))throw Error('Semifinais de conferencia da MLS ainda nao concluidas.');const pair=v629MLSHigherSeed(c,semis[0].winner,semis[1].winner);makeSingles('conf_'+conf,[pair]);}return;}
    if(d.round===6){const e=c.rounds.conf_east?.[0]?.winner,w=c.rounds.conf_west?.[0]?.winner;if(!e||!w)throw Error('Finais de conferencia da MLS ainda nao concluidas.');const pair=v629MLSHigherSeed(c,e,w,true);makeSingles('mls_cup',[pair],true);}
  }'''
    html = replace_function(html, "v629MLSPreparePlayoffStage", helpers_and_prepare)

    schedule_resolution = r'''function v629MLSScheduleResolution(s,c){
    v18200MLSRepairState(s,c);const all=[...(c.rounds.r1_east||[]),...(c.rounds.r1_west||[])];if(!all.length)return false;const needs=all.some(t=>!t.winner);if(needs)v18200MLSEnsureStage(s,3);v18200MLSEnsureStage(s,4);c.mls.r1Scheduled=true;if(s.vacation?.active&&s.vacation.untilSeason)s.vacation.remaining=Math.max(1,s.schedule.length-(Number(s.day)||0));return true;
  }'''
    html = replace_function(html, "v629MLSScheduleResolution", schedule_resolution)

    apply_result = r'''function v629MLSApplyResult(s,f,m){
    v18200EnsureMLSMatchWinner(s,f,m);const r=v3ApplyMatch(s,m);f.result=r;const c=s.competitions.mls;if(!c)throw Error('Competicao MLS ausente.');c.played=(c.played||0)+1;const tie=c.rounds[f.phase]?.[f.tieIndex];if(!tie)throw Error('Confronto da MLS nao encontrado.');const winner=v18200MLSResultWinner(s,f,r);tie.results??=[];tie.results.push({fixtureId:f.id,home:f.home,away:f.away,...r});
    if(f.mlsSeries){tie.wins??={};tie.wins[winner]=(tie.wins[winner]||0)+1;if(tie.wins[winner]>=2)tie.winner=winner;}else tie.winner=winner;if(tie.winner)r.qualifier=tie.winner;
    if(f.phase==='conf_east'&&tie.winner)c.mls.conferenceChampions.east=tie.winner;if(f.phase==='conf_west'&&tie.winner)c.mls.conferenceChampions.west=tie.winner;if(f.phase==='mls_cup'&&tie.winner)v18200MLSFinalizeChampion(s,c,tie.winner,tie);
    performanceDevelopment58(s,m);v18200MLSRepairState(s,c);if(Number(f.mlsRound)===2){const stage=s.schedule[s.day];if(stage?.type==='mlsplayoff'&&stage.fixtures.every(x=>x.result))v629MLSScheduleResolution(s,c);}return r;
  }'''
    html = replace_function(html, "v629MLSApplyResult", apply_result)

    old_prepare_wrapper = "v4_prepareStage=function(s){const d=s.schedule[s.day];if(d?.type==='mlsplayoff'&&!d.prepared){v629MLSPreparePlayoffStage(s,d);return;}return v629BasePrepareStage(s);};"
    new_prepare_wrapper = "v4_prepareStage=function(s){let d=s.schedule[s.day];if(d?.type==='mlsplayoff'){v18200MLSRecover(s);d=s.schedule[s.day];if(d?.type==='mlsplayoff'){if(!d.prepared)v629MLSPreparePlayoffStage(s,d);return;}}return v629BasePrepareStage(s);};"
    html = replace_once(html, old_prepare_wrapper, new_prepare_wrapper, "prepareStage MLS recuperavel")

    old_complete_start = "const v629BaseCompleteSeason=completeSeason;\n  completeSeason=function(s){"
    start = html.find(old_complete_start)
    end_marker = "\n  const usaCatalog629="
    end = html.find(end_marker, start)
    if start < 0 or end < 0:
        fail("wrapper completeSeason da MLS nao encontrado")
    old_block = html[start:end]
    history_tail_start = old_block.find("const out=v629BaseCompleteSeason(s)")
    if history_tail_start < 0:
        fail("corpo completeSeason MLS inesperado")
    replacement = r'''const v629BaseCompleteSeason=completeSeason;
  completeSeason=function(s){
    const mls=s?.competitions?.mls;if(mls){v18200MLSRecover(s);if(!mls.champion){const required=v18200MLSRequiredRound(s,mls);if(required!=null){const at=v18200MLSEnsureStage(s,required);s.seasonDone=false;if(Number(s.day)>=s.schedule.length)s.day=at;prepareStage(s);return false;}}}
    const out=v629BaseCompleteSeason(s),champId=s.competitions?.mls?.champion;if(champId){const world=s.worldHistory?.find(x=>Number(x.year)===Number(s.year)),row=world?.countries?.find(x=>x.country==='usa');if(row){row.champion=champId;row.leagueRunnerUp=s.competitions.mls.mls?.cupRunner||row.leagueRunnerUp;}const h=s.history?.find(x=>Number(x.year)===Number(s.year));if(h&&h.country==='usa'){const club=team(s,s.user),conf=club?.mlsConference||'east',ct=v629MLSConferenceTable(s,conf);h.position=ct.findIndex(t=>t.id===s.user)+1;h.champion=team(s,champId)?.name||h.champion;}}return out;};'''
    html = html[:start] + replacement + html[end:]

    validate_anchor = "  const usaCatalog629=WorldCatalog.countries.find(c=>c.id==='usa');"
    validate_patch = r'''  const v18200BaseMLSValidate=validate;
  validate=function(s){const out=v18200BaseMLSValidate(s);try{v18200MLSRecover(out);}catch(e){console.warn('[FutBR] recuperacao MLS no load:',e?.message||e);}return out;};
  const usaCatalog629=WorldCatalog.countries.find(c=>c.id==='usa');'''
    html = replace_once(html, validate_anchor, validate_patch, "recuperacao MLS durante validate")

    if "Playoff da MLS sem vencedor." in html:
        fail("excecao antiga da MLS ainda permanece")
    marker = "window.GestorFC=window.GestorFC||{};window.GestorFC.mlsVacation18200={version:'18.200',mandatoryShootout:true,idempotentRecovery:true,noRestartOnResume:true,seasonWaitsForCup:true};"
    html = html.rstrip() + "\n<script id=\"futbr-mls-vacation-18200-meta\">" + marker + "</script>\n"
    index_path.write_text(html, encoding="utf-8")
    print("MLS vacation/playoff recovery 18.200 applied")


if __name__ == "__main__":
    main()
