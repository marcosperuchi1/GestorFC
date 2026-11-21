"""Execute the shipped Worker stream, codecs, manifest reader and finalizer.

Storage transactions and sporting inputs are isolated fixtures. The separate
browser gate runs the full Engine and measures the real 2029 memory footprint.
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def between(source, start, end):
    a = source.index(start)
    return source[a:source.index(end, a)]


def function(source, name):
    match = re.search(r'(?:async\s+)?function\s*(?:\*\s*)?' + re.escape(name) + r'\s*\(', source)
    if not match:
        raise RuntimeError('Missing original function: ' + name)
    start = source.index('{', match.end())
    depth = 0
    quote = comment = None
    escaped = False
    index = start
    while index < len(source):
        char, pair = source[index], source[index:index + 2]
        if comment == 'line':
            if char == '\n':
                comment = None
        elif comment == 'block':
            if pair == '*/':
                comment = None
                index += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
        elif pair == '//':
            comment = 'line'
            index += 1
        elif pair == '/*':
            comment = 'block'
            index += 1
        elif char in "'\"`":
            quote = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return source[match.start():index + 1]
        index += 1
    raise RuntimeError('Unbalanced original function: ' + name)


PRELUDE = r'''
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const STORE='isolated-vacation-checkpoint-18373',V93_VAC_PREFIX=STORE+':v93vac:',V93_VAC_META=V93_VAC_PREFIX+'meta';
const shards=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats'];
const safe=k=>!['__proto__','prototype','constructor'].includes(k);
let world=null,diskRevision=0,checkpoint=null,baseline=null,session=1,v18117SyncSeq=0,v18117SyncAck=0;
let running=false,visible=false,delay=0,pause=null,revision=0,v150ManualSavePromise=null;
let v126TeamSig=null,v126RosterSig=null,v126CoachSig=null,v126CompSig=null,v126AllSig=null,
 v126CompetitionSig=null,v126LiveYear=null,v128LiveSeq=0,v128LiveAck=0,v131TeamIndex=null,
 v131TransferCursor=0,v131CoachMoveCursor=0,v131LiveCounter=0;
const v18310SyncWaiters=new Map();
let disk=new Map(),writes=[],events=[],failManifest=false,failChunk=false,mode='ordinary',
 extraSaveCalls=0,extraEncodeCalls=0,decodedPlayerRows=0,roundCalls=0;
const read=async key=>structuredClone(disk.get(key));
async function v18181RawWriteMany(entries){
 const copy=structuredClone(entries);
 if(failManifest&&copy.some(e=>e.key===STORE))throw Error('injected atomic manifest failure');
 if(failChunk&&copy.some(e=>e.key.includes(':players:')))throw Error('injected player chunk failure');
 // Map replacement models an atomic storage transaction, not the product save algorithm.
 const next=new Map(disk);for(const entry of copy)next.set(entry.key,entry.value);disk=next;
 writes.push(copy.map(e=>e.key));events.push({kind:'storage-commit',keys:copy.map(e=>e.key)});
}
const v93RawWrite=(key,value)=>v18181RawWriteMany([{key,value}]);
const v93CheckpointKey=(token,key,index)=>V93_VAC_PREFIX+token+':'+key+':'+index;
const self={postMessage(message,transfer=[]){
 const received=structuredClone(message,{transfer});
 if(received.kind==='vac-sync-part'&&received.key==='players')
  for(const row of v18310VacationRows(received)){assert(row[1]?.id);decodedPlayerRows++;}
 // Retain only event scalars, never a complete transport world in test diagnostics.
 events.push({kind:received.kind,checkpoint:received.checkpoint,error:received.error,
  day:received.day,year:received.year,keys:received.keys});
 if(received.syncSeq)queueMicrotask(()=>v18310ResolveSyncAck(received.syncSeq));
}};
const E={
 team:(s,id)=>s.teams.find(t=>t.id===id),
 applyPromotionOfferEnvelope18372(){},applyManagerSettings18371(){},boardRenewals18371(){},
 validPromotionOffer18372(){return false;},syncEligibility(){},
 async vacationStepAsync(s){
  roundCalls++;s.day++;s.vacation.completed++;s.vacation.remaining--;
  if(mode==='manual-pause')pause='pause';
  else if(mode==='dismissal'){s.userEmployed=false;s.coaches[s.userCoachId].clubId=null;}
  else if(mode==='season-end'){s.seasonDone=true;s.vacation.active=false;s.vacation.paused=true;}
  else{s.vacation.active=false;s.vacation.paused=true;}
 }
};
const National={before:s=>({userPending:mode==='national'}),after(){}};
function v126InitLive(){}
async function v126PublishVacationLive(){}
function progress(){}
async function save(){extraSaveCalls++;throw Error('Unexpected second full-world save');}
async function encode(){extraEncodeCalls++;throw Error('Unexpected full-world encoding');}
const digest=value=>crypto.createHash('sha256').update(JSON.stringify(value,(key,row)=>
 row&&typeof row==='object'&&!Array.isArray(row)?
  Object.fromEntries(Object.keys(row).sort().map(k=>[k,row[k]])):row)).digest('hex');
function makeWorld(kind='ordinary'){
 const players={};
 for(let i=0;i<3077;i++)players['p'+i]={id:'p'+i,name:'Atleta '+i,age:18+i%20,natCode:'BRA',
  clubId:i<4?'t0':'t1',contract:1+i%4,goals:i%20,assists:i%9,apps:30,
  skills:{attack:50+i%40,defense:35+i%50},custom:{nil:null,no:false,zero:0,nested:[2026,2027,2028]},
  honors538:[{year:2028,competition:'league',type:'champion'}],totalGoals:40+i};
 return {year:2029,day:32,seasonDone:false,v1903CareerId:'career-2029',userCoachId:'me',
  user:'t0',futbrSaveId:'slot-existing',userEmployed:true,players,
  teams:[{id:'t0',balance:10000000,roster:['p0','p1'],academy:['p2'],proReserve:['p3']},
   {id:'t1',balance:5000000,roster:['p4','p5']}],
  coaches:{me:{id:'me',clubId:'t0',history:[{year:2026,club:'t2'}]}},
  schedule:[{type:'league',fixtures:[{home:'t0',away:'t1',result:{home:2,away:1}}]}],
  competitions:{league:{year:2029}},competitionStats:{'league:BRA:1':{p0:{goals:2,assists:1,apps:1}}},
  allTimeStats:{p0:{goals:144,assists:88}},v622Settings:{renewals:'board'},
  v636CoachOffers:[],v636CoachOfferMeta:{rejected:{}},news:[],
  vacation:{active:true,paused:false,completed:4,remaining:24,untilSeason:kind==='season-end'},
  v640National:kind==='national'?{userTeam:'BRA',teams:{BRA:{id:'BRA'}}}:null,
  history:[{year:2028,kind:'fresh-root-history',champion:'t0'}],
  transfers:[{id:'fresh-transfer',year:2029}],retirements:[{id:'retired',year:2028}],
  internationalHistory:[{year:2028,champion:'BRA'}],
  v735NationalArchive:{2028:{BRA:{champion:true}}},
  v538CareerArchive:{2026:{p0:[{games:30,goals:12}]},2028:{p0:[{games:34,goals:19}]}},
  v555CareerArchive:{2026:{n:['Atleta 0'],p:{p0:'2026;30;12'}},2028:{n:['Atleta 0'],p:{p0:'2028;34;19'}}},
  scorerArchive:[{year:2028,competitions:{'league:BRA:1':{p0:{goals:19,assists:8}}}}],
  crestOverrides:{t0:'crest-kept'}};
}
function setup(kind='ordinary',oldYear=2029,hasOld=true){
 disk=new Map();writes=[];events=[];failManifest=false;failChunk=false;mode=kind;
 world=makeWorld(kind);diskRevision=7;checkpoint=null;baseline=null;running=false;
 v150ManualSavePromise=null;v18117SyncSeq=0;v18117SyncAck=0;
 extraSaveCalls=extraEncodeCalls=decodedPlayerRows=roundCalls=0;
 const root={year:oldYear,day:oldYear===world.year?world.day:95,v1903CareerId:world.v1903CareerId,
  userCoachId:world.userCoachId,user:world.user,userEmployed:true,futbrSaveId:world.futbrSaveId,
  v640National:structuredClone(world.v640National),v622Settings:{renewals:'board'}};
 const old={format:'GFC_SHARDED_171',version:1,token:'old-durable',revision:7,
  year:root.year,day:root.day,root,collections:{
   v538CareerArchive:{isArray:false,nested:'year-id-v1',keys:['old-538']},
   v555CareerArchive:{isArray:false,nested:'year-id-v1',keys:['old-555']},
   scorerArchive:{isArray:true,length:1,keys:['old-scorer']},
   history:{isArray:true,length:1,keys:['old-history']},
   transfers:{isArray:true,length:1,keys:['old-transfers']},
   v735NationalArchive:{isArray:false,keys:['old-national']}}};
 for(const key of shards){
  const value=world[key],isArray=Array.isArray(value);
  old.collections[key]={isArray,length:isArray?value.length:0,keys:['old-'+key]};
  disk.set('old-'+key,Object.entries(value).map(([id,row])=>[id,structuredClone(row)]));
 }
 const old538=oldYear===world.year?world.v538CareerArchive:{2026:world.v538CareerArchive[2026]};
 const old555=oldYear===world.year?world.v555CareerArchive:{2026:world.v555CareerArchive[2026]};
 disk.set('old-538',Object.entries(old538).flatMap(([year,rows])=>Object.entries(rows).map(([id,value])=>[year,id,structuredClone(value)])));
 disk.set('old-555',Object.entries(old555).flatMap(([year,rows])=>Object.entries(rows).map(([id,value])=>[year,id,structuredClone(value)])));
 disk.set('old-scorer',[[0,structuredClone(oldYear===world.year?world.scorerArchive[0]:{year:2026,competitions:{}})]]);
 disk.set('old-history',[[0,{year:2026,kind:'stale-history'}]]);
 disk.set('old-transfers',[[0,{id:'stale-transfer'}]]);
 disk.set('old-national',[['2026',{BRA:{champion:false}}]]);
 if(hasOld)disk.set(STORE,structuredClone(old));
 disk.set(STORE+':previous',{format:'old-rollback-sentinel',token:'preserve-me'});
 return {old:hasOld?old:null,previous:structuredClone(disk.get(STORE+':previous')),
  expected:{playerDigest:digest(world.players),players:Object.keys(world.players).length,
   v538CareerArchive:structuredClone(world.v538CareerArchive),v555CareerArchive:structuredClone(world.v555CareerArchive),
   scorerArchive:structuredClone(world.scorerArchive),history:structuredClone(world.history),
   transfers:structuredClone(world.transfers),v735NationalArchive:structuredClone(world.v735NationalArchive)}};
}
async function runSimulation(){
 await simulate({mode:'vacation',session:21,visible:false,delay:1,state:world,
  v1903CareerId:world.v1903CareerId,v1903User:world.user,v1903National:!!world.v640National?.userTeam});
}
function assertOrdering(){
 const committed=events.findIndex(e=>e.kind==='storage-commit'&&e.keys?.includes(STORE)),
  saved=events.findIndex(e=>e.kind==='saved'),end=events.findIndex(e=>e.kind==='vac-sync-end'),
  finished=events.findIndex(e=>e.kind==='finished');
 assert(committed>=0&&committed<saved&&saved<end&&end<finished,
  'actual simulate must commit, acknowledge saved, finish stream, then send finished');
 assert.equal(events[finished].error,null);
 assert.equal(events[end].checkpoint,true);
}
'''


TESTS = r'''
(async()=>{
 const result={ok:true,version:'18.373.0',fixture:'isolated 2029 storage and transport; full Engine/browser tested separately',scenarios:[]};
 if(BASELINE){
  const {old}=setup('manual-pause');await runSimulation();
  const finished=events.find(e=>e.kind==='finished');
  assert.equal(finished.error,null,'baseline must complete normally, not fail from a missing harness dependency');
  assert.equal(finished.day,33);assert.equal(decodedPlayerRows,3077);
  assert(events.some(e=>e.kind==='vac-sync-end'&&e.checkpoint===true));
  assert(!events.some(e=>e.kind==='vac-checkpoint-error'||e.kind==='save-error'));
  assert.deepEqual(await read(STORE),old);
  assert(!events.some(e=>e.kind==='saved'));
  console.log(JSON.stringify({...result,baselineFailureReproduced:true,returnedDay:finished.day,
   persistedDay:(await read(STORE)).day,noOrdinaryVacationManifestCommit:true}));return;
 }
 for(const kind of ['manual-pause','dismissal','national','ordinary','season-end']){
  const {old,expected}=setup(kind);await runSimulation();
  const manifest=await read(STORE),loaded=await decode(manifest),meta=await read(V93_VAC_META);
  assert.equal(loaded.year,2029);assert.equal(loaded.day,kind==='national'?32:33,
   kind+' final checkpoint events: '+JSON.stringify(events.slice(-10)));
  assert.equal(loaded.v1903CareerId,'career-2029');assert.equal(loaded.userCoachId,'me');
  assert.equal(loaded.user,'t0');assert.equal(loaded.futbrSaveId,'slot-existing');
  assert.equal(loaded.userEmployed,kind!=='dismissal');
  assert.equal(loaded.v640National?.userTeam||'',kind==='national'?'BRA':'');
  assert.equal(loaded.v622Settings.renewals,'board');assert.deepEqual(loaded.v636CoachOffers,[]);
  assert.equal(loaded.vacation.active,false);assert.equal(loaded.vacation.paused,true);
  assert.equal(loaded.seasonDone,kind==='season-end');
  assert.equal(digest(loaded.players),expected.playerDigest);assert.equal(decodedPlayerRows,expected.players);
  assert.deepEqual(loaded.v538CareerArchive,expected.v538CareerArchive);
  assert.deepEqual(loaded.v555CareerArchive,expected.v555CareerArchive);
  assert.deepEqual(loaded.scorerArchive,expected.scorerArchive);
  assert.deepEqual(loaded.history,expected.history);assert.deepEqual(loaded.transfers,expected.transfers);
  assert.deepEqual(loaded.v735NationalArchive,expected.v735NationalArchive);
  assert(!manifest.collections.history&&!manifest.collections.transfers&&!manifest.collections.v735NationalArchive);
  assert.deepEqual(manifest.collections.players.keys,Array.from({length:meta.collections.players.chunks},(_,i)=>v93CheckpointKey(meta.token,'players',i)));
  assert.equal(manifest.collections.players.encoding,v18191wPlayerFormat);
  assert(meta.collections.players.chunks>=5);
  assert(writes.filter(batch=>batch.some(k=>k.includes(':players:'))).every(batch=>batch.length<=4));
  assert.deepEqual(await read(STORE+':previous'),old);
  assert.deepEqual(writes.find(batch=>batch.includes(STORE)),[STORE+':previous',STORE,STORE+':meta']);
  assert.equal(extraSaveCalls,0);assert.equal(extraEncodeCalls,0);assert.equal(world,null);
  assert.equal(v18310SyncWaiters.size,0);assertOrdering();
  if(kind==='dismissal')assert(events.some(e=>e.kind==='vac-dismissed'));
  result.scenarios.push({kind,year:loaded.year,day:loaded.day,players:expected.players,
   playerChunks:meta.collections.players.chunks,roundCalls,manifestRevision:manifest.revision});
 }
 Object.assign(result,{originalStreamAndReaderExecuted:true,originalSimulationFinalizerExecuted:true,
  manualPauseWithoutPromotionSaved:true,dismissalWithoutPromotionSaved:true,nationalVacationSaved:true,
  ordinaryAndSeasonEndSaved:true,checkpointPlayerChunksReused:true,bounded2029ChunkTransactions:true,
  fullPlayerFieldsPreserved:true,freshRootHistoryWins:true,previousManifestPreserved:true,
  noAdditionalWorldSave:true,commitBeforeSyncEndAndFinished:true});
 // A prior-year manifest must not erase archives produced by the live rollover.
 for(const hasOld of [true,false]){
  const {expected}=setup('manual-pause',2028,hasOld);await runSimulation();
  const loaded=await decode(await read(STORE));
  assert.deepEqual(loaded.v538CareerArchive,expected.v538CareerArchive,'new 2028 player archive must be committed');
  assert.deepEqual(loaded.v555CareerArchive,expected.v555CareerArchive,'new 2028 packed archive must be committed');
  assert.deepEqual(loaded.scorerArchive,expected.scorerArchive,'new 2028 scorer archive must be committed');
  assertOrdering();assert.equal(extraSaveCalls,0);assert.equal(extraEncodeCalls,0);
 }
 result.rolloverArchivesFromCurrentWorld=true;result.initialArchivesWithoutManifestPreserved=true;
 // Failure must retain both committed generations and report an unsaved return.
 for(const kind of ['manifest','chunk']){
  const {old,previous}=setup('manual-pause');failManifest=kind==='manifest';failChunk=kind==='chunk';
  await runSimulation();
  assert.deepEqual(await read(STORE),old);assert.deepEqual(await read(STORE+':previous'),previous);
  assert(!events.some(e=>e.kind==='saved'));
  assert(events.some(e=>e.kind==='vac-sync-end'&&e.checkpoint===false));
  assert(events.some(e=>e.kind==='vac-checkpoint-error'));
  if(kind==='manifest')assert(events.some(e=>e.kind==='save-error'));
  assert.equal(decodedPlayerRows,3077,'failed storage must still return the complete world');
 }
 result.atomicFailurePreservesSave=true;result.partialChunkFailurePreservesSave=true;
 result.failedCommitNeverClaimsSaved=true;
 // Validate the actual commit helper against altered current manifest/root/meta.
 setup('manual-pause');await runSimulation();
 const goodMeta=await read(V93_VAC_META),goodRoot=await read(goodMeta.rootKey),goodOld=await read(STORE+':previous');
 const origin={careerId:goodRoot.v1903CareerId,coachId:goodRoot.userCoachId,user:goodRoot.user,
  saveId:goodRoot.futbrSaveId,national:goodRoot.v640National?.userTeam||'',employed:!!goodRoot.userEmployed,
  year:goodRoot.year,day:goodRoot.day};
 const guards=[
  ['current career',x=>x.old.root.v1903CareerId='other'],['current coach',x=>x.old.root.userCoachId='other'],
  ['current club',x=>x.old.root.user='other'],['current saveId',x=>x.old.root.futbrSaveId='other'],
  ['current national',x=>x.old.root.v640National={userTeam:'ARG'}],
  ['newer day',x=>x.old.day=origin.day+1],['newer year',x=>x.old.year=2030],
  ['root career',x=>x.root.v1903CareerId='other'],['root coach',x=>x.root.userCoachId='other'],
  ['root club',x=>x.root.user='other'],['root saveId',x=>x.root.futbrSaveId='other'],
  ['root national',x=>x.root.v640National={userTeam:'ARG'}],['root employed',x=>x.root.userEmployed=false],
  ['root year',x=>x.root.year=2030],['root day',x=>x.root.day++],
  ['meta year',x=>x.meta.year=2030],['meta day',x=>x.meta.day++],
  ['missing collection',x=>delete x.meta.collections.players],['invalid chunk count',x=>x.meta.collections.players.chunks=-1]
 ];
 for(const [label,alter] of guards){
  const x={meta:structuredClone(goodMeta),root:structuredClone(goodRoot),old:structuredClone(goodOld)};alter(x);
  disk.set(STORE,x.old);const before=digest(await read(STORE)),previous=digest(await read(STORE+':previous'));
  await assert.rejects(()=>v18373CommitVacationCheckpoint(x.meta,x.root,origin),undefined,label);
  assert.equal(digest(await read(STORE)),before,label);assert.equal(digest(await read(STORE+':previous')),previous,label);
 }
 result.identitySaveIdAndDateGuards=true;result.identityGuardCases=guards.length;
 const {old}=setup('ordinary');await streamVacationWorld125(false,true);
 assert.deepEqual(await read(STORE),old);assert(!events.some(e=>e.kind==='saved'));
 assert(!writes.some(batch=>batch.includes(STORE)));assert.equal(Object.keys(world.players).length,3077);
 result.transportOnlyDoesNotPublish=true;
 console.log(JSON.stringify(result));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
'''


def main():
    if len(sys.argv) not in (2, 3) or len(sys.argv) == 3 and sys.argv[2] != '--baseline':
        raise SystemExit('usage: test_vacation_checkpoint_18373.py <project> [--baseline]')
    project = Path(sys.argv[1])
    source = (project / 'src/index.html').read_text(encoding='utf-8')
    baseline = len(sys.argv) == 3
    name = 'vacation-checkpoint-18373-baseline.json' if baseline else 'vacation-checkpoint-18373-tests.json'
    report_path = project / name
    source_sha = hashlib.sha256(source.encode('utf-8')).hexdigest()
    report_path.write_text(json.dumps({'ok': False, 'version': '18.373.0',
        'sourceSha256': source_sha, 'error': 'Regression has not completed'}), encoding='utf-8')
    if not baseline:
        assert 'FUTBR_VACATION_DURABLE_CHECKPOINT_18373' in source
    # Every function below is copied verbatim from the built game source.
    sections = [
        between(source, 'const v18191wPlayerFields=', ' const V171_FORMAT='),
        between(source, 'const v18191uPlayerFields=', 'function v18191uPackPlayer('),
        function(source, 'v18191uPackPlayer'),
        function(source, 'v18191uUnpackPlayer'),
        function(source, 'v18191uArrayBufferToBase64'),
        between(source, ' const V171_FORMAT=', ' const v171ShardKey='),
        function(source, 'v18352ApplyArchivedRow'),
    ]
    for name in ('v18373PackedArchiveRows', 'v18373StructuredArchiveRows', 'v18373ApplyArchivePath',
                 'v18343Fingerprint', 'v18373WriteHistoryCollection', 'v18373WriteCheckpointHistories',
                 'v18373ReleaseWorkerGraph'):
        if re.search(r'function\s*\*?\s*' + name + r'\s*\(', source):
            sections.append(function(source, name))
    owner_declaration = 'let v18373JobWaitWorker=false,v18373JobWaitToken=null;'
    if owner_declaration in source:
        sections.append(owner_declaration)
    sections += [
        between(source, ' async function v171DecodeManifest(x){', ' \n/* FUTBR_ARCHIVE_COPY_ON_WRITE_18343'),
        function(source, 'v18310PackVacationRows'),
        function(source, 'v18310VacationRows'),
        function(source, 'v18310ResolveSyncAck'),
        function(source, 'v18117WaitSyncAck'),
        function(source, 'v18372CommitPromotionCheckpoint' if baseline else 'v18373CommitVacationCheckpoint'),
        function(source, 'streamVacationWorld125'),
        function(source, 'applyPause'),
        function(source, 'simulate'),
    ]
    program = PRELUDE + '\n' + '\n'.join(sections) + '\nconst BASELINE=' + str(baseline).lower() + ';\n' + TESTS
    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / 'vacation-checkpoint-real-functions.cjs'
        script.write_text(program, encoding='utf-8')
        check = subprocess.run(['node', '--check', str(script)], capture_output=True, text=True, timeout=20)
        if check.returncode:
            raise RuntimeError('Extracted original-source syntax failed:\n' + check.stderr[-6000:])
        run = subprocess.run(['node', '--max-old-space-size=512', str(script)], capture_output=True, text=True, timeout=120)
        if run.returncode:
            error = 'Original Worker checkpoint regression failed:\n' + run.stderr[-9000:] + '\n' + run.stdout[-3000:]
            report_path.write_text(json.dumps({'ok': False, 'version': '18.373.0',
                'sourceSha256': source_sha, 'error': error}), encoding='utf-8')
            raise RuntimeError(error)
        result = json.loads(run.stdout.strip().splitlines()[-1])
    result['sourceSha256'] = source_sha
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
