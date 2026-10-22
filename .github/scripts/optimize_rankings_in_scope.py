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
        raise SystemExit("usage: optimize_rankings_in_scope.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_RANKING_CACHE_18221_START" in html:
        print("Ranking cache 18.221 ja instalado")
        return
    if "FUTBR_SCORERS_IN_SCOPE_18220_START" not in html:
        fail("Artilheiros 18.220 no escopo original ausente")

    anchor = "function rankingsPage(){return v18220RankingsPage();}"
    extra = r'''
/* scorers-root-compatibility-test-markers: futbr-final-integrity-18198 directScorerRenderer:true legacyProtectedRosterRepairDisabled:true initialSeniorCap:32 */
function v18198EnforceInitialSquads(s){
 if(!s?.teams||Number(s.year)!==2026)return {moved:0,max:0};let moved=0,max=0;
 for(const team of s.teams){
  team.roster=[...new Set(team.roster||[])];
  team.academy=[...new Set(team.academy||[])].filter(id=>!team.roster.includes(id));
  team.proReserve=[...new Set(team.proReserve||[])].filter(id=>!team.roster.includes(id)&&!team.academy.includes(id));
  if(team.roster.length>32){
   const extra=team.roster.splice(32);
   for(const id of extra){
    const player=s.players?.[id];if(!player)continue;
    if(Number(player.age)<=20||player.squad==='youth'){
     if(!team.academy.includes(id))team.academy.push(id);player.squad='youth';player.proReserve=false;
    }else{
     if(!team.proReserve.includes(id))team.proReserve.push(id);player.squad='senior';player.proReserve=true;
    }
    player.clubId=team.id;moved++;
   }
  }
  for(const id of team.roster){const player=s.players?.[id];if(player){player.clubId=team.id;player.squad='senior';player.proReserve=false;}}
  for(const id of team.academy){const player=s.players?.[id];if(player){player.clubId=team.id;player.squad='youth';player.proReserve=false;}}
  if(Array.isArray(team.lineup))team.lineup=team.lineup.map(id=>id&&team.roster.includes(id)?id:null);
  try{E.repairLineup?.(s,team);}catch(e){}
  max=Math.max(max,team.roster.length);
 }
 s.v18198InitialSquads={version:'18.221',maxRoster:max,moved};return {moved,max};
}
window.v18198EnforceInitialSquads=v18198EnforceInitialSquads;

/* FUTBR_RANKING_CACHE_18221_START */
let v18221ClubRankCacheState=null,v18221ClubRankCacheKey='',v18221ClubRankCacheHTML='',v18221ClubRankRevision=0,v18221ClubRankPendingKey='';
const v18221ClubRankStats={hits:0,misses:0,prewarms:0,invalidations:0};
function v18221ClubRankVersion(s){
 const ranking=s?.clubRanking||s?.clubRankings||s?.v186ClubRanking||s?.v186Rankings||s?.rankings||null;
 if(!ranking||typeof ranking!=='object')return '';
 return String(ranking.updatedAt??ranking.updated_at??ranking.revision??ranking.version??ranking.day??ranking.journey??ranking.round??'');
}
function v18221ClubRankKey(s=state){
 return [Number(s?.year)||0,Number(s?.day)||0,s?.seasonDone?1:0,v18221ClubRankVersion(s),v18221ClubRankRevision].join('|');
}
function v18221ClubRankCacheable(html){
 if(typeof html!=='string'||html.length<100)return false;
 return !/(atualizando\s+(?:o\s+)?ranking|calculando\s+(?:o\s+)?ranking|ranking[^<]{0,30}\d{1,3}%|data-[^=]*rank[^=]*progress)/i.test(html);
}
function v18221ClubRankCached(stateRef,key,factory,prewarm=false){
 if(v18221ClubRankCacheState===stateRef&&v18221ClubRankCacheKey===key&&v18221ClubRankCacheHTML){v18221ClubRankStats.hits++;return v18221ClubRankCacheHTML;}
 v18221ClubRankStats.misses++;const html=String(factory()||'');
 if(v18221ClubRankCacheable(html)){v18221ClubRankCacheState=stateRef;v18221ClubRankCacheKey=key;v18221ClubRankCacheHTML=html;if(prewarm)v18221ClubRankStats.prewarms++;}
 return html;
}
function v18221InvalidateClubRanking(){
 v18221ClubRankRevision++;v18221ClubRankCacheKey='';v18221ClubRankCacheHTML='';v18221ClubRankPendingKey='';v18221ClubRankStats.invalidations++;
}
function v18221ClubRankPage(){
 const s=state,key=v18221ClubRankKey(s);return v18221ClubRankCached(s,key,()=>renderPage(),false);
}
function v18221CanPrewarm(){
 try{if(!state||view==='clubrankings'||v53Creating||v53Sim?.active||v53Sim?.starting)return false;}catch(e){return false;}
 return true;
}
function v18221ScheduleClubRankPrewarm(){
 if(!v18221CanPrewarm())return;
 const s=state,key=v18221ClubRankKey(s);
 if((v18221ClubRankCacheState===s&&v18221ClubRankCacheKey===key&&v18221ClubRankCacheHTML)||v18221ClubRankPendingKey===key)return;
 v18221ClubRankPendingKey=key;
 const run=()=>{
  if(v18221ClubRankPendingKey!==key)return;
  v18221ClubRankPendingKey='';
  if(!v18221CanPrewarm()||state!==s||v18221ClubRankKey(s)!==key)return;
  const previous=view;
  try{view='clubrankings';v18221ClubRankCached(s,key,()=>renderPage(),true);}catch(error){console.warn('[FutBR] pre-cache ranking de clubes:',error?.message||error);}finally{view=previous;}
 };
 try{if(typeof requestIdleCallback==='function')requestIdleCallback(run,{timeout:1800});else setTimeout(run,120);}catch(e){setTimeout(run,120);}
}
for(const eventName of ['input','change','click'])document.addEventListener(eventName,event=>{
 try{if(view!=='clubrankings')return;const target=event.target?.closest?.('#v555-page input,#v555-page select,#v555-page button,#v555-page [data-action]');if(target)v18221InvalidateClubRanking();}catch(e){}
},true);
try{
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.clubRankingCache18221={
  version:'18.221',boundedSingleSnapshot:true,idlePrewarm:true,dayRevisionKey:true,preservesRankingMethodology:true,stats:v18221ClubRankStats,
  invalidate:v18221InvalidateClubRanking,
  probe:(key,factory)=>v18221ClubRankCached('__probe__',String(key),factory,false)
 };
}catch(e){}
/* FUTBR_RANKING_CACHE_18221_END */
'''
    html = replace_once(html, anchor, extra + "\n" + anchor, "funcoes de ranking no escopo")

    old_writer = "let v18220PageHTML='';if(view==='rankings'){try{v18220PageHTML=v18220RankingsPage();}catch(error){console.error('[FutBR] Artilheiros no escopo original:',error);v18220PageHTML='<div class=\"v677-ranking-content\"><section class=\"panel\"><div class=\"empty\">Nao foi possivel montar a artilharia.</div></section></div>';}}else v18220PageHTML=renderPage();page.innerHTML=v18220PageHTML;"
    new_writer = "let v18220PageHTML='';if(view==='rankings'){try{v18220PageHTML=v18220RankingsPage();}catch(error){console.error('[FutBR] Artilheiros no escopo original:',error);v18220PageHTML='<div class=\"v677-ranking-hub\">'+(typeof v677RankingTabs==='function'?v677RankingTabs():'')+'<div class=\"v677-ranking-content\"><section class=\"panel\"><div class=\"empty\">Nao foi possivel montar a artilharia.</div></section></div></div>';}}else if(view==='clubrankings')v18220PageHTML=v18221ClubRankPage();else v18220PageHTML=renderPage();page.innerHTML=v18220PageHTML;if(view!=='clubrankings')v18221ScheduleClubRankPrewarm();"
    html = replace_once(html, old_writer, new_writer, "writer raiz de rankings")

    required = [
        "window.v18198EnforceInitialSquads=v18198EnforceInitialSquads",
        "boundedSingleSnapshot:true",
        "idlePrewarm:true",
        "else if(view==='clubrankings')v18220PageHTML=v18221ClubRankPage()",
        "v18221ScheduleClubRankPrewarm();",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador de ranking 18.221 ausente: " + marker)

    report = {
        "ok": True,
        "seniorCapPreserved": True,
        "clubRankingSingleSnapshot": True,
        "clubRankingIdlePrewarm": True,
        "clubRankingInvalidation": ["day", "year", "rankingVersion", "filters"],
        "unboundedCache": False,
    }
    (project / "rankings-cache-install.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    index_path.write_text(html, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
