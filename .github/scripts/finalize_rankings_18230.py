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
        raise SystemExit("usage: finalize_rankings_18230.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_RANKING_CACHE_18230_START" in html:
        print("Rankings 18.230 ja finalizados")
        return
    if "FUTBR_RANKING_CACHE_18221_START" not in html:
        fail("cache de clubes 18.221 ausente")
    if "FUTBR_SCORERS_IN_SCOPE_18220_START" not in html:
        fail("Artilheiros in-scope 18.220 ausente")

    old_header = "return '<section class=\"panel\" data-v18220-scorers-root=\"1\"><div class=\"panel-head\"><div><h3>Ranking de Artilheiros</h3><span class=\"tiny muted\">Estatisticas da temporada, copas e selecoes</span></div></div><div class=\"panel-body\"><div class=\"filters\">'+"
    new_header = "return '<section class=\"panel\" data-v18220-scorers-root=\"1\" data-v18230-compact-header=\"1\"><div class=\"panel-body\"><div class=\"filters\">'+"
    html = replace_once(html, old_header, new_header, "cabecalho compacto de Artilheiros")

    start_marker = "/* FUTBR_RANKING_CACHE_18221_START */"
    end_marker = "/* FUTBR_RANKING_CACHE_18221_END */"
    start = html.find(start_marker)
    end = html.find(end_marker, start)
    if start < 0 or end < 0:
        fail("bloco 18.221 nao localizado")
    end += len(end_marker)

    cache_block = r'''/* FUTBR_RANKING_CACHE_18230_START */
let v18221ClubRankCacheState=null,v18221ClubRankCacheKey='',v18221ClubRankCacheHTML='',v18221ClubRankRevision=0,v18221ClubRankPendingKey='';
const v18221ClubRankStats={hits:0,misses:0,prewarms:0,invalidations:0,retries:0,staleServed:0,swaps:0};
let v18230ClubRankEntries=new Map(),v18230ClubRankLastHTML='',v18230ClubRankLastBaseKey='',v18230ClubRankFilterTimer=0;
const V18230_CLUB_RANK_CACHE_MAX=3;
function v18221ClubRankVersion(s){
 const ranking=s?.clubRanking||s?.clubRankings||s?.v186ClubRanking||s?.v186Rankings||s?.rankings||null;
 if(!ranking||typeof ranking!=='object')return '';
 return String(ranking.updatedAt??ranking.updated_at??ranking.revision??ranking.version??ranking.day??ranking.journey??ranking.round??'');
}
function v18230ClubRankBaseKey(s=state){
 return [Number(s?.year)||0,Number(s?.day)||0,s?.seasonDone?1:0,v18221ClubRankVersion(s)].join('|');
}
function v18221ClubRankKey(s=state){return v18230ClubRankBaseKey(s)+'|'+v18221ClubRankRevision;}
function v18221ClubRankCacheable(html){
 if(typeof html!=='string'||html.length<100)return false;
 return !/(atualizando\s+(?:o\s+)?ranking|calculando\s+(?:o\s+)?ranking|sincronizando\s+(?:o\s+)?ranking|ranking[^<]{0,30}\d{1,3}%|data-[^=]*rank[^=]*progress)/i.test(html);
}
function v18230ResetForState(stateRef){
 if(v18221ClubRankCacheState===stateRef)return;
 v18221ClubRankCacheState=stateRef;v18230ClubRankEntries=new Map();v18221ClubRankCacheKey='';v18221ClubRankCacheHTML='';v18230ClubRankLastHTML='';v18230ClubRankLastBaseKey='';v18221ClubRankPendingKey='';
}
function v18230RememberClubRank(stateRef,key,baseKey,html,prewarm=false){
 v18230ResetForState(stateRef);
 if(v18230ClubRankEntries.has(key))v18230ClubRankEntries.delete(key);
 v18230ClubRankEntries.set(key,html);
 while(v18230ClubRankEntries.size>V18230_CLUB_RANK_CACHE_MAX)v18230ClubRankEntries.delete(v18230ClubRankEntries.keys().next().value);
 v18221ClubRankCacheKey=key;v18221ClubRankCacheHTML=html;v18230ClubRankLastHTML=html;v18230ClubRankLastBaseKey=baseKey;
 if(prewarm)v18221ClubRankStats.prewarms++;
}
function v18221ClubRankCached(stateRef,key,factory,prewarm=false,baseKey=key){
 v18230ResetForState(stateRef);
 if(v18230ClubRankEntries.has(key)){
  const html=v18230ClubRankEntries.get(key);v18230ClubRankEntries.delete(key);v18230ClubRankEntries.set(key,html);v18221ClubRankStats.hits++;return html;
 }
 v18221ClubRankStats.misses++;
 const html=String(factory()||'');
 if(v18221ClubRankCacheable(html))v18230RememberClubRank(stateRef,key,baseKey,html,prewarm);
 return html;
}
function v18230RankBusy(){
 try{return !!((typeof v53Creating!=='undefined'&&v53Creating)||(typeof v53Sim!=='undefined'&&(v53Sim?.active||v53Sim?.starting)));}catch(e){return false;}
}
function v18230ComputeClubRank(s,key,baseKey,prewarm=false){
 const previous=view;let html='';
 try{view='clubrankings';html=v18221ClubRankCached(s,key,()=>renderPage(),prewarm,baseKey);}finally{view=previous;}
 return html;
}
function v18230SyncNotice(html){
 const notice='<div class="v18230-club-rank-sync tiny muted" style="padding:6px 12px;text-align:right">Sincronizando a jornada atual em segundo plano...</div>';
 const needle='<div class="v677-ranking-content">';
 return html.includes(needle)?html.replace(needle,needle+notice):notice+html;
}
function v18230SwapVisibleClubRank(s,key,html){
 try{
  if(view!=='clubrankings'||state!==s||v18221ClubRankKey(s)!==key)return;
  const page=document.querySelector('#v555-page');if(!page)return;
  page.innerHTML=html;v551CleanScreen?.(page);v554CleanLegacyCopy?.();v548ApplyFeatureLocks?.(page);v1882EnhanceCountrySelects?.(page);v555ScheduleDecor?.(page);v18221ClubRankStats.swaps++;
 }catch(e){console.warn('[FutBR] troca do snapshot de clubes:',e?.message||e);}
}
function v18230QueueClubRankWarm(s,key,baseKey,attempt=0){
 if(!s||v18221ClubRankPendingKey===key&&attempt===0)return;
 v18221ClubRankPendingKey=key;
 const run=()=>{
  if(state!==s||v18221ClubRankKey(s)!==key){if(v18221ClubRankPendingKey===key)v18221ClubRankPendingKey='';return;}
  if(v18230RankBusy()){
   if(attempt<24){v18221ClubRankStats.retries++;setTimeout(()=>v18230QueueClubRankWarm(s,key,baseKey,attempt+1),Math.min(900,120+attempt*45));}else if(v18221ClubRankPendingKey===key)v18221ClubRankPendingKey='';
   return;
  }
  let html='';
  try{html=v18230ComputeClubRank(s,key,baseKey,true);}catch(error){console.warn('[FutBR] pre-calculo ranking de clubes:',error?.message||error);}
  if(v18221ClubRankCacheable(html)){
   if(v18221ClubRankPendingKey===key)v18221ClubRankPendingKey='';v18230SwapVisibleClubRank(s,key,html);return;
  }
  if(attempt<14){v18221ClubRankStats.retries++;setTimeout(()=>v18230QueueClubRankWarm(s,key,baseKey,attempt+1),Math.min(700,80+attempt*40));}
  else if(v18221ClubRankPendingKey===key)v18221ClubRankPendingKey='';
 };
 try{if(attempt===0&&typeof requestIdleCallback==='function')requestIdleCallback(run,{timeout:900});else setTimeout(run,attempt===0?40:0);}catch(e){setTimeout(run,40);}
}
function v18221InvalidateClubRanking(reason='control'){
 v18221ClubRankRevision++;v18221ClubRankCacheKey='';v18221ClubRankCacheHTML='';v18221ClubRankPendingKey='';v18221ClubRankStats.invalidations++;
}
function v18221ClubRankPage(){
 const s=state,baseKey=v18230ClubRankBaseKey(s),key=v18221ClubRankKey(s);
 v18230ResetForState(s);
 if(v18230ClubRankEntries.has(key))return v18221ClubRankCached(s,key,()=>'',false,baseKey);
 v18230QueueClubRankWarm(s,key,baseKey,0);
 if(v18230ClubRankLastHTML&&v18230ClubRankLastBaseKey!==baseKey){v18221ClubRankStats.staleServed++;return v18230SyncNotice(v18230ClubRankLastHTML);}
 const html=v18230ComputeClubRank(s,key,baseKey,false);
 if(v18221ClubRankCacheable(html))return html;
 return html||v18230ClubRankLastHTML||'<div class="empty">Sincronizando ranking de clubes...</div>';
}
function v18221CanPrewarm(){try{return !!state&&view!=='clubrankings';}catch(e){return false;}}
function v18221ScheduleClubRankPrewarm(){
 if(!v18221CanPrewarm())return;
 const s=state,baseKey=v18230ClubRankBaseKey(s),key=v18221ClubRankKey(s);
 v18230ResetForState(s);
 if(v18230ClubRankEntries.has(key))return;
 v18230QueueClubRankWarm(s,key,baseKey,0);
}
function v18230IsClubRankControl(target){
 const el=target?.closest?.('#v555-page input,#v555-page select,#v555-page button,#v555-page [data-action]');if(!el)return false;
 if(el.matches('input,select'))return true;
 const action=String(el.dataset?.action||'').toLowerCase(),text=String(el.textContent||'').trim().toLowerCase();
 return /rank|filter|page|prev|next/.test(action)||text==='anterior'||text==='proxima'||text==='próxima';
}
document.addEventListener('input',event=>{
 try{if(view!=='clubrankings'||!v18230IsClubRankControl(event.target))return;clearTimeout(v18230ClubRankFilterTimer);v18230ClubRankFilterTimer=setTimeout(()=>v18221InvalidateClubRanking('input'),160);}catch(e){}
},true);
document.addEventListener('change',event=>{try{if(view==='clubrankings'&&v18230IsClubRankControl(event.target))v18221InvalidateClubRanking('change');}catch(e){}},true);
document.addEventListener('click',event=>{try{if(view==='clubrankings'&&v18230IsClubRankControl(event.target)&&!event.target?.closest?.('input,select'))v18221InvalidateClubRanking('click');}catch(e){}},true);
try{
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.clubRankingCache18221={
  version:'18.230',boundedSingleSnapshot:true,boundedSnapshots:V18230_CLUB_RANK_CACHE_MAX,idlePrewarm:true,staleWhileRevalidate:true,retryUntilReady:true,controlAwareInvalidation:true,dayRevisionKey:true,preservesRankingMethodology:true,stats:v18221ClubRankStats,
  invalidate:v18221InvalidateClubRanking,
  probe:(key,factory)=>v18221ClubRankCached('__probe__',String(key),factory,false,String(key)),
  get size(){return v18230ClubRankEntries.size;}
 };
}catch(e){}
/* FUTBR_RANKING_CACHE_18230_END */'''

    html = html[:start] + cache_block + html[end:]

    required = [
        "data-v18230-compact-header=\"1\"",
        "FUTBR_RANKING_CACHE_18230_START",
        "version:'18.230'",
        "boundedSnapshots:V18230_CLUB_RANK_CACHE_MAX",
        "staleWhileRevalidate:true",
        "retryUntilReady:true",
        "controlAwareInvalidation:true",
        "Sincronizando a jornada atual em segundo plano",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador 18.230 ausente: " + marker)
    if "<h3>Ranking de Artilheiros</h3>" in html[html.find("FUTBR_SCORERS_IN_SCOPE_18220_START"):html.find("FUTBR_SCORERS_IN_SCOPE_18220_END")]:
        fail("cabecalho alto de Artilheiros ainda presente")

    report = {
        "ok": True,
        "version": "18.230",
        "scorersCompactHeader": True,
        "clubRankingMethodology": "unchanged-original-renderer",
        "clubRankingBoundedSnapshots": 3,
        "clubRankingIdleRetry": True,
        "clubRankingStaleWhileRevalidate": True,
        "clubRankingControlAwareInvalidation": True,
        "unboundedCache": False,
    }
    (project / "rankings-18230-install.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    index_path.write_text(html, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
