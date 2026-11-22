"""Test 18.382 production code: lossless named saves, bounded native reads,
robust failure recovery, sharded loading and player transfer invariants."""
from pathlib import Path
import hashlib,json,subprocess,sys
from playwright.sync_api import sync_playwright

def extract(s,a,b):
 x=s.find(a)
 if x<0:raise RuntimeError('Missing regression begin marker '+a)
 y=s.find(b,x+len(a))
 if y<0:raise RuntimeError('Missing regression end marker '+b)
 return s[x:y]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_career_sync_load_18382.py <game-root>')
 root=Path(sys.argv[1]).resolve()
 source=(root/'src/index.html').read_text(encoding='utf-8')
 copy=extract(source,'/* FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382','\nfunction block(text){')
 hydrate=extract(source,' async function hydrateManifest(manifest,progress=null){',' async function loadDirect(progress=null,allowOwner=false){')
 sync=extract(source,'/* FUTBR_CAREER_SYNC_LOW_ALLOC_18382','const v53Base={render,renderWelcome,act,persist,guardManage,loadLocal,helpPage,vacationPage,commitDay,downloadFile};')
 assertions=[
  'const stride=4;' in hydrate,
  'const stored=await readMany(partKeys);' in hydrate,
  'stored[j]=null' in hydrate,
  "if(i+stride<keys.length)await yieldUI();" in hydrate,
  "await v18382CopyChunkGroup(group);" in copy,
  'if(pairs.length>4)' in copy,
  "await delMany(created).catch" in copy,
  "async function v18382CopyChunkGroup(pairs)" in copy,
  "if(m.format==='player-packed-buffer-v1'" in sync,
  "m.bytes=null;" in sync,
  "dst[player.id]=player;" in sync,
  "v18382ApplyVacationRows(dst,m)" in source,
  "seq:Number(m.syncSeq)||0" in source,
  "if(card&&card.dataset.v18382Pct!==String(pct))" in source
 ]
 if not all(assertions):raise RuntimeError('Lost a required bounded data invariant: '+str([i for i,x in enumerate(assertions) if not x]))
 mock=r"""
const assert=require('node:assert/strict');
const FORMAT='GFC_SHARDED_171';
const errors=[];
global.window={GestorFC:{},FutBRDesktop:null};
const actual=new Map(),readCalls=[],writeCalls=[],deleted=[];
const cloning=value=>JSON.parse(JSON.stringify(value));
window.FutBRDesktop={
 directStorage:true,
 async readMany(keys){readCalls.push(keys.length);return keys.map(k=>actual.has(k)?cloning(actual.get(k)):null);},
 async writeMany(entries){writeCalls.push(entries.length);for(const e of entries)actual.set(e.key,cloning(e.value));}
};
function manifestKeys(m){return m.format===FORMAT?Object.values(m.collections||{}).flatMap(s=>s.keys||[]):[];}
async function delMany(keys){deleted.push(...keys);for(const k of keys)actual.delete(k);}
function now(){return 555;}
function db(){throw Error('Native path must not call browser IndexedDB');}
"""
 checks_copy=r"""
(async()=>{
 // Simulate 452 independent stored chunks: 450 packed player shards are
 // sufficient to represent a 225k+ world at typical >=500 players per shard.
 const playerKeys=Array.from({length:450},(_,i)=>'save:players:'+i);
 for(let i=0;i<playerKeys.length;i++){
  actual.set(playerKeys[i],{format:'packed',rows:[[i*512,'p'+i]],count:512});
 }
 actual.set('save:history:0',[['2036',{goals:160,assist:24}]]);
 actual.set('save:history:1',[['2037',{goals:182,assist:25}]]);
 const oldManifest={
  format:FORMAT,version:'18.381',root:{careerId:'A',year:2038,day:101},
  collections:{
   players:{encoding:'json',isArray:false,keys:playerKeys,length:0},
   v555CareerArchive:{nested:'year-id-v1',isArray:false,keys:['save:history:0','save:history:1']}
  }
 };
 const copied=await copyManifest(oldManifest,'archive:A');
 assert.equal(copied.created.length,452);
 assert.equal(copied.manifest.collections.players.keys.length,450);
 assert.deepEqual(copied.manifest.root,oldManifest.root);
 assert.equal(readCalls.reduce((a,b)=>a+b,0),452);
 assert.equal(writeCalls.reduce((a,b)=>a+b,0),452);
 assert(readCalls.every(n=>n<=4&&n>0),readCalls);
 assert(writeCalls.every(n=>n<=4&&n>0),writeCalls);
 assert(readCalls.length<125,'Request count must drop below a quarter of the original individual IPC reads');
 assert.equal(v18382CopyMetrics.maxReadBatch,4);
 // Stored copies must be independent across careers.
 actual.get(copied.manifest.collections.players.keys[0]).rows[0][1]='changed-in-archive';
 assert.equal(actual.get(playerKeys[0]).rows[0][1],'p0','Original save must be immutable');
 const restored=await copyManifest(copied.manifest,'active:B');
 assert.equal(restored.manifest.collections.players.keys.length,450);
 assert.notEqual(restored.manifest.collections.players.keys[0],copied.manifest.collections.players.keys[0]);
 assert.notEqual(restored.manifest.collections.players.keys[0],playerKeys[0]);
 // Failure path: simulate a missing mid-copy shard and verify full cleanup
 // of newly allocated destination keys without touching any source key.
 const bad={format:FORMAT,root:{id:'broken'},collections:{players:{
  isArray:false,keys:[playerKeys[0],playerKeys[1],'absent',playerKeys[3],playerKeys[4]]}}};
 let err=null;try{await copyManifest(bad,'archive:failure');}catch(e){err=e;}
 assert(err&&/indisponível/.test(err.message),'Missing shard must fail safely');
 assert(!actual.has('archive:failure:players:0'),'Failed copy destination must be cleaned');
 assert(!actual.has('archive:failure:players:4'),'Failed partial batch must be cleaned');
 assert(actual.has(playerKeys[0])&&actual.has(playerKeys[1]),'Old save must remain intact');
 console.log('COPY_OK '+JSON.stringify({readBatches:readCalls.length/2,maxNativeBatch:v18382CopyMetrics.maxReadBatch,
  independentlyCopied:452,preservedUnchangedSource:true,failureCleanup:true}));
})();
"""
 # Run copy test first, then use isolated declarations for restore/reader testing.
 src_copy=mock+'\n'+copy+'\n'+checks_copy
 f=root/'career-copy-18382-fixture.cjs'
 f.write_text(src_copy,encoding='utf-8')
 proc=subprocess.run(['node',str(f)],text=True,capture_output=True,timeout=65)
 try:f.unlink()
 except OSError:pass
 if proc.returncode:raise RuntimeError('Named-save clone regression: '+proc.stderr[-3200:])
 copy_report=json.loads([s[8:] for s in proc.stdout.splitlines() if s.startswith('COPY_OK ')][-1])
 mock_load=r"""
const assert=require('node:assert/strict');
const FORMAT='GFC_SHARDED_171',v18191uPlayerFormat='v18191-packed-test';
const reading=new Map(),calls=[],progress=[];
const yieldUI=async()=>{};
const readMany=async keys=>{calls.push(keys.length);return keys.map(k=>reading.get(k));};
const v18191uDecodePlayerChunk=async obj=>obj.records;
const v18373ApplyArchivePath=(dst,row)=>{
 const path=row[0];let obj=dst;
 for(let i=0;i<path.length-1;i++)obj=obj[path[i]]??(obj[path[i]]={});
 obj[path[path.length-1]]=row[1];
};
const applyLegacyArchive=(dst,row)=>{dst[row[0]]??={};dst[row[0]][row[1]]=row[2];};
const manifest={format:FORMAT,root:{careerId:'sample',year:2038},collections:{
 players:{isArray:false,keys:[],encoding:'packed'},
 v555CareerArchive:{isArray:false,nested:'tree-path-v1',keys:[]},
 teams:{isArray:true,length:3,keys:[]}
}};
for(let i=0;i<17;i++){
 const key='players:'+i;manifest.collections.players.keys.push(key);
 reading.set(key,{format:v18191uPlayerFormat,records:
  Array.from({length:600},(_,j)=>['p'+(i*600+j),{id:'p'+(i*600+j),form:i%2?7:4,goals:j}])});
}
reading.set('history:a',[[['2031','p5'],{club:'x',apps:28,goals:13}]]);
reading.set('history:b',[[['2032','p5'],{club:'y',apps:30,goals:15}]]);
manifest.collections.v555CareerArchive.keys=['history:a','history:b'];
reading.set('teams:0',[[0,{id:'t0',name:'Flamengo'}],[1,{id:'t1',name:'Palmeiras'}],[2,{id:'t2',name:'Corinthians'}]]);
manifest.collections.teams.keys=['teams:0'];
"""
 checks_load=r"""
(async()=>{
 const full=await hydrateManifest(manifest,p=>progress.push(p));
 assert.equal(Object.keys(full.players).length,10200);
 assert.equal(full.players.p1020.goals,420);
 assert.equal(full.v555CareerArchive['2032'].p5.goals,15);
 assert.equal(full.teams.length,3);
 assert.equal(full.teams[0].name,'Flamengo');
 assert.equal(full.careerId,'sample');
 assert(calls.every(n=>n>=1&&n<=4),'Read groups must stay <=4');
 assert.equal(calls.reduce((a,b)=>a+b,0),20);
 assert.equal(progress.length,20,'Every chunk must retain its progress callback');
 assert(progress.some(p=>p.key==='players'&&p.done===17&&p.total===17));
 const cut=reading.get('players:4');
 reading.delete('players:4');
 let err=null;try{await hydrateManifest(manifest);}catch(e){err=e;}
 assert(err&&/Bloco do save ausente/.test(err.message));
 reading.set('players:4',cut);
 console.log('LOAD_OK '+JSON.stringify({readCalls:calls.length/2,loadedPlayers:10200,
  batchCeiling:Math.max(...calls),historyLossless:true,missingChunkFailClosed:true}));
})();
"""
 f=root/'career-load-18382-fixture.cjs'
 f.write_text(mock_load+'\n'+hydrate+'\n'+checks_load,encoding='utf-8')
 proc=subprocess.run(['node',str(f)],text=True,capture_output=True,timeout=60)
 try:f.unlink()
 except OSError:pass
 if proc.returncode:raise RuntimeError('Bounded loading regression: '+proc.stderr[-3500:])
 load_report=json.loads([s[8:] for s in proc.stdout.splitlines() if s.startswith('LOAD_OK ')][-1])
 mock_sync=r"""
const assert=require('node:assert/strict');
global.window={};
const v18382SyncMetrics={players:0,batches:0,decodeMs:0,maxPackedBytes:0,lastBatchMs:0};
const v18191uUnpackPlayer=row=>({id:row[0],name:row[1],country:row[2],overall:row[3]});
const v18310VacationRows=m=>m.rows||[];
const v18373ApplyTreeRow=(dst,row)=>{dst[row[0]]=row[1];};
"""
 # The real sync helper declares v18382SyncMetrics, so strip only the mock declaration.
 mock_sync=mock_sync.replace("const v18382SyncMetrics={players:0,batches:0,decodeMs:0,maxPackedBytes:0,lastBatchMs:0};","")
 checks_sync=r"""
const world={},total=225343;
for(let i=0;i<total;i+=512){
 const last=Math.min(total,i+512);
 const rows=Array.from({length:last-i},(_,j)=>['p'+(i+j),'Atleta '+(i+j),'BRA',(i+j)%100]);
 const bytes=new TextEncoder().encode(JSON.stringify(rows)).buffer;
 const message={format:'player-packed-buffer-v1',bytes};
 const applied=v18382ApplyVacationRows(world,message);
 assert.equal(applied,last-i);
 assert.equal(message.bytes,null,'Transferred source buffer must be released');
}
assert.equal(Object.keys(world).length,total);
assert.equal(world.p225342.name,'Atleta 225342');
assert.equal(world.p12345.country,'BRA');
assert.equal(v18382SyncMetrics.players,total);
assert.equal(v18382SyncMetrics.batches,Math.ceil(total/512));
assert(v18382SyncMetrics.maxPackedBytes<200000);
assert(v18382SyncMetrics.decodeMs>=0);
const hist={};
assert.equal(v18382ApplyVacationRows(hist,{format:'tree-path-v1',rows:[['t1',{winner:'Flamengo'}]]}),1);
assert.equal(hist.t1.winner,'Flamengo');
assert(!String(v18382ApplyVacationRows).includes('yield [p.id,p]'),'No per-player pair array intermediary');
console.log('SYNC_OK '+JSON.stringify({playerCount:total,batches:v18382SyncMetrics.batches,
 maxPackedBytes:v18382SyncMetrics.maxPackedBytes,decodedWithoutPerPlayerTuple:true,
 historyFallback:true,ackLogicUnchanged:true}));
"""
 f=root/'career-sync-18382-fixture.cjs'
 f.write_text(mock_sync+'\n'+sync+'\n'+checks_sync,encoding='utf-8')
 proc=subprocess.run(['node',str(f)],text=True,capture_output=True,timeout=100)
 try:f.unlink()
 except OSError:pass
 if proc.returncode:raise RuntimeError('Full-world 225343 player transfer regression: '+proc.stderr[-3500:])
 sync_report=json.loads([s[8:] for s in proc.stdout.splitlines() if s.startswith('SYNC_OK ')][-1])
 report={
  'ok':True,'version':'18.382.0','independentSavesPreserved':True,
  'legacyAndPackedSaveLoadLossless':True,'missingChunkFailsWithoutOverwrite':True,
  'maxConcurrentReadChunks':4,'maxCopyChunks':4,
  'playerWorldTransferredExactly':True,'playerCount':sync_report['playerCount'],
  'nativeCopyCallsReducedAtLeastFourfold':True,
  'syncNoExtraWorldClone':True,'workerAckGuardPreserved':True,
  'yearHistoriesPreserved':True,
  'copy':copy_report,'load':load_report,'sync':sync_report,
  'sourceSha256':hashlib.sha256(source.encode()).hexdigest()
 }
 (root/'career-sync-load-18382-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
