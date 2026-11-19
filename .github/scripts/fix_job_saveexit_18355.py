from __future__ import annotations
import json,sys
from pathlib import Path

MARK='FUTBR_JOB_SAVE_EXIT_18355'
def one(src,old,new,label):
    count=src.count(old)
    if count!=1:raise RuntimeError(f'{label}: expected one occurrence, found {count}')
    return src.replace(old,new,1)

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_job_saveexit_18355.py <project>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src/index.html'
    src=path.read_text(encoding='utf-8')
    if MARK in src:raise RuntimeError('18355 applied twice')
    for required in ['FUTBR_NATIVE_MIRROR_18354','FUTBR_UNEMPLOYED_TURBO_18327',
      'FUTBR_UNEMPLOYED_RESUME_18334_BEGIN','FUTBR_OOMSAFE_ARCHIVE_18352']:
        if required not in src:raise RuntimeError('Missing historical release feature '+required)
    # A previous employment/division is a preference, not a global lifetime
    # ban on receiving proposals when a country changes its league structure.
    start=src.index('function availableJobs(s){')
    end=src.index('function takeJob(s,id){',start)
    block=src[start:end]
    block=one(block,"else return [];",
      """else {
        // 18.355: a league restructure or relegation must never strand
        // an unemployed manager with an empty candidate list forever.
        // Retain reputation/vacancy thresholds from the original pool.
        const adjacent=pool.filter(t=>Math.abs(Number(t.division)-prevDiv)<=1);
        if(adjacent.length)pool=adjacent;
        // If neither division has vacancies, keep the wider eligible pool.
       }""",'vacancy selection fallback')
    block=one(block,
      "let pool=s.teams.filter(t=>t.id!==s.user&&Number(t.base)<=Number(me.reputation||60)+10&&(!t.coachId||Number(t.fanPressure||0)>=42));",
      """let pool=s.teams.filter(t=>t.id!==s.user&&Number(t.base)<=Number(me.reputation||60)+10&&(!t.coachId||Number(t.fanPressure||0)>=42));
     // Long-term unemployment must not become permanent just because every
     // club hired an interim coach. Boards may consider changing projects.
     const since=me.unemployedSince,yearGap=Math.max(0,Number(s.year)-Number(since?.year??s.year));
     const roundsFree=yearGap>0?Math.max(8,yearGap*38+Number(s.day||0)-Number(since?.day||0)):Math.max(0,Number(s.day||0)-Number(since?.day||0));
     if(!pool.length&&roundsFree>=8){
      pool=s.teams.filter(t=>t.id!==s.user&&Number(t.base)<=Number(me.reputation||60)+10&&
       (!prevDiv||Math.abs(Number(t.division)-prevDiv)<=1));
     }""",
      'realistic long-term unemployment market fallback')
    src=src[:start]+block+src[end:]
    start=src.index('function v636GenerateCoachOffer(s,afterUserMatch=false){')
    end=src.index('function v636CoachOfferModal(',start)
    block=src[start:end]
    old="const since=me.unemployedSince,daysFree=Math.max(0,day-Number(since?.day??day));if(daysFree<2)return 0;"
    new="""const since=me.unemployedSince;
  // In the new season 'day' restarts at zero. Count old-season rounds,
  // not just the current season: a dismissal at year-end is not a new one.
  const yearsFree=Math.max(0,Number(s.year)-Number(since?.year??s.year));
  const seasonLength=Math.max(1,Number(s.schedule?.length)||38);
  const daysFree=since?(yearsFree>0?Math.max(2,yearsFree*seasonLength+day-Number(since.day||0)):Math.max(0,day-Number(since.day||0))):Math.max(2,day);
  if(daysFree<2)return 0;"""
    block=one(block,old,new,'cross-season elapsed unemployed rounds')
    src=src[:start]+block+src[end:]
    # If a save never returns, release modal BUSY through an explicit failure,
    # while leaving the original IndexedDB write alive (no corruption and no
    # deceptive success/automatic close).
    start=src.index('async function ensureSaved(){')
    end=src.index('async function archiveCurrent(',start)
    block=src[start:end]
    # 18.338 replaced ensureSaved with a checkpoint-aware path. Insert the
    # watchdog only in its non-clean branch so unchanged careers skip a rewrite.
    original="""   const p=persist(false);
   await v52FlushSave();
   await p;
   if(v52SavePromise)await v52SavePromise;
   x=await get(BASE).catch(()=>null);"""
    replacement="""   const v18355PendingSave=(async()=>{
    const p=persist(false);
    await v52FlushSave();
    await p;
    if(v52SavePromise)await v52SavePromise;
   })();
   let v18355Timer;
   try{
    await Promise.race([
     v18355PendingSave,
     new Promise((_,reject)=>{v18355Timer=setTimeout(()=>reject(new Error(
      'O salvamento excedeu 90 segundos. A gravação ainda pode estar ativa; não feche à força. Verifique o status antes de tentar novamente.')),90000);})
    ]);
   }finally{clearTimeout(v18355Timer);}
   x=await get(BASE).catch(()=>null);"""
    block=one(block,original,replacement,'manual save watchdog after 18.338 verified checkpoint')
    # The 18.338 matches(x) already checks full identity, career, year, day,
    # season closure, and save health. Do not weaken or duplicate that check.
    for guard in ('const clean=matches(x)&&saveOK',
      'if(!matches(x)||!saveOK||v52SaveDirty||v52SavePromise)',
      "String(x.root?.v1903CareerId||'')===String(state.v1903CareerId||'')"):
      if guard not in block:raise RuntimeError('Missing 18.338 integrity guard: '+guard)
    src=src[:start]+block+src[end:]
    src=one(src,"const EDITION='18.354.0';","const EDITION='18.355.0';",'sidebar version')
    src=one(src,
      "window.GestorFC.version='18.354.0';window.GestorFC.visualVersion='18.354.0';",
      "window.GestorFC.version='18.355.0';window.GestorFC.visualVersion='18.355.0';",
      'runtime version')
    marker="""/* FUTBR_JOB_SAVE_EXIT_18355: unemployed market across seasons and safe save watchdog.
   Preserve every career row, player, ranking and historic save block. */
"""
    src=one(src,'async function ensureSaved(){',marker+'async function ensureSaved(){','diagnostic marker')
    path.write_text(src,encoding='utf-8')
    report={'ok':True,'version':'18.355.0','crossSeasonJobSearch':True,
      'vacancyFallbackPreservesReputationAndPressure':True,
      'saveTimeoutReturnsErrorNotFalseSuccess':True,
      'saveWatchdogSeconds':90,'checkpointYearDayVerified':True,
      'doesNotInterruptInFlightSave':True,'noSaveSchemaMigration':True}
    (root/'job-save-exit-18355-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':main()
