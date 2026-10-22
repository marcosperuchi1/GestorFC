from __future__ import annotations

import json
import re
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
        raise SystemExit("usage: fix_incremental_club_ranking.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_INCREMENTAL_CLUB_RANKING_18300_START" in html:
        print("Ranking incremental 18.300 ja instalado")
        return
    if "FUTBR_RANKING_CACHE_18230_START" not in html:
        fail("Rankings 18.230 ausente")

    # No desktop, o banco nativo e a autoridade. A falha do localStorage/IndexedDB
    # do WebView nao deve gerar um aviso permanente quando a ponte nativa existe.
    old_notice = "if(!saveOK)h+='<div class=\"notice mb16\">O navegador bloqueou o salvamento automático nesta sessão.</div>';"
    new_notice = "if(!saveOK&&!window.FutBRDesktop?.available)h+='<div class=\"notice mb16\">O navegador bloqueou o salvamento automático nesta sessão.</div>';"
    html = replace_once(html, old_notice, new_notice, "aviso de salvamento desktop")

    # Expor o ciclo uma unica vez permite recalcular somente os clubes afetados,
    # sem remontar a janela de quatro anos para cada clube.
    export_old = "clubRankingRows633:v633ClubRankingRows,rankProfile633:v633RankProfile,titleLedger633:v633ClubTitleLedger"
    export_new = "clubRankingRows633:v633ClubRankingRows,rankCycle633:v633Cycle,rankProfile633:v633RankProfile,titleLedger633:v633ClubTitleLedger"
    html = replace_once(html, export_old, export_new, "exportacao do ciclo do ranking")

    # O cache visual passa a acompanhar a revisao real do coeficiente persistente,
    # em vez de invalidar cegamente por ano/dia.
    old_base_key = "return [Number(s?.year)||0,Number(s?.day)||0,s?.seasonDone?1:0,v18221ClubRankVersion(s)].join('|');"
    new_base_key = "return [Number(s?.year)||0,Number(s?.v18300ClubRankingStore?.revision)||0,s?.seasonDone?1:0,v18221ClubRankVersion(s)].join('|');"
    html = replace_once(html, old_base_key, new_base_key, "chave incremental do ranking")

    anchor = "/* FUTBR_RANKING_CACHE_18230_START */"
    pos = html.find(anchor)
    if pos < 0:
        fail("ponto de insercao do ranking incremental ausente")

    block = r'''
/* FUTBR_INCREMENTAL_CLUB_RANKING_18300_START */
const V18300_CLUB_RANK_VERSION=1;
const v18300BaseClubRankingRows=E.clubRankingRows633?.bind(E);
let v18300PersistQueued=false;
function v18300SchedulePersist(){
 if(v18300PersistQueued||!state)return;v18300PersistQueued=true;
 queueMicrotask(()=>{v18300PersistQueued=false;try{const out=persist();if(out?.catch)out.catch(()=>{});}catch(e){}});
}
function v18300RankTargetDay(s){
 const last=Number(s?.lastDay);if(Number.isFinite(last))return Math.max(-1,Math.floor(last));
 return Math.max(-1,(Number(s?.day)||0)-1);
}
function v18300Conf(s,team,row){
 if(row?.conf)return row.conf;
 try{return E.country(team?.country)?.confederation||E.country(team?.country)?.conf||'';}catch(e){return '';}
}
function v18300MinimalRow(row){
 return {id:row.id,conf:row.conf||'',points:Number(row.points)||0,totalPoints:Number(row.totalPoints??row.points)||0,performancePoints:Number(row.performancePoints??row.points)||0,domesticPoints:Number(row.domesticPoints)||0,continentalPoints:Number(row.continentalPoints)||0,leaguePoints:Number(row.leaguePoints)||0,cupPoints:Number(row.cupPoints)||0,titlePoints:Number(row.titlePoints)||0,titleCount:Number(row.titleCount)||0,bestStage:Number(row.bestStage)||0,recentBest:Number(row.recentBest)||0,recentTitle:Number(row.recentTitle)||0,gd:Number(row.gd)||0,gf:Number(row.gf)||0,globalRank:Number(row.globalRank)||0,confRank:Number(row.confRank)||0};
}
function v18300RowsReady(rows){
 return Array.isArray(rows)&&rows.length>100&&rows.some(row=>Number.isFinite(Number(row?.totalPoints??row?.points)))&&rows.every(row=>row?.id);
}
function v18300CandidateRows(s){
 const candidates=[];
 for(const [key,value] of Object.entries(s||{})){
  if(!/club.*rank|rank.*club/i.test(key))continue;
  if(Array.isArray(value))candidates.push(value);
  else if(Array.isArray(value?.rows))candidates.push(value.rows);
 }
 return candidates.find(v18300RowsReady)||null;
}
function v18300BuildStore(s,rows){
 const map={},order=[];
 for(const row of rows){if(!row?.id||map[row.id])continue;map[row.id]=v18300MinimalRow(row);order.push(row.id);}
 const store={version:V18300_CLUB_RANK_VERSION,model:'persistent-incremental-18.300',year:Number(s.year)||0,lastProcessedDay:v18300RankTargetDay(s),revision:1,rows:map,order,seenTitles:{},createdAt:Date.now(),updatedAt:Date.now()};
 s.v18300ClubRankingStore=store;v18300CaptureTitles(s,store);v18300SchedulePersist();return store;
}
function v18300CaptureTitles(s,store,affected=null){
 store.seenTitles??={};
 const add=(key,id)=>{if(!id||store.seenTitles[key])return;store.seenTitles[key]=id;if(affected)affected.add(id);};
 for(const [country,winner] of Object.entries(s?.cupWinners||{}))add('cup:'+s.year+':'+country,winner);
 for(const competition of Object.values(s?.competitions||{}))if(competition?.champion)add('competition:'+s.year+':'+competition.id,competition.champion);
 for(const season of s?.worldHistory||[]){const year=Number(season?.year);if(!Number.isFinite(year))continue;for(const row of season?.countries||[]){if(row?.champion)add('league:'+year+':'+row.country+':1',row.champion);if(row?.secondChampion)add('league:'+year+':'+row.country+':2',row.secondChampion);if(row?.cup)add('cup-history:'+year+':'+row.country,row.cup);}}
 for(const rec of s?.internationalHistory||[])if(rec?.champion)add('international:'+rec.year+':'+rec.id,rec.champion);
}
function v18300AffectedClubs(s,store,target){
 const affected=new Set(),start=Math.max(0,(Number(store.lastProcessedDay)||-1)+1),end=Math.min(target,(s.schedule||[]).length-1);
 for(let index=start;index<=end;index++)for(const fixture of s.schedule?.[index]?.fixtures||[]){if(!fixture?.result)continue;if(fixture.home)affected.add(fixture.home);if(fixture.away)affected.add(fixture.away);}
 v18300CaptureTitles(s,store,affected);return affected;
}
function v18300UpdateRow(s,store,id,cycle){
 const team=(s.teams||[]).find(item=>item.id===id);if(!team)return false;
 const previous=store.rows[id],conf=v18300Conf(s,team,previous);if(!conf)return false;
 try{
  const profile=E.rankProfile633?.(s,conf,id,cycle);if(!profile)return false;
  store.rows[id]=v18300MinimalRow({id,conf,...profile,globalRank:previous?.globalRank||0,confRank:previous?.confRank||0});
  if(!store.order.includes(id))store.order.push(id);return true;
 }catch(error){console.warn('[FutBR] atualizacao incremental do ranking:',id,error?.message||error);return false;}
}
function v18300Compare(s,a,b){
 const A=storeRow(a),B=storeRow(b),ta=(s.teams||[]).find(t=>t.id===a),tb=(s.teams||[]).find(t=>t.id===b);
 function storeRow(id){return s.v18300ClubRankingStore?.rows?.[id]||{};}
 return (Number(B.totalPoints)-Number(A.totalPoints))||(Number(B.performancePoints)-Number(A.performancePoints))||(Number(B.titlePoints)-Number(A.titlePoints))||(Number(B.continentalPoints)-Number(A.continentalPoints))||(Number(B.domesticPoints)-Number(A.domesticPoints))||(Number(B.titleCount)-Number(A.titleCount))||(Number(B.bestStage)-Number(A.bestStage))||(Number(B.recentTitle)-Number(A.recentTitle))||(Number(B.recentBest)-Number(A.recentBest))||(Number(B.gd)-Number(A.gd))||(Number(B.gf)-Number(A.gf))||((Number(tb?.base)||0)-(Number(ta?.base)||0))||String(ta?.name||a).localeCompare(String(tb?.name||b),'pt-BR');
}
function v18300SortStore(s,store){
 store.order=store.order.filter(id=>store.rows[id]&&(s.teams||[]).some(team=>team.id===id));store.order.sort((a,b)=>v18300Compare(s,a,b));
 const confCounts={};store.order.forEach((id,index)=>{const row=store.rows[id];row.globalRank=index+1;row.confRank=(confCounts[row.conf]=(confCounts[row.conf]||0)+1);});
}
function v18300HydrateRows(s,store){
 const teams=new Map((s.teams||[]).map(team=>[team.id,team]));return store.order.map(id=>{const row=store.rows[id],team=teams.get(id);return row&&team?{...row,name:team.name,short:team.short,country:team.country,base:team.base}:null;}).filter(Boolean);
}
function v18300EnsureStore(s){
 let store=s?.v18300ClubRankingStore;
 if(store?.version!==V18300_CLUB_RANK_VERSION||!store?.rows||!Array.isArray(store?.order)){
  const candidate=v18300CandidateRows(s);if(candidate)return v18300BuildStore(s,candidate);
  const rows=v18300BaseClubRankingRows?.(s)||[];if(v18300RowsReady(rows))return v18300BuildStore(s,rows);return null;
 }
 if(Number(store.year)!==Number(s.year)){
  // Fim do ano anterior e inicio do novo usam a mesma janela de quatro anos.
  // Preservar a base evita uma reconstrucao mundial sem nenhum jogo novo.
  store.year=Number(s.year)||0;store.lastProcessedDay=-1;store.updatedAt=Date.now();store.revision=(Number(store.revision)||0)+1;v18300CaptureTitles(s,store);v18300SchedulePersist();
 }
 const target=v18300RankTargetDay(s);
 if(target>Number(store.lastProcessedDay??-1)){
  const affected=v18300AffectedClubs(s,store,target),cycle=E.rankCycle633?.(s);let changed=0;
  for(const id of affected)if(v18300UpdateRow(s,store,id,cycle))changed++;
  store.lastProcessedDay=target;store.updatedAt=Date.now();
  if(changed){v18300SortStore(s,store);store.revision=(Number(store.revision)||0)+1;}
  v18300SchedulePersist();
 }
 return store;
}
if(v18300BaseClubRankingRows)E.clubRankingRows633=function(s){
 const store=v18300EnsureStore(s);return store?v18300HydrateRows(s,store):v18300BaseClubRankingRows(s);
};
function v18300HideTimingMessage(message){
 const text=String(message||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 return /temporada/.test(text)&&/(carreg|process|gerad|conclu|prepar)/.test(text)&&(/\d+(?:[.,]\d+)?\s*(?:ms|s|seg|segundo|segundos)\b/.test(text)||/tempo\s*:/.test(text));
}
const v18300BaseToast=toast;
toast=function(message,...args){if(v18300HideTimingMessage(message))return;return v18300BaseToast.call(this,message,...args);};
try{window.GestorFC=window.GestorFC||{};window.GestorFC.clubRankingIncremental18300={version:'18.300',persistentStore:true,carryAcrossSeason:true,affectedClubsOnly:true,titleEvents:true,baseMethodologyPreserved:true,hideInternalSeasonTiming:true,store:()=>state?.v18300ClubRankingStore||null};}catch(e){}
/* FUTBR_INCREMENTAL_CLUB_RANKING_18300_END */
'''

    html = html[:pos] + block + "\n" + html[pos:]

    required = [
        "FUTBR_INCREMENTAL_CLUB_RANKING_18300_START",
        "rankCycle633:v633Cycle",
        "persistentStore:true",
        "carryAcrossSeason:true",
        "affectedClubsOnly:true",
        "!window.FutBRDesktop?.available",
        "Number(s?.v18300ClubRankingStore?.revision)",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador incremental ausente: " + marker)

    report = {
        "ok": True,
        "version": "18.300",
        "desktopSaveWarningHiddenWhenNativeStorageAvailable": True,
        "seasonTimingToastHidden": True,
        "clubRankingPersistentStore": True,
        "clubRankingCarriesAcrossSeason": True,
        "clubRankingUpdatesAffectedClubsOnly": True,
        "clubRankingTitleEvents": True,
        "clubRankingMethodology": "rankProfile633-original",
        "structuralPerformancePreserved": True,
    }
    (project / "incremental-ranking-18300-install.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    index_path.write_text(html, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
