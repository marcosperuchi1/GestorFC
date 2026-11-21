"""Publish the completed vacation's existing shards before returning control.

The active Worker owns the authoritative world. Its completed stream already
writes bounded chunks; this patch commits their manifest for every vacation,
including a dismissal or manual pause. No extra world serialization is needed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


MARKER = 'FUTBR_VACATION_DURABLE_CHECKPOINT_18373'


def once(source, before, after, label):
    count = source.count(before)
    if count != 1:
        raise RuntimeError(f'18.373 {label}: expected one anchor, found {count}')
    return source.replace(before, after, 1)


WORKER = r'''
 /* FUTBR_VACATION_DURABLE_CHECKPOINT_18373
    Publish the already-written vacation chunks for every complete return,
    including dismissal and manual pause. The live UI must not have to copy
    its entire world into another Worker merely to save and exit. */
 async function v18373CommitVacationCheckpoint(meta,root,origin){
  if(!origin||meta?.format!=='GFC_VAC_CHECKPOINT_93'||!meta.token||!root||
     !origin.careerId||!origin.coachId||!origin.user||
     String(root.v1903CareerId||'')!==origin.careerId||
     String(root.userCoachId||'')!==origin.coachId||String(root.user||'')!==origin.user||
     String(root.futbrSaveId||'')!==origin.saveId||
     String(root.v640National?.userTeam||'')!==origin.national||
     !!root.userEmployed!==origin.employed||
     Number(root.year)!==origin.year||Number(root.day)!==origin.day||
     Number(meta.year)!==origin.year||Number(meta.day)!==origin.day)
   throw Error('O checkpoint das férias divergiu da carreira atual. O save anterior foi preservado.');
  const old=await read(STORE),same=old?.format===V171_FORMAT&&
   String(old.root?.v1903CareerId||'')===origin.careerId&&
   String(old.root?.userCoachId||'')===origin.coachId&&String(old.root?.user||'')===origin.user&&
   String(old.root?.futbrSaveId||'')===origin.saveId&&
   String(old.root?.v640National?.userTeam||'')===origin.national;
  if(old&&(!same||Number(old.year)>origin.year||
     Number(old.year)===origin.year&&Number(old.day)>origin.day))
   throw Error('O save atual não pertence à mesma carreira ou já está adiante das férias.');
  const collections={},nextRoot={...(same?old.root||{}:{}),...root};
  for(const key of V171_SHARDS){
   const spec=meta.collections?.[key];
   if(spec){
    const count=Number(spec.chunks);
    if(!Number.isInteger(count)||count<0)throw Error('Índice de blocos das férias inválido.');
    collections[key]={isArray:!!spec.isArray,length:Number(spec.length)||0,
     keys:Array.from({length:count},(_,i)=>v93CheckpointKey(meta.token,key,i)),
     ...(spec.encoding?{encoding:spec.encoding}:null),
     ...(spec.nested?{nested:spec.nested}:null)};
    delete nextRoot[key];
   }else if(Object.prototype.hasOwnProperty.call(root,key)){
    // Current history in the streamed root takes precedence over old shards.
    delete collections[key];
   }else if(same&&old.collections?.[key]){
    collections[key]=old.collections[key];delete nextRoot[key];
   }else if(world?.[key]!=null)nextRoot[key]=world[key];
  }
  for(const key of shards)if(!meta.collections?.[key]||!collections[key])
   throw Error('Checkpoint das férias incompleto: '+key+'.');
  const saved={at:Date.now(),year:origin.year,day:origin.day,
   revision:Math.max(Number(old?.revision)||0,diskRevision)+1,format:V171_FORMAT},
   manifest={format:V171_FORMAT,version:1,revision:saved.revision,token:'vacation-'+meta.token,
    at:saved.at,year:saved.year,day:saved.day,root:nextRoot,collections};
  // The manifest and rollback pointer become visible in one existing atomic
  // batch, after all chunks succeeded and before sync-end/finished is sent.
  await v18181RawWriteMany([{key:STORE+':previous',value:old||null},
   {key:STORE,value:manifest},{key:STORE+':meta',value:saved}]);
  diskRevision=saved.revision;checkpoint=null;
  return {...saved,bytes:0,ms:0,storage:'vacation checkpoint manifest',vacation18373:true};
 }
'''


def patch(source):
    if MARKER in source:
        return source
    start = source.index(' /* FUTBR_PROMOTION_DURABLE_CHECKPOINT_18372')
    end = source.index('async function streamVacationWorld125(', start)
    source = source[:start] + WORKER + '\n' + source[end:]
    source = once(source, """ const promotionOrigin18372=!skipCheckpoint&&!world.vacation?.active&&world.vacation?.paused&&
  (world.v636CoachOffers||[]).some(o=>o?.status==='pending'&&Number(o.day)===Number(world.day)&&E.validPromotionOffer18372(world,o))?
  {careerId:String(world.v1903CareerId||''),coachId:String(world.userCoachId||''),user:String(world.user||''),year:Number(world.year),day:Number(world.day)}:null;""",
        """ const vacationOrigin18373=!skipCheckpoint?
  {careerId:String(world.v1903CareerId||''),coachId:String(world.userCoachId||''),
   user:String(world.user||''),saveId:String(world.futbrSaveId||''),
   national:String(world.v640National?.userTeam||''),employed:!!world.userEmployed,
   year:Number(world.year),day:Number(world.day)}:null;""", 'capture complete vacation identity')
    source = once(source,
        "  if(promotionOrigin18372){const saved=await v18372CommitPromotionCheckpoint(checkpointMeta,root,promotionOrigin18372);self.postMessage({kind:'saved',session,...saved});}",
        "  if(vacationOrigin18373){const saved=await v18373CommitVacationCheckpoint(checkpointMeta,root,vacationOrigin18373);self.postMessage({kind:'saved',session,...saved});}",
        'commit every completed vacation before returning control')
    source = once(source,
        " }catch(e){checkpointError(e);if(promotionOrigin18372)self.postMessage({kind:'save-error',session,error:e?.message||String(e)});}",
        " }catch(e){checkpointError(e);if(vacationOrigin18373)self.postMessage({kind:'save-error',session,error:e?.message||String(e)});}",
        'report failed commit without pretending it was saved')
    return source


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: fix_vacation_checkpoint_18373.py <project>')
    root = Path(sys.argv[1])
    path = root / 'src/index.html'
    source = path.read_text(encoding='utf-8')
    out = patch(source)
    path.write_text(out, encoding='utf-8')
    report = {
        'ok': True, 'version': '18.373.0',
        'allVacationReturnsCommitted': True,
        'dismissalAndManualPauseIncluded': True,
        'reusesAlreadyWrittenChunks': True,
        'noSecondWorldSave': True,
        'identityAndDateGuarded': True,
        'previousManifestCommittedAtomically': True,
        'commitBeforeVacationFinished': True,
    }
    (root / 'vacation-checkpoint-18373-install.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
