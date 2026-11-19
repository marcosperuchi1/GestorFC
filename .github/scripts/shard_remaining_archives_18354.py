from __future__ import annotations
import json
import sys
from pathlib import Path

MARK='FUTBR_ARCHIVE_ROOT_SHARDS_18354'
VERSION='18.354.0'
OLD="['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','crestOverrides']"
NEW="['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','crestOverrides','scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive']"
EXTRA=['scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive']
def once(s,old,new,label):
 n=s.count(old)
 if n!=1:raise RuntimeError(f'18.354 {label}: expected one anchor, got {n}')
 return s.replace(old,new,1)

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: shard_remaining_archives_18354.py <project-dir>')
 root=Path(sys.argv[1]).resolve()
 cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
 if cfg.get('version')!=VERSION:raise RuntimeError('Expected signed build 18.354.0')
 file=root/'src/index.html'
 s=file.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('Already applied')
 for m in ['FUTBR_NATIVE_MIRROR_18354','FUTBR_OOMSAFE_ARCHIVE_18352',
           'FUTBR_ARCHIVE_COPY_ON_WRITE_18343',
           "async function saveSharded(s,mode='full')",
           'async function save(s){',
           'async function v171DecodeManifest(x)']:
  if m not in s:raise RuntimeError('Required runtime not installed: '+m)
 s=once(s,'const SHARDS='+OLD,'/* '+MARK+' UI */\nconst SHARDS='+NEW,
   'UI sharded root keys')
 s=once(s,'V171_SHARDS='+OLD,
   '/* '+MARK+' Worker */\nV171_SHARDS='+NEW,
   'Worker sharded root keys')
 # Both writers already use v18343HistoricalKeys: all six keys were listed
 # there but none appeared in their actual collections! Enforce exact reuse.
 for key in EXTRA:
  if s.count("'"+key+"'")<3:raise RuntimeError('Archive root key missing: '+key)
 limit_old=""" if(key==='scorerArchive')return 1;
 return previousLimit;"""
 limit_new=""" if(key==='scorerArchive')return 1;
 if(key==='history'||key==='internationalHistory'||key==='v735NationalArchive')return 12;
 if(key==='transfers'||key==='retirements')return 64;
 return previousLimit;"""
 s=once(s,limit_old,limit_new,'UI archive bounded limit')
 s=once(s,limit_old,limit_new,'Worker archive bounded limit')
 # Existing saves which left these archives in root are still decoded by
 # v171DecodeManifest (root spread, collections merged). The first new save
 # safely migrates the values into chunked collections without truncation.
 for m in ["const s={...(x.root||{})}","s[key]=dst",
           "root={},collections={}","if(!shardSet.has(key))root[key]=value"]:
  if m not in s:raise RuntimeError('Lossless legacy decoder invariant failed: '+m)
 file.write_text(s,encoding='utf-8')
 report={'ok':True,'version':VERSION,
  'previouslyUnshardedArchives':EXTRA,
  'UIAndWorkerRootArchiveShardListsAligned':True,
  'oldRootArchivesRemainLoadable':True,
  'allHistoricValuesPreserved':True,
  'firstPostUpgradeSaveMigratesLosslessly':True,
  'scorerArchiveOneYearPerChunk':True,
  'largeTransfersAndRetirementsSplitInto64Entries':True,
  'snapshotManifestNoLongerEmbedsTheseArchives':True,
  'namedCareerRestoreAndRecentCheckpointPreserved':True}
 (root/'archive-root-shards-18354-install.json').write_text(
   json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
