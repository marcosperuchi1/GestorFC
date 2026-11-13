from pathlib import Path
import json, sys

VERSION='18.316'
MARK='FUTBR_RANK_ROLLOVER_18316'

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: fix_rank_rollover_18316.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); path=root/'src'/'index.html'
    html=path.read_text(encoding='utf-8')
    if MARK in html:
        print('18.316 already applied'); return
    patch=r'''
<script id="gfc-v18316-rank-rollover-carry">
/* FUTBR_RANK_ROLLOVER_18316 */
(()=>{
 'use strict';
 window.GestorFC=window.GestorFC||{};const G=window.GestorFC;
 const stats={carryHits:0,snapshotFallbackHits:0,promotions:0,failedPromotions:0,captures:0};
 function cloneRows(rows){return (rows||[]).slice(0,V86_RANK_LIMIT).map(r=>({...r,titles:Array.isArray(r?.titles)?r.titles.map(t=>({...t})):[]}));}
 function cloneRecords(records,rows){const out={};for(const r of rows||[]){const x=records?.[r.id];out[r.id]={games:Number(x?.games)||0,wins:Number(x?.wins)||0,draws:Number(x?.draws)||0,losses:Number(x?.losses)||0};}return out;}
 function currentSeasonAlreadyPlayed(s){
  if(!s)return false;
  if((s.teams||[]).some(t=>(Number(t?.stats?.p)||0)>0))return true;
  const lim=Math.min((s.schedule||[]).length,Math.max(0,Number(s.day)||0));
  for(let i=0;i<lim;i++)for(const f of s.schedule?.[i]?.fixtures||[])if(f?.result)return true;
  return false;
 }
 function syntheticCarry(s){
  const year=Number(s?.year)||0,snap=s?.v18312ClubRankSnapshot;
  if(!snap||Number(snap.year)!==year-1||!Array.isArray(snap.rows)||!snap.rows.length)return null;
  const rows=cloneRows(snap.rows),records=cloneRecords(snap.records||{},rows);
  return {version:1,careerId:String(s?.v1903CareerId||''),oldYear:year-1,year,stamp:v86Stamp(s),oldTitleRevision:Number(snap.titleRevision)||0,rows,records,hasExpiringHistory:false,v18316Synthetic:true};
 }
 function validCarry(s,carry){return !!(s&&carry&&Number(carry.year)===Number(s.year)&&Array.isArray(carry.rows)&&carry.rows.length);}
 function promote(s=state){
  if(!s)return false;const year=Number(s.year)||0,c=v86RankCache;
  if(c?.ready&&!c.building&&Number(c.year)===year&&Array.isArray(c.rows)&&c.rows.length)return false;
  // Once the new season has real club results, never replace live data with the previous-season base.
  if(currentSeasonAlreadyPlayed(s))return false;
  let carry=validCarry(s,s.v18111RankCarry)?s.v18111RankCarry:null,source='v18111-carry';
  if(carry)stats.carryHits++;else{carry=syntheticCarry(s);source='v18312-previous-snapshot';if(carry)stats.snapshotFallbackHits++;}
  if(!carry)return false;
  try{
   carry.stamp=v86Stamp(s);
   const target=(c&&Number(c.year)!==year)?c:null;
   if(!v18111RebaseCache(s,carry,target))throw new Error('v18111RebaseCache recusou o handoff');
   const nc=v86RankCache;
   nc.v18312Source='season-carry-18.316:'+source;
   nc.v18316CarriedFrom=Number(carry.oldYear)||year-1;
   nc.v18316CarrySource=source;
   nc.v18316CarryReady=true;
   // Titles are a separate sparse layer and must be reconciled against the new season window.
   nc.v18315TitlesReady=false;nc.v18315AppliedRowsRef=null;nc.v18315TitleStamp='';nc.v18315TitleIds=null;
   nc.dirty=false;nc.ready=true;nc.building=false;nc.progress=100;nc.refreshing=false;
   s.v18111RankCarry=carry;
   stats.promotions++;
   return true;
  }catch(e){stats.failedPromotions++;console.warn('[18.316] handoff de ranking',e);return false;}
 }
 const baseEnsure=v86EnsureBuild;
 v86EnsureBuild=function(...args){
  try{promote(state);}catch(e){console.warn('[18.316] pre-ensure',e);}
  const c=baseEnsure(...args);
  try{
   if(c&&Number(c.year)===Number(state?.year)&&c.ready&&!c.building){
    G.v18315?.ensure?.();
    if(c.v18316CarryReady){G.v18312?.capture?.();stats.captures++;c.v18316CarryReady=false;}
   }
  }catch(e){if(c)c.error=String(e?.message||e);console.warn('[18.316] pos-ensure',e);}
  return c;
 };
 // The background warm-up must never discard a valid previous-season carry and start at 0%.
 const baseRunWarm=typeof v127RunRankWarm==='function'?v127RunRankWarm:null;
 if(baseRunWarm)v127RunRankWarm=function(expectedKey){try{promote(state);}catch(e){}return baseRunWarm(expectedKey);};
 // If a later cleanup nulled only the UI cache, the next render restores the retained season snapshot instantly.
 function ensure(){try{promote(state);return v86EnsureBuild(false);}catch(e){console.warn('[18.316] ensure',e);return v86RankCache;}}
 G.v18316={version:'18.316',architecture:'cross-season-ready-top1000-carry',noSeasonRebuild:true,preserveRecords:true,preserveCoefficients:true,previousSnapshotFallback:true,sparseTitlesAfterCarry:true,stats,ensure,status:()=>({year:Number(state?.year)||0,cacheYear:Number(v86RankCache?.year)||0,ready:!!v86RankCache?.ready,building:!!v86RankCache?.building,progress:Number(v86RankCache?.progress)||0,source:v86RankCache?.v18316CarrySource||v86RankCache?.v18312Source||'',carriedFrom:v86RankCache?.v18316CarriedFrom||null,rows:v86RankCache?.rows?.length||0,records:Object.keys(v86RankCache?.records||{}).length})};
})();
</script>
'''
    html += patch
    path.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,'noSeasonRebuild':True,'preserveRecords':True,'previousSnapshotFallback':True,'titlesSparseAfterCarry':True}
    (root/'rank-rollover-18316-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__': main()
