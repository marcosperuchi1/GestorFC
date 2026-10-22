from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: stabilize_incremental_ranking_18300.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_INCREMENTAL_CLUB_RANKING_18301_START" in html:
        print("Ranking incremental 18.301 ja estabilizado")
        return
    if "FUTBR_INCREMENTAL_CLUB_RANKING_18300_START" not in html:
        fail("ranking incremental 18.300 ausente")

    # O executavel desktop nao deve exibir o aviso do armazenamento web. O save
    # nativo/fragmentado continua ativo e seus erros reais seguem tratados pela
    # propria camada de persistencia.
    warning = "if(!saveOK&&!window.FutBRDesktop?.available)h+='<div class=\"notice mb16\">O navegador bloqueou o salvamento automático nesta sessão.</div>';"
    html = replace_once(html, warning, "", "retirada definitiva do aviso web no desktop")

    html = replace_once(
        html,
        "rankCycle633:v633Cycle,rankProfile633:v633RankProfile",
        "rankCycle633:v633Cycle,rankWindow633:v633RankWindow,rankProfile633:v633RankProfile",
        "exportacao da janela do ranking",
    )

    anchor = "/* FUTBR_RANKING_CACHE_18230_START */"
    pos = html.find(anchor)
    if pos < 0:
        fail("ponto de insercao 18.301 ausente")

    block = r'''
/* FUTBR_INCREMENTAL_CLUB_RANKING_18301_START */
const v18301BaseClubRecord=typeof v657ClubRankingRecord==='function'?v657ClubRankingRecord:null;
function v18301BlankRecord(){return {games:0,wins:0,draws:0,losses:0};}
function v18301RecordCopy(record){return {games:Number(record?.games)||0,wins:Number(record?.wins)||0,draws:Number(record?.draws)||0,losses:Number(record?.losses)||0};}
function v18301FixtureKey(s,day,index,fixture){return [Number(s?.year)||0,day,fixture?.id||index,fixture?.home||'',fixture?.away||''].join('|');}
function v18301Score(result){
 const home=Number(result?.home??result?.homeGoals??result?.goalsHome??result?.score?.[0]),away=Number(result?.away??result?.awayGoals??result?.goalsAway??result?.score?.[1]);
 return Number.isFinite(home)&&Number.isFinite(away)?[home,away]:null;
}
function v18301AddRecord(store,id,outcome){
 if(!id)return;store.records??={};const record=store.records[id]||(store.records[id]=v18301BlankRecord());record.games++;
 if(outcome>0)record.wins++;else if(outcome<0)record.losses++;else record.draws++;
}
function v18301MarkSeenFixtures(s,store,through){
 store.seenFixtures??={};const end=Math.min(Math.max(-1,Number(through)||-1),(s.schedule||[]).length-1);
 for(let day=0;day<=end;day++)for(const [index,fixture] of (s.schedule?.[day]?.fixtures||[]).entries())if(fixture?.result)store.seenFixtures[v18301FixtureKey(s,day,index,fixture)]=1;
}
function v18301EnsureRecords(s,store){
 if(!store)return;
 if(!store.records){store.records={};for(const id of store.order||[]){let record=null;try{record=v18301BaseClubRecord?.(s,id);}catch(e){}store.records[id]=v18301RecordCopy(record);}v18301MarkSeenFixtures(s,store,store.lastProcessedDay);store.recordRevision=1;v18300SchedulePersist();}
 else{store.seenFixtures??={};store.recordRevision=Number(store.recordRevision)||1;}
}
function v18301CompetitionClubs(s,stage,fixture,affected){
 const add=id=>{if(id)affected.add(id);};
 const competitionId=fixture?.competition||stage?.competition||stage?.competitionId;
 const competition=competitionId?s.competitions?.[competitionId]:null;
 if(competition){
  for(const id of competition.participants||[])add(id);
  for(const id of Object.keys(competition.standings||{}))add(id);
  for(const group of competition.groups||[])for(const id of group||[])add(id);
  for(const ties of Object.values(competition.rounds||{}))for(const tie of Array.isArray(ties)?ties:[]){add(tie?.a);add(tie?.b);add(tie?.winner);}
 }
 const country=fixture?.country||stage?.country,division=Number(fixture?.division??stage?.division);
 if(country&&Number.isFinite(division))for(const team of s.teams||[])if(team.country===country&&Number(team.division||1)===division)add(team.id);
}
const v18301BaseAffectedClubs=v18300AffectedClubs;
v18300AffectedClubs=function(s,store,target){
 v18301EnsureRecords(s,store);
 const affected=v18301BaseAffectedClubs(s,store,target),start=Math.max(0,(Number(store.lastProcessedDay)||-1)+1),end=Math.min(target,(s.schedule||[]).length-1);
 let recordChanged=false;
 for(let day=start;day<=end;day++){
  const stage=s.schedule?.[day];
  for(const [index,fixture] of (stage?.fixtures||[]).entries()){
   if(!fixture?.result)continue;
   affected.add(fixture.home);affected.add(fixture.away);v18301CompetitionClubs(s,stage,fixture,affected);
   const key=v18301FixtureKey(s,day,index,fixture);if(store.seenFixtures[key])continue;
   const score=v18301Score(fixture.result);if(score){const [home,away]=score;v18301AddRecord(store,fixture.home,home===away?0:home>away?1:-1);v18301AddRecord(store,fixture.away,home===away?0:away>home?1:-1);recordChanged=true;}
   store.seenFixtures[key]=1;
  }
 }
 if(recordChanged)store.recordRevision=(Number(store.recordRevision)||0)+1;
 return affected;
};
const v18301BaseBuildStore=v18300BuildStore;
v18300BuildStore=function(s,rows){const store=v18301BaseBuildStore(s,rows);v18301EnsureRecords(s,store);const window=E.rankWindow633?.(s);store.windowKey=window?[window.start,window.end,window.includeCurrent?1:0].join('|'):'';return store;};
const v18301BaseEnsureStore=v18300EnsureStore;
v18300EnsureStore=function(s){const store=v18301BaseEnsureStore(s);if(store){v18301EnsureRecords(s,store);const window=E.rankWindow633?.(s),key=window?[window.start,window.end,window.includeCurrent?1:0].join('|'):'';if(!store.windowKey)store.windowKey=key;else if(key&&store.windowKey!==key){store.windowKey=key;store.rebasePending=true;store.updatedAt=Date.now();v18300SchedulePersist();}}return store;};
v18300SortStore=function(s,store){
 const teamIds=new Set((s.teams||[]).map(team=>team.id));store.order=store.order.filter(id=>store.rows[id]&&teamIds.has(id));store.order.sort((a,b)=>v18300Compare(s,a,b));
 const confCounts={};store.order.forEach((id,index)=>{const row=store.rows[id];row.globalRank=index+1;row.confRank=(confCounts[row.conf]=(confCounts[row.conf]||0)+1);});
};
if(v18301BaseClubRecord){
 v657ClubRankingRecord=function(s,id){const store=v18300EnsureStore(s),record=store?.records?.[id];return record?v18301RecordCopy(record):v18301BaseClubRecord(s,id);};
 try{window.GestorFC.clubRankingRecord657=v657ClubRankingRecord;}catch(e){}
}
try{
 window.GestorFC=window.GestorFC||{};const api=window.GestorFC.clubRankingIncremental18300||(window.GestorFC.clubRankingIncremental18300={});
 Object.assign(api,{version:'18.301',competitionScopedUpdates:true,incrementalRecordColumns:true,optimizedSort:true,desktopWebSaveWarningRemoved:true,rankWindowTracked:true});
}catch(e){}
/* FUTBR_INCREMENTAL_CLUB_RANKING_18301_END */
'''
    html = html[:pos] + block + "\n" + html[pos:]

    required = [
        "FUTBR_INCREMENTAL_CLUB_RANKING_18301_START",
        "rankWindow633:v633RankWindow",
        "competitionScopedUpdates:true",
        "incrementalRecordColumns:true",
        "desktopWebSaveWarningRemoved:true",
        "const teamIds=new Set",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador 18.301 ausente: " + marker)
    if "O navegador bloqueou o salvamento automático nesta sessão." in html:
        fail("aviso web de salvamento ainda presente no HTML final")

    report = {
        "ok": True,
        "version": "18.301",
        "desktopWebSaveWarningRemoved": True,
        "seasonTimingToastHidden": True,
        "competitionScopedUpdates": True,
        "incrementalRecordColumns": True,
        "optimizedOrderSort": True,
        "rankWindowTracked": True,
        "fullWorldRebuildAtSeasonStart": False,
    }
    (project / "incremental-ranking-18301-install.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    index_path.write_text(html, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
