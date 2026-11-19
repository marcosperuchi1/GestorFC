from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from test_oomsafe_saves_18352 import TEST
from test_season_saves_18343 import jsfunc

ROOT_ARCHIVES=['scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive']
def swap_once(s,old,new,label):
 if s.count(old)!=1:
  raise RuntimeError('18.354 '+label+': expected one, got '+str(s.count(old)))
 return s.replace(old,new,1)

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_archive_root_shards_18354.py <project>')
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 for mark in ('FUTBR_ARCHIVE_ROOT_SHARDS_18354 UI','FUTBR_ARCHIVE_ROOT_SHARDS_18354 Worker',
              'FUTBR_NATIVE_MIRROR_18354','FUTBR_ARCHIVE_COPY_ON_WRITE_18343',
              'FUTBR_OOMSAFE_ARCHIVE_18352'):
  if mark not in html:raise RuntimeError('Archive regression missing '+mark)
 original="['v538CareerArchive','v555CareerArchive','players','retirements','transfers']"
 expanded="['v538CareerArchive','v555CareerArchive','players','retirements','transfers','scorerArchive','history','internationalHistory','v735NationalArchive']"
 js=TEST.replace(original,expanded)
 if js==TEST or original in js:raise RuntimeError('Failed to update test writer keys')
 insert=r"""
// 2030+ archives previously lived in root: assert lossless sharding now.
s.scorerArchive=Array.from({length:5},(_,i)=>({year:2026+i,competitions:{
 'league:bra:3':{p1:{goals:i+14,team:'a'},p2:{goals:i+14,team:'b'}}}}));
s.history=Array.from({length:169},(_,i)=>({year:2026+i%5,round:i,
 winner:'a',loser:'b',events:[{minute:15,goal:'p1'}]}));
s.internationalHistory=Array.from({length:88},(_,i)=>({year:2026+i%5,
 continent:'uefa',winner:'a',runner:'b'}));
s.v735NationalArchive={2026:{matches:[],winner:'BRA'},2027:{matches:[],winner:'FRA'},
 2028:{matches:[],winner:'ARG'},2029:{matches:[],winner:'ESP'}};
s.transfers=Array.from({length:149},(_,i)=>({id:'t'+i,year:2026+i%5,player:'p'+i,
 from:'a',to:'b',fee:i*10000}));
s.retirements=Array.from({length:113},(_,i)=>({id:'r'+i,year:2026+i%5,age:36,
 player:'p'+i}));
const extras=['scorerArchive','transfers','retirements','history',
 'internationalHistory','v735NationalArchive'];
function assertRootArchivesSharded(db,manifest,label){
 for(const k of extras){
  assert(!Object.hasOwn(manifest.root,k),label+': '+k+' still embedded in root');
  assert(manifest.collections[k],label+': missing collection '+k);
  assert(manifest.collections[k].keys.length>0,label+': no chunks '+k);
  assert.equal(JSON.stringify(decodeDb(db,manifest,k)),JSON.stringify(s[k]),
   label+': lost data in '+k);
 }
 assert(manifest.collections.scorerArchive.keys.length>=5,label+': five archive years merged');
 assert(manifest.collections.transfers.keys.length>=3,label+': transfers chunk exceeds 64 entries');
 assert(manifest.collections.history.keys.length>=14,label+': years/events chunk exceeds 12 entries');
}
"""
 js=swap_once(js,'function decodeDb(db,m,key){',insert+'\nfunction decodeDb(db,m,key){','add 2030 history')
 js=swap_once(js,'const first=clone(db.get(KEY));','const first=clone(db.get(KEY));\n assertRootArchivesSharded(db,first,"UI");',
              'UI write/read all archive collections')
 js=swap_once(js,'const latest=db.get(STORE);',
              'const latest=db.get(STORE);\n assertRootArchivesSharded(db,latest,"Worker");',
              'Worker write/read all archive collections')
 js=swap_once(js,
  "const legacy={format:V171_FORMAT,year:2028,root:{year:2028},collections:{",
  "const legacy={format:V171_FORMAT,year:2028,root:{year:2028,scorerArchive:[{year:2026,competitions:{}}]},collections:{",
  'old root archive fixture')
 js=swap_once(js,
  "assert.equal(JSON.stringify(old.v538CareerArchive),JSON.stringify(oldYear),'Legacy unsharded save cannot load');",
  """assert.equal(JSON.stringify(old.v538CareerArchive),JSON.stringify(oldYear),'Legacy unsharded save cannot load');
 assert.deepEqual(JSON.parse(JSON.stringify(old.scorerArchive)),[{year:2026,competitions:{}}],
  'Old root-embedded scorer archive must remain readable');""",
  'backward compatibility assertion')
 js=swap_once(js,
  "console.log(JSON.stringify({ok:true,version:'18.352.0',ui,worker,",
  "console.log(JSON.stringify({ok:true,version:'18.354.0',ui,worker,",
  'report version')
 # Extract the two actual writers, unlike a static-only check.
 def helper(needle):
  idx=html.index(needle)
  start=html.rfind('/* FUTBR_OOMSAFE_ARCHIVE_18352',0,idx)
  if start<0:raise RuntimeError('Nested archive helper not found: '+needle)
  return html[start:idx]
 ui_anchor='async function writeCollection(token,key,value,limit,previous=null){'
 worker_anchor='async function save(s){'
 ui=helper(ui_anchor)+'\n'+jsfunc(html,ui_anchor)+'\n'+jsfunc(html,"async function saveSharded(s,mode='full'){")
 worker=helper(worker_anchor)+'\n'+jsfunc(html,worker_anchor)+'\n'+jsfunc(html,'async function v171DecodeManifest(x)')
 program='globalThis.UI_CODE='+json.dumps(ui)+';\n'
 program+='globalThis.WORKER_CODE='+json.dumps(worker)+';\n'+js
 filename=root/'test-archive-root-shards-18354.cjs'
 filename.write_text(program,encoding='utf-8')
 try:
  syntax=subprocess.run(['node','--check',str(filename)],capture_output=True,text=True,timeout=35)
  if syntax.returncode:raise RuntimeError('JS check '+syntax.stderr[-8500:])
  result=subprocess.run(['node','--max-old-space-size=512',str(filename)],
   capture_output=True,text=True,timeout=180)
  if result.returncode:raise RuntimeError('Sharded 2030 save regression: '+result.stderr[-11000:])
 finally:
  filename.unlink(missing_ok=True)
 report=json.loads(result.stdout.strip().splitlines()[-1])
 report['allSixRootArchivesSharded']=True
 report['legacyRootArchivesStillReadable']=True
 report['UIAndWorkerRoundTripAllHistoryTypes']=True
 report['writtenShardSizesBounded']=True
 report['noHistoryOrFieldDropped']=True
 report['simulatedUnder512MBNodeHeap']=True
 (root/'archive-root-shards-18354-tests.json').write_text(
   json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
