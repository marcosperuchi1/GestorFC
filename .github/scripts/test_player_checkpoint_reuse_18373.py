"""Prove player reuse through actual UI, vacation and ordinary Worker writers.

Reuse the isolated storage/transport harness from the vacation boot gate. No
production save or browser profile is opened, and no whole-world test hook is
added to the shipped HTML.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from test_vacation_memory_boot_18373 import NODE as BOOT_NODE, between
from fix_player_checkpoint_reuse_18373 import legacy_unpacker


SHAPES = r'''
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
function fast(object){return %HasFastProperties(object);}
function makeApi(row){
 const prefix=row.prefix,api=new Function(row.source+`\nreturn {
  fields:${prefix}PlayerFields,unpack:${prefix}UnpackPlayer,pack:${prefix}PackPlayer,
  encode:${prefix}EncodePlayerChunk,decode:${prefix}DecodePlayerChunk,format:${prefix}PlayerFormat};`)();
 api.legacy=new Function('fields',`const ${prefix}PlayerFields=fields;\n`+row.legacy+`\nreturn ${prefix}UnpackPlayer;`)(api.fields);
 return api;
}
function densePlayer(fields){
 const player={id:'dense',name:'Zé 漢字 🏆\0',pos:'MEI',skills:{pace:70,pass:65},fitness:97,apps:22,
  goals:8,assists:3,age:25,clubId:'t1',unknownString:'kept',unknownObject:{values:[0,false,null]},unknownNull:null};
 for(let i=0;i<fields.length;i++)if(!Object.hasOwn(player,fields[i]))player[fields[i]]=i+1;
 return player;
}
(async()=>{
 const results=[];
 for(const row of input){
  const api=makeApi(row),dense=densePlayer(api.fields),packed=api.pack(dense,'dense');
  const legacy=api.legacy(packed),decoded=api.unpack(packed);
  assert.deepEqual(decoded,legacy);assert.deepEqual(Reflect.ownKeys(decoded),Reflect.ownKeys(legacy));
  assert.equal(fast(legacy),false,row.prefix+': legacy dynamic assignments must reproduce dictionary backing');
  assert.equal(fast(decoded),true,row.prefix+': actual shipped decoder must create a fast player object');
  // Do not invent absent fields. Existing statistics updates retain the
  // shape; adding new fields later is explicitly outside this guarantee.
  decoded.fitness=83;decoded.apps++;decoded.goals+=2;decoded.skills.pace++;
  assert.equal(fast(decoded),true);assert.equal(decoded.fitness,83);assert.equal(decoded.apps,23);

  const sparse={id:'sparse',name:'',fitness:undefined,listed:false,injury:0,contract:null},sparseRow=api.pack(sparse,91),
   sparseDecoded=api.unpack(sparseRow),sparseLegacy=api.legacy(sparseRow);
  assert.deepEqual(sparseDecoded,sparseLegacy);
  assert.equal(sparseDecoded.id,'91');assert.equal(Object.hasOwn(sparseDecoded,'fitness'),true);
  assert.equal(sparseDecoded.fitness,undefined);assert.equal(sparseDecoded.listed,false);
  assert.equal(sparseDecoded.injury,0);assert.equal(sparseDecoded.contract,null);
  assert.equal(Object.hasOwn(sparseDecoded,'pos'),false);
  const symbol=Symbol('legacy-extra'),extra={id:42,name:'Extra override',unknown:'保留',constructor:'data',prototype:'own'};
  extra[symbol]='symbol value';let reads=0;
  Object.defineProperty(extra,'getter',{enumerable:true,get(){reads++;return 'getter value';}});
  Object.defineProperty(extra,'hidden',{enumerable:false,value:'not copied'});
  const withExtra=[...sparseRow.slice(0,4),extra],withLegacy=api.legacy(withExtra),withDecoded=api.unpack(withExtra);
  assert.equal(reads,2);assert.deepEqual(withDecoded,withLegacy);
  assert.deepEqual(Reflect.ownKeys(withDecoded),Reflect.ownKeys(withLegacy));assert.equal(withDecoded.id,42);
  assert.equal(withDecoded[symbol],'symbol value');assert.equal(Object.hasOwn(withDecoded,'hidden'),false);
  for(const key of Reflect.ownKeys(withDecoded)){
   const descriptor=Object.getOwnPropertyDescriptor(withDecoded,key);
   assert.equal(descriptor.enumerable,true);assert.equal(descriptor.writable,true);assert.equal(descriptor.configurable,true);
  }
  const prototypeValue={injected:'literal-data'},prototypeExtra=JSON.parse('{"__proto__":{"injected":"literal-data"},"constructor":"literal"}'),
   safe=api.unpack([...sparseRow.slice(0,4),prototypeExtra]);
  assert.equal(Object.getPrototypeOf(safe),Object.prototype);assert.equal(Object.hasOwn(safe,'__proto__'),true);
  assert.deepEqual(safe.__proto__,prototypeValue);assert.equal(safe.constructor,'literal');
  assert.equal(Object.prototype.injected,undefined);

  // Decode both historical storage encodings with each real w/u/m codec.
  const transportRow=api.pack(densePlayer(api.fields),'legacy-packed'),
   expected=api.legacy(JSON.parse(JSON.stringify(transportRow))),
   json={format:api.format,encoding:'json',data:JSON.stringify([transportRow]),count:1},
   fromJson=(await api.decode(json))[0][1],gzip=await api.encode([['legacy-packed',densePlayer(api.fields)]]),
   fromGzip=(await api.decode(gzip))[0][1];
  assert.deepEqual(fromJson,expected);assert.deepEqual(fromGzip,expected);
  assert.equal(fast(fromJson),true);assert.equal(fast(fromGzip),true);

  const count=12000,cohort=new Array(count);let newFast=0,oldFast=0;
  for(let i=0;i<count;i++){
   const current=api.unpack(packed);current.fitness=80+i%20;current.apps=i;cohort[i]=current;
   if(fast(current))newFast++;if(fast(api.legacy(packed)))oldFast++;
  }
  assert.equal(newFast,count);assert.equal(oldFast,0);
  assert.equal(cohort[count-1].apps,count-1);assert.equal(cohort[0].unknownString,'kept');
  results.push({decoder:row.prefix,knownFields:api.fields.length,ownPlayerFields:Object.keys(decoded).length,
   cohortPlayers:count,fastAfterDecodeAndExistingUpdates:newFast,legacyFast:oldFast});
 }
 console.log(JSON.stringify({actualThreeUnpackersUseFastProperties:true,densePlayerCohortUsesFastProperties:true,
  existingPlayerUpdatesKeepFastProperties:true,sparsePackedPresencePreserved:true,
  extraOverridesAndSymbolsPreserved:true,prototypeKeysDecodedAsSafeOwnData:true,
  legacyPlayerCodecsRoundtrip:true,shapeEvidence:{engine:'Node V8 HasFastProperties intrinsic',
   forcedGarbageCollection:false,newFieldAdditionsGuaranteedFast:false,cohorts:results}}));
})().catch(error=>{console.error(error?.stack||String(error));process.exit(1);});
'''


TESTS = r'''
const HASH_FORMAT='sha256-player-packed-json-v1';
function expose(env){
 vm.runInContext(`fixture.call=(op,params={})=>v53Call(op,params);
  fixture.packRows=rows=>rows.map(([id,p])=>v18191uPackPlayer(p,id));
  fixture.playerRoundtrip=async rows=>v18191uDecodePlayerChunk(await v18191uEncodePlayerChunk(rows));`,env.context);
}
function playersFixture(year=2029,unemployed=false){
 const s=fixture({year});s.userEmployed=!unemployed;
 if(unemployed)s.coaches.me.clubId=null;
 s.players={};s.teams[0].roster=[];s.teams[1].roster=[];
 for(let i=0;i<1600;i++){
  const id='p'+i,p={unknownExtra:{ordinal:i,text:'Zé 🏆 東京\0 '+i,values:[false,null,0,'']},
   goals:i%7,id,skills:{pass:70,pace:60},name:'Player '+i,age:23,clubId:i%2?'t1':'t2',fitness:100,
   listed:false,injury:0,contract:2031};
  if(i===5)p.name='Ação 漢字 🚀\uD800\0';
  if(i===6){p.unknownExtra.unpaired='\uDFFF';p.unknownExtra.nul='a\0b';}
  s.players[id]=p;s.teams[i%2?0:1].roster.push(id);
 }
 return s;
}
function rowsOf(s){return Object.entries(s.players);}
function currentCanonicalHash(env,rows){return digest(env.ui.packRows(rows));}
function assertScheme(env,manifest,year,label){
 const spec=manifest.collections.players,limit=year>=2029?512:768;
 assert.equal(spec.archiveHash,HASH_FORMAT,label+': canonical hash scheme must be explicit');
 assert.equal(spec.encoding,'FUTBR_PLAYERS_PACKED_GZIP_V1');
 assert.equal(spec.keys.length,Math.ceil(1600/limit));assert.equal(spec.hashes.length,spec.keys.length);
 assert.ok(spec.hashes.every(h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h)),label+': every normal player chunk must carry its hash');
 return spec;
}
async function saveUI(env){const pending=env.ui.persist();await env.ui.flush();await pending;}
async function roundtripPlayers(env,expected){
 const loaded=await env.ui.load();assert.deepEqual(clone(loaded.players),expected);
 env.ui.set(loaded);return loaded;
}
async function workerProducer(kind,year=2029){
 const env=environment();expose(env);let s=playersFixture(year,kind==='jobwait');await env.seed(s);
 const expected=clone(s.players),beforeHistory=history(s),initialManifest=clone(env.disk.get(KEY)),initialSpec=initialManifest.collections.players;
 assert.equal(env.ui.memory().maxRowsPerChunk,year>=2029?512:768);
 if(kind==='vacation'){
  s.vacation={active:true,paused:false,remaining:1,completed:0};
  await env.ui.start('vacation',{liveStateNoPreSave:true,vacationCheckpoint:true});
 }else if(kind==='manual'){
  const day=s.day;s.live={status:'finished',fixtureId:'f'+day,minute:90,home:'t1',away:'t2',homeGoals:1,awayGoals:0};
  await env.ui.start('dayfast',{humanMatch:true});
  await env.ui.call('settle-storage-18373');
 }else{
  const m=env.disk.get(KEY),token={careerId:s.v1903CareerId,coachId:s.userCoachId,user:s.user,futbrSaveId:s.futbrSaveId,
   userEmployed:false,year:s.year,day:s.day,seasonDone:false,token:m.token,revision:m.revision};
  env.ui.setJob(token);await env.ui.start('dayfast',{jobWaitAuto:true,jobWaitResident:false});
  const at=await env.ui.call('check');
  const result=await env.ui.call('jobwait-checkpoint-18370',{careerId:s.v1903CareerId,user:s.user,year:at.year,day:at.day,
   coachDelta:{offers:[],offerMeta:{rejected:{}},tracker:null,career:s.v636CoachCareer,news:[]}});
  assert.equal(result.ok,true);env.ui.setJob(null);
 }
 assert.ok(env.messages.length);assert.ok(env.messages.every(m=>!m.hasState));
 const workerManifest=clone(env.disk.get(KEY)),workerSpec=workerManifest.collections.players;
 assert.equal(workerManifest.day,s.day+1);
 let loaded=await roundtripPlayers(env,expected);assert.deepEqual(history(loaded),beforeHistory);
 const limit=year>=2029?512:768,rows=rowsOf(loaded);

 // Dirty metadata still hashes every current batch. No player chunk is
 // compressed or written when those contents equal the Worker checkpoint.
 const before=env.ui.memory();loaded.manager+=' metadata edit';await saveUI(env);
 const after=env.ui.memory();
 assert.equal(after.playerChunksWritten-before.playerChunksWritten,0,kind+': unchanged current players must reuse their Worker checkpoint, not be recompressed');
 let spec=assertScheme(env,env.disk.get(KEY),year,kind+' to UI');
 assert.deepEqual(spec.keys,workerSpec.keys);
 assert.ok(after.chunksReused-before.chunksReused>=workerSpec.keys.length);
 assert.ok(after.fingerprintCalls-before.fingerprintCalls>=workerSpec.keys.length);
 assertScheme(env,initialManifest,year,'UI initial save');assertScheme(env,workerManifest,year,kind);
 for(let i=0,n=0;i<rows.length;i+=limit,n++)assert.equal(workerSpec.hashes[n],currentCanonicalHash(env,rows.slice(i,i+limit)));
 if(kind==='vacation'){
  const checkpoint=env.disk.get(KEY+':v93vac:meta');
  assert.equal(checkpoint.collections.players.archiveHash,HASH_FORMAT);
  assert.deepEqual(workerSpec.hashes,checkpoint.collections.players.hashes);
 }else{
  // A day that changes only the synthetic fixture date should reuse the UI's
  // canonical chunks even when packed/unpacked property order differs.
  assert.deepEqual(workerSpec.keys,initialSpec.keys,kind+': ordinary Worker must reuse equal UI player chunks');
 }

 // Known fields and unknown extras are equally authoritative. Each change
 // rewrites exactly its own chunk, preserving every other existing key.
 let mutations=0;
 for(const edit of [p=>{p.fitness=81;},p=>{p.unknownExtra.text='Alteração 🧪 漢字\0';},
                   p=>{delete p.listed;},p=>{p.listed=null;}]){
  const oldKeys=[...spec.keys],written=env.ui.memory().playerChunksWritten;
  edit(loaded.players.p900);edit(expected.p900);await saveUI(env);spec=env.disk.get(KEY).collections.players;
  const changed=spec.keys.flatMap((key,i)=>key!==oldKeys[i]?[i]:[]);
  assert.deepEqual(changed,[Math.floor(900/limit)]);assert.equal(env.ui.memory().playerChunksWritten-written,1);mutations++;
 }
 loaded=await roundtripPlayers(env,expected);

 // A null digest cannot prove equality. Only that chunk is rewritten; a
 // legacy raw-player scheme cannot be compared to the packed scheme at all.
 const nullAt=1,prior=clone(env.disk.get(KEY)),written=env.ui.memory().playerChunksWritten;
 env.disk.get(KEY).collections.players.hashes[nullAt]=null;loaded.manager+=' null hash';await saveUI(env);
 spec=env.disk.get(KEY).collections.players;
 assert.deepEqual(spec.keys.flatMap((key,i)=>key!==prior.collections.players.keys[i]?[i]:[]),[nullAt]);
 assert.equal(env.ui.memory().playerChunksWritten-written,1);
 const legacyKeys=[...spec.keys],legacyWritten=env.ui.memory().playerChunksWritten;
 env.disk.get(KEY).collections.players.archiveHash='sha256-json-v1';
 loaded.manager+=' legacy tag';await saveUI(env);spec=assertScheme(env,env.disk.get(KEY),year,'legacy fallback');
 assert.equal(env.ui.memory().playerChunksWritten-legacyWritten,spec.keys.length);
 assert.ok(spec.keys.every((key,i)=>key!==legacyKeys[i]));
 loaded=await roundtripPlayers(env,expected);

 const beforeFailure=clone(env.disk.get(KEY));loaded.players.p1.fitness=13;env.failSave('commit');await saveUI(env);
 assert.equal(env.disk.get(KEY).token,beforeFailure.token);assert.deepEqual(env.disk.get(KEY).collections.players,beforeFailure.collections.players);
 assert.ok(beforeFailure.collections.players.keys.every(key=>env.disk.has(key)));
 const recovered=await env.ui.load();assert.deepEqual(clone(recovered.players),expected);

 const worker=env.workers[0],helpers=worker.context.self.__playerReuseTest18373;
 assert.ok(helpers,'test-only hook into actual private Worker helpers');
 const unicodeRows=[['unicode',{id:'unicode',name:'Zé 漢字 🏆\0\uD800',skills:{pace:70},extra:{nul:'a\0b',unpaired:'\uDFFF'}}]];
 const packed=await helpers.pack(unicodeRows);
 assert.equal(packed.hash,currentCanonicalHash(env,unicodeRows));
 const copy=structuredClone(packed.bytes,{transfer:[packed.bytes]});assert.equal(packed.bytes.byteLength,0);
 assert.ok(copy.byteLength>0);assert.equal(await helpers.hash(unicodeRows),packed.hash);
 assert.ok(helpers.retainedBytes()<=4*1024*1024,'Reusable scratch must never be detached or retain oversized inputs');
 const unsupported=[['x',{id:'x',name:'Not reusable',extra:undefined}]];
 assert.equal(await helpers.hash(unsupported),null);
 if(kind==='vacation'&&year===2029){
  for(const sample of [['a\0é漢🏆\uD800'],['é'.repeat(3*1024*1024)],['small after oversized']])
   assert.equal(await helpers.legacyFingerprint(sample),digest(sample));
  assert.ok(helpers.retainedBytes()<=4*1024*1024);
 }
 const report={producer:kind,year,chunks:workerSpec.keys.length,players:1600,
  metadataPlayerWrites:0,onePlayerMutations:mutations,canonicalHashesVerified:true,
  legacyFallbackRewrites:legacyKeys.length};
 env.close();return report;
}
(async()=>{
 const producers=[];
 for(const kind of ['vacation','manual','jobwait'])producers.push(await workerProducer(kind));
 producers.push(await workerProducer('vacation',2026));
 console.log(JSON.stringify({ok:true,version:'18.373.0',actualUiAndThreeWorkerPathsExecuted:true,
  canonicalHashesMatchPackedBytes:true,metadataOnlySaveReusesAllPlayerChunks:true,
  onePlayerEditRewritesOneChunk:true,knownAndExtraFieldsRoundtrip:true,
  unicodeAndPresenceBitsPreserved:true,alignedChunksBeforeAndAfter2029:true,
  vacationHashesPromotedIntoManifest:true,ordinaryWorkerReusesUiPlayerChunks:true,
  currentEveryBatchFingerprintRecomputed:true,legacyAndNullHashesNeverReused:true,
  failedCommitPreservesPreviousPlayers:true,transferDoesNotDetachHashScratch:true,
  workerHashScratchBounded:true,producers}));
})().catch(error=>{console.error(error?.stack||String(error));process.exit(1);});
'''


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_player_checkpoint_reuse_18373.py <project>')
    root = Path(sys.argv[1])
    source = (root / 'src/index.html').read_text(encoding='utf-8')
    worker = between(source, 'function v53WorkerMain(){', '\n\n\nconst v18191uPlayerFields=')
    if 'FUTBR_PLAYER_CHECKPOINT_REUSE_18373_WORKER' in worker:
        hook = """self.__playerReuseTest18373={
 pack:rows=>v18310PackVacationRows(rows,true),
 hash:rows=>v18373PackedPlayerHash(v18373PreparePackedPlayers(rows)),
 retainedBytes:()=>v18373WorkerHashScratch?.byteLength||0,
 legacyFingerprint:rows=>v18343Fingerprint(rows)};
 """
        anchor = "self.postMessage({kind:'ready'});"
        assert worker.count(anchor) == 1
        worker = worker.replace(anchor, hook + anchor, 1)
    persist_start = source.index('// No career payload is written to LocalStorage.')
    payload = {
        'worker': worker,
        'runtime': between(source, '/* FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN', '/* FUTBR_SAVE_MEMORY_RUNTIME_18373_END */'),
        'playerCodec': between(source, 'const v18191uPlayerFields=', '// 5.3: one authoritative simulation'),
        'baseStart': between(source, 'async function v53StartSimulation(mode,options={}){', '\nrunVacation=async function()'),
        'bootUI': between(source, '/* FUTBR_VACATION_BOUNDED_BOOT_18373 */', 'async function v53StartSimulation(mode,options={}){'),
        'persist': between(source[persist_start:], 'persist=function(notify=false){', '\nv52FlushSave=async function()'),
        'deferredPersist': between(source, 'const v168BasePersist=persist;', 'const v168BaseStartSimulation='),
        'rolloverWrapper': between(source, 'const v168BaseStartSimulation=v53StartSimulation;', '\nconst v168BasePrepare='),
        'jobIdentity': between(source, 'function v18373JobIdentity(s=state){', 'function v18373LightTeam('),
        'migrationPause': between(source, 'function v18373ArchiveMigrationPaused(){', 'window.GestorFC.jobWaitMemory18373='),
        'migration': between(source, 'let v555ArchiveMigration=null,v555ArchiveMigrationTimer=0;', 'const v555BaseActualClubsByYear='),
    }
    anchor = '(async()=>{\n const normal=await runGood();'
    assert BOOT_NODE.count(anchor) == 1
    harness = BOOT_NODE[:BOOT_NODE.index(anchor)] + TESTS
    scripts = [m[2] for m in re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script\s*>', source, re.I)
               if not re.search(r'type\s*=\s*["\'](?:application/[^"\']+|importmap)', m[1], re.I)]
    with tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        (work / 'test.js').write_text(harness, encoding='utf-8')
        (work / 'payload.json').write_text(json.dumps(payload), encoding='utf-8')
        (work / 'scripts.json').write_text(json.dumps(scripts), encoding='utf-8')
        shape_codecs = [
            {'prefix': 'v18191w', 'source': between(source, 'const v18191wPlayerFields=', ' const V171_FORMAT='),
             'legacy': legacy_unpacker('v18191w')},
            {'prefix': 'v18191u', 'source': payload['playerCodec'], 'legacy': legacy_unpacker('v18191u')},
            {'prefix': 'v18191m', 'source': between(source, 'const v18191mPlayerFields=', 'async function v18183DbWriteMany('),
             'legacy': legacy_unpacker('v18191m')},
        ]
        (work / 'shapes.js').write_text(SHAPES, encoding='utf-8')
        (work / 'shape-codecs.json').write_text(json.dumps(shape_codecs), encoding='utf-8')
        syntax = subprocess.run(['node', '-e', "const fs=require('fs'),vm=require('vm');for(const s of JSON.parse(fs.readFileSync(process.argv[1])))new vm.Script(s)", str(work / 'scripts.json')],
                                capture_output=True, text=True, timeout=45)
        if syntax.returncode:
            raise RuntimeError(syntax.stderr)
        shapes = subprocess.run(['node', '--allow-natives-syntax', str(work / 'shapes.js'), str(work / 'shape-codecs.json')],
                                capture_output=True, text=True, timeout=90)
        if shapes.returncode:
            raise RuntimeError(shapes.stderr[-12000:])
        run = subprocess.run(['node', str(work / 'test.js'), str(work / 'payload.json')],
                             capture_output=True, text=True, timeout=180)
        if run.returncode:
            raise RuntimeError(run.stderr[-14000:] + '\n' + run.stdout[-3000:])
        report = json.loads(run.stdout.strip().splitlines()[-1])
        report.update(json.loads(shapes.stdout.strip().splitlines()[-1]))
    report['inlineScriptsParsed'] = len(scripts)
    (root / 'player-checkpoint-reuse-18373-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
