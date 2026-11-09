from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def function(src, name):
    m=re.search(r'(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',src)
    if not m:raise RuntimeError('missing function '+name)
    start=m.start();p=src.index('{',m.end());depth=0;quote=None;comment=None;escape=False;i=p
    while i<len(src):
        c=src[i];n=src[i:i+2]
        if comment=='line':
            if c=='\n':comment=None
        elif comment=='block':
            if n=='*/':comment=None;i+=1
        elif quote:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c==quote:quote=None
        elif n=='//':comment='line';i+=1
        elif n=='/*':comment='block';i+=1
        elif c in "'\"`":quote=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return src[start:i+1]
        i+=1
    raise RuntimeError('unbalanced function '+name)

def is_javascript_script(attrs):
    m=re.search("type\\s*=\\s*['\"]([^'\"]+)['\"]",attrs,re.I)
    if not m:return True
    kind=m.group(1).strip().lower().split(';',1)[0].strip()
    return kind in {'module','text/javascript','application/javascript','text/ecmascript','application/ecmascript','application/x-javascript','text/jscript'}

def codec(src,prefix):
    start=src.index('const '+prefix+'PlayerFields=')
    end=src.index('function '+prefix+'PackPlayer(',start)
    return src[start:end]+'\n'+'\n'.join(function(src,prefix+suffix) for suffix in ('PackPlayer','UnpackPlayer','ArrayBufferToBase64'))

HARNESS=r'''
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
let world=null,session=1,v18117SyncSeq=0,v18117SyncAck=0;
const shards=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats'];
const V93_VAC_META='career:v93vac:meta',V93_VAC_PREFIX='career:v93vac:';
const safe=k=>!['__proto__','constructor','prototype'].includes(k);
const v93CheckpointKey=(token,key,i)=>V93_VAC_PREFIX+token+':'+key+':'+i;
let disk=new Map(),received=null,last=null,errors=[],batchSizes=[],failWrite=false;
async function read(k){return disk.get(k);}
async function v93RawWrite(k,v){disk.set(k,structuredClone(v));}
async function v18181RawWriteMany(entries){
 batchSizes.push(entries.length);
 if(failWrite)throw Error('injected storage failure');
 const prepared=entries.map(e=>[e.key,structuredClone(e.value)]);
 for(const [k,v] of prepared)disk.set(k,v);
}
const self={postMessage(msg,transfer=[]){
 const m=structuredClone(msg,{transfer});
 if(m.kind==='vac-sync-start')received={...m.root,v538CareerArchive:archive538,v555CareerArchive:archive555,scorerArchive:scorers};
 if(m.kind==='vac-sync-collection-start')received[m.key]=m.isArray?new Array(m.length):{};
 if(m.kind==='vac-sync-part')for(const [id,row] of v18310VacationRows(m))received[m.key][id]=row;
 if(m.kind==='vac-checkpoint-error')errors.push(m.error);
 if(m.kind==='vac-sync-end')last=m;
 if(m.syncSeq)queueMicrotask(()=>v18310ResolveSyncAck(m.syncSeq));
}};
const archive538 = {};
const archive555 = {};
archive555['2025'] = {
 version: 1,
 n: {A: 'Player'},
 p: {p0: ['2025;12;4']}
};
const scorers = [{
 year: 2025,
 competitions: {league: {p0: {goals: 12, assists: 4}}}
}];
function fixture(n,year){
 const players={};
 for(let i=0;i<n;i++){
  const id='p'+i;
  players[id]={id,name:'Atleta '+i,pos:['GOL','ZAG','LAT','VOL','MEI','ATA'][i%6],age:18+i%23,natCode:'BRA',skills:{attack:i%100,defense:(i*7)%100},potential:65+i%35,fitness:100,goals:i%40,assists:i%19,apps:i%46,clubId:'t'+i%60,totalGoals:33+i%300,careerMinutes:5000+i,real:!!(i%2),custom18310:{nullValue:null,zero:0,empty:'',falseValue:false,years:[2026,2027,2028]},honors:[{year:year-1,type:'champion'}]};
 }
 return {year,day:90,seasonDone:true,players,teams:[{id:'t0',roster:['p0','p1'],academy:['p2']}],coaches:{c0:{id:'c0',history:[{year:year-1,club:'t0'}]}},schedule:[{fixtures:[{home:'t0',away:'t1',result:{home:2,away:0,scorers:['p0']}}]}],competitionStats:{league:{p0:{goals:12,assists:4,apps:30}}},allTimeStats:{p0:{goals:333,assists:127}},v538CareerArchive:archive538,v555CareerArchive:archive555,scorerArchive:scorers};
}
function digest(obj){return crypto.createHash('sha256').update(JSON.stringify(obj,(key,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v)).digest('hex');}
(async()=>{
 const results=[];
 for(let year=2026;year<=2030;year++){
  const n=year===2029?202574:12500;
  world=fixture(n,year);const expected=digest(world.players),statsBefore=JSON.stringify(world.allTimeStats);
  batchSizes=[];errors=[];const t=performance.now();await streamVacationWorld125(true,false);
  assert.equal(digest(received.players),expected,'all player fields must survive transfer');
  assert.equal(JSON.stringify(received.allTimeStats),statsBefore,'career totals must survive');
  assert.strictEqual(received.scorerArchive,scorers,'immutable history is not cloned or lost');
  assert.equal(world.players,null,'worker releases players');
  assert.equal(last.checkpoint,true);assert.equal(errors.length,0);assert.ok(Math.max(...batchSizes)<=8);
  const meta=disk.get(V93_VAC_META),fromDisk={};
  for(let i=0;i<meta.collections.players.chunks;i++){
   const rows=await v18191wDecodePlayerChunk(disk.get(v93CheckpointKey(meta.token,'players',i)));
   for(const [id,p] of rows)fromDisk[id]=p;
  }
  assert.equal(digest(fromDisk),expected,'compressed checkpoint must reload exactly');
  world={};assert.equal(await v93ApplyVacationCheckpoint(year,90),true);
  assert.equal(digest(world.players),expected,'real resume function must decode packed checkpoints');
  assert.equal(await v93ApplyVacationCheckpoint(year,91),false,'wrong day must not apply a checkpoint');
  results.push({year,players:n,ms:Math.round(performance.now()-t),transactions:batchSizes.length,maxBatch:Math.max(...batchSizes),wireBytes:last.performance18310.playerBytes});
  disk.clear();received=null;world=null;if(global.gc)global.gc();
 }
 disk.set(V93_VAC_META,{format:'GFC_VAC_CHECKPOINT_93',token:'legacy',year:2024,day:3,rootKey:'legacy-root',collections:{players:{isArray:false,chunks:1}}});
 disk.set('legacy-root',{year:2024,day:3});disk.set(v93CheckpointKey('legacy','players',0),[['p-old',{id:'p-old',name:'Legacy',goals:37}]]);
 world={};assert.equal(await v93ApplyVacationCheckpoint(2024,3),true);assert.equal(world.players['p-old'].goals,37);disk.clear();
 const previous={format:'GFC_VAC_CHECKPOINT_93',token:'previous-good'};
 disk.set(V93_VAC_META,previous);world=fixture(2200,2031);const wanted=digest(world.players);failWrite=true;errors=[];
 await streamVacationWorld125(true,false);
 assert.equal(last.checkpoint,false);assert.ok(errors.length>0);
 assert.strictEqual(disk.get(V93_VAC_META),previous);assert.equal(digest(received.players),wanted);
 assert.equal(v18310SyncWaiters.size,0,'ack waiters cannot leak');
 console.log(JSON.stringify({ok:true,scope:'synthetic transfer/checkpoint cycles, not full-season simulation',cycles:results,integrity:'all JSON-compatible player fields, extras, totals and scorer archives',storageFailureRecovery:true,workerReleased:true,maxPendingChunks:8,legacyCheckpoint:true,heapMiB:Math.round(process.memoryUsage().heapUsed/1048576)},null,2));
})().catch(e=>{console.error(e);process.exit(1)});
'''

