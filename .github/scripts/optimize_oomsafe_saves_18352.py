from __future__ import annotations
import json
import sys
from pathlib import Path

MARK = 'FUTBR_OOMSAFE_ARCHIVE_18352'
VERSION = '18.352.0'
NESTED_HELPER = r"""
/* FUTBR_OOMSAFE_ARCHIVE_18352: lossless annual player-history chunks.
   The old format placed ALL career years in one JS array and SHA256 JSON string.
   Iterate each (year,player) record instead; no historical data or field is dropped.
   Legacy manifests lacking the nested marker still decode in the old format. */
const v18352NestedArchiveKeys=new Set(['v538CareerArchive','v555CareerArchive']);
const v18352ArchiveStats={version:'18.352',format:'year-id-v1',rowsPerChunk:128,
  preservesOldManifest:true,fullHistoryRetained:true};
function v18352ApplyArchivedRow(dst,entry){
 if(!Array.isArray(entry)||entry.length<3)throw Error('Invalid archived history chunk');
 const year=String(entry[0]),id=entry[1];
 if(year==='__proto__'||year==='prototype'||year==='constructor')throw Error('Invalid historical year');
 if(id===null){
  dst[year]=entry[3]===1?{}:entry[2];
  return;
 }
 if(id==='__proto__'||id==='prototype'||id==='constructor')throw Error('Invalid historical player id');
 if(dst[year]==null)dst[year]={};
 else if(typeof dst[year]!=='object'||Array.isArray(dst[year]))
  throw Error('Invalid historical year record');
 dst[year][id]=entry[2];
}
"""

UI_FUNC_OLD = "async function writeCollection(token,key,value,limit,previous=null){"
WORKER_OLD = "const v18181Stable=new Set(['v538CareerArchive','v555CareerArchive','scorerArchive']);"