def main():
    project=Path(sys.argv[1]).resolve();html=(project/'src/index.html').read_text(encoding='utf-8')
    scripts=[m.group(2) for m in re.finditer(r'<script\\b([^>]*)>(.*?)</script>',html,re.S|re.I) if is_javascript_script(m.group(1))]
    assert 'scorerArchive:scorers||[]' in html
    chunks=[]
    for prefix in ['v18191w','v18191u']:
        chunks.append(codec(html,prefix))
    chunks+=[function(html,'v18191wDecodePlayerChunk'),function(html,'v18310PackVacationRows'),'const v18310SyncWaiters=new Map();',function(html,'v18310ResolveSyncAck'),function(html,'v18117WaitSyncAck'),function(html,'v18310VacationRows'),function(html,'streamVacationWorld125'),function(html,'v93ApplyVacationCheckpoint')]
    test=project/'test-season-sync-18310.cjs'
    test.write_text('\n'.join(chunks)+'\n'+HARNESS,encoding='utf-8')
    checked=subprocess.run(['node','--check',str(test)],capture_output=True,text=True,encoding='utf-8',timeout=30)
    if checked.returncode:
        print('GENERATED TEST SOURCE\n'+test.read_text(encoding='utf-8')[:45000])
        raise RuntimeError(checked.stderr)
    run=subprocess.run(['node','--expose-gc','--max-old-space-size=2048',str(test)],capture_output=True,text=True,encoding='utf-8',timeout=180)
    print(run.stdout)
    if run.returncode:raise RuntimeError(run.stderr)
    result=json.loads(run.stdout)
    (project/'season-sync-18310-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    syntax=project/'syntax-18310.cjs'
    syntax.write_text("const vm=require('node:vm');const fs=require('node:fs');const scripts=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let checked=0,skippedJson=0;for(let i=0;i<scripts.length;i++){const src=String(scripts[i]??'').trim();if((src.startsWith('{')||src.startsWith('['))){try{JSON.parse(src);skippedJson++;continue;}catch{}}try{new vm.Script(scripts[i],{filename:'inline-'+i});checked++;}catch(e){console.error(e);process.exit(1)}}console.log('syntax ok '+checked+' js; skipped '+skippedJson+' json');",encoding='utf-8')
    data=project/'scripts-18310.json';data.write_text(json.dumps(scripts),encoding='utf-8')
    subprocess.run(['node',str(syntax),str(data)],check=True,timeout=40)
    data.unlink();test.unlink();syntax.unlink()

if __name__=='__main__':main()