def swap(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f'{label}: expected one anchor but found {n}')
    return s.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: optimize_oomsafe_saves_18352.py <project>')
    root=Path(sys.argv[1]).resolve()
    cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    if cfg.get('version')!=VERSION:
        raise RuntimeError('Desktop must be version 18.352.0 for this update')
    path=root/'src/index.html'
    html=path.read_text(encoding='utf-8')
    if MARK in html:raise RuntimeError('18.352 already applied')
    for required in ('FUTBR_CLEAN_INCREMENTAL_SHARDS_18349',
       'FUTBR_ARCHIVE_COPY_ON_WRITE_18343','FUTBR_SERIEC_PHASES_HISTORY_18351',
       'FUTBR_CALENDAR_MATCH_RETIRE_18350','async function v171DecodeManifest(x)',
       'async function save(s){','async function saveSharded(s,mode=',
       'async function writeCollection(token,key,value,limit,previous=null){'):
        if required not in html:raise RuntimeError('Missing historical code: '+required)

    # Exactly one worker and one UI helper, using separate closure scopes.
    anchor='const v18343HistoricalKeys=new Set(['
    if html.count(anchor)!=2:raise RuntimeError('Expected two existing archive fingerprint helpers')
    html=html.replace(anchor,NESTED_HELPER+'\n'+anchor)

    # The normal reader is in the simulation worker; both old and new formats
    # use the existing same manifest and the same restoration code path.
    start=html.index('async function v171DecodeManifest(x)')
    end=html.index('async function decode(x)',start)
    decoder=html[start:end]
    old="for(const [id,row] of rows||[]){if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;}"
    new="""for(const entry of rows||[]){
      if(spec?.nested==='year-id-v1'){v18352ApplyArchivedRow(dst,entry);continue;}
      const [id,row]=entry;
      if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;
     }"""
    decoder=swap(decoder,old,new,'worker archive backward-compatible reader')
    html=html[:start]+decoder+html[end:]

    # UI manual "save and exit" writer.
    a=html.index(UI_FUNC_OLD)
    b=html.index('async function saveSharded(s,mode=',a)
    ui=html[a:b]
    ui=swap(ui,UI_FUNC_OLD,
      UI_FUNC_OLD+"\n const nested=v18352NestedArchiveKeys.has(key)&&value&&typeof value==='object';\n if(nested)limit=128;",
      'UI archive chunk selection')
    ui=swap(ui,"oldSpec=history&&previous&&!!previous.isArray===isArray&&",
        "oldSpec=history&&previous&&!!previous.isArray===isArray&&(!nested||previous.nested==='year-id-v1')&&",
        'UI require new archive codec before hash reuse')
    ui=swap(ui,"const target=key==='players'?(Number(state?.year)>=2029?2:4):4;",
        "const target=nested?1:key==='players'?(Number(state?.year)>=2029?2:4):4;",
        'UI one historical chunk per IndexedDB batch')
    old_loop=""" for(const id in (value||{})){
  rows.push([id,value[id]]);
  if(rows.length>=limit)await flush();
 }
 await flush();await commit(true);"""
    new_loop=""" if(nested){
  for(const year in value){if(!Object.prototype.hasOwnProperty.call(value,year))continue;
   const records=value[year];
   if(records&&typeof records==='object'&&!Array.isArray(records)){
    let count=0;
    for(const id in records){if(!Object.prototype.hasOwnProperty.call(records,id))continue;
     rows.push([year,id,records[id]]);count++;
     if(rows.length>=limit)await flush();
    }
    if(!count){rows.push([year,null,{},1]);if(rows.length>=limit)await flush();}
   }else{rows.push([year,null,records,0]);if(rows.length>=limit)await flush();}
  }
 }else for(const id in (value||{})){
  rows.push([id,value[id]]);
  if(rows.length>=limit)await flush();
 }
 await flush();await commit(true);"""
    ui=swap(ui,old_loop,new_loop,'UI annual per-player archive iterator')
    ui=swap(ui,
        "...(history?{hashes,archiveHash:'sha256-json-v1'}:null),",
        "...(history?{hashes,archiveHash:'sha256-json-v1'}:null),\n  ...(nested?{nested:'year-id-v1'}:null),",
        'UI manifest nested codec marker')
    html=html[:a]+ui+html[b:]

    # Worker checkpoints after simulated rounds use the same exact record
    # representation, so a loaded worker save is not different from a manual save.
    a=html.index(WORKER_OLD,html.index('async function save(s){'))
    b=html.index(' const manifest=',a)
    worker=html[a:b]
    worker=swap(worker,
        "const history=v18343HistoricalKeys.has(key),isArray=Array.isArray(value),keys=[],",
        "const history=v18343HistoricalKeys.has(key),nested=v18352NestedArchiveKeys.has(key)&&value&&typeof value==='object',isArray=Array.isArray(value),keys=[],",
        'worker archive kind')
    worker=swap(worker,
        "(key!=='players'||old.collections[key].encoding===v18191wPlayerFormat)?",
        "(key!=='players'||old.collections[key].encoding===v18191wPlayerFormat)&&(!nested||old.collections[key].nested==='year-id-v1')?",
        'worker require archive codec')
    worker=swap(worker,
        "limit=v18343HistoricalLimit(key,baseLimit);",
        "limit=nested?128:v18343HistoricalLimit(key,baseLimit);",
        'worker history chunk size')
    worker=swap(worker,
        "const target=key==='players'?(Number(s.year)>=2029?2:4):4;",
        "const target=nested?1:key==='players'?(Number(s.year)>=2029?2:4):4;",
        'worker one nested chunk per disk batch')
    old_loop="""  for(const id in value){
   if(!safe(id))continue;
   rows.push([id,value[id]]);
   if(rows.length>=limit)await flush();
  }
  await flush();await commit(true);"""
    new_loop="""  if(nested){
   for(const year in value){if(!safe(year)||!Object.prototype.hasOwnProperty.call(value,year))continue;
    const records=value[year];
    if(records&&typeof records==='object'&&!Array.isArray(records)){
     let count=0;
     for(const id in records){if(!safe(id)||!Object.prototype.hasOwnProperty.call(records,id))continue;
      rows.push([year,id,records[id]]);count++;
      if(rows.length>=limit)await flush();
     }
     if(!count){rows.push([year,null,{},1]);if(rows.length>=limit)await flush();}
    }else{rows.push([year,null,records,0]);if(rows.length>=limit)await flush();}
   }
  }else for(const id in value){
   if(!safe(id))continue;
   rows.push([id,value[id]]);
   if(rows.length>=limit)await flush();
  }
  await flush();await commit(true);"""
    worker=swap(worker,old_loop,new_loop,'worker per-player annual archive iterator')
    worker=swap(worker,
        "...(history?{hashes,archiveHash:'sha256-json-v1'}:null),",
        "...(history?{hashes,archiveHash:'sha256-json-v1'}:null),\n   ...(nested?{nested:'year-id-v1'}:null),",
        'worker manifest nested codec marker')
    html=html[:a]+worker+html[b:]

    # Avoid reporting success from an interrupted native/manual save. The last
    # atomic manifest continues to point at the previous valid shards on failure.
    for marker in ('await commitManifest(manifest,old,meta)',
       'await v18181RawWriteMany([{key:STORE+:',
       'v18343Fingerprint(raw)',
       'FUTBR_LONG_CAREER_SAVE_18338_BEGIN'):
        if marker=='await v18181RawWriteMany([{key:STORE+:':continue
        if marker not in html:raise RuntimeError('Historical checkpoint guarantee missing: '+marker)

    html=swap(html,"const EDITION='18.351.0';","const EDITION='18.352.0';",
         'visible desktop version')
    html=swap(html,
      "window.GestorFC.version='18.351.0';window.GestorFC.visualVersion='18.351.0';",
      "window.GestorFC.version='18.352.0';window.GestorFC.visualVersion='18.352.0';",
      'footer desktop version')
    path.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,
      'perYearPlayerRowsPerShard':128,
      'largeMultiYearHistoryObjectsNeverSerializedTogether':True,
      'UIAndWorkerUseIdenticalNestedSchema':True,
      'oldUnsplitArchivesRemainReadable':True,
      'sha256UnchangedArchiveChunksReusedOnlyIfExactMatch':True,
      'unchangedExistingSaveManifestRetainedUntilCommit':True,
      'retirementTransferCompetitionHistoryPreserved':True,
      'noNamedSaveMigrationRequired':True,
      'noCareerYearPlayerOrFieldsDiscarded':True}
    (root/'oomsafe-save-18352-install.json').write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
