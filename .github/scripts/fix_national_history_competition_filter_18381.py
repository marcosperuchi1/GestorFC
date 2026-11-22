"""FutBR Manager 18.381: one entry per distinct national competition name in historical filters.

Only the national-championship select's option generation and comparison are
changed. Raw historical IDs, winning nations, years and scorer totals stay
unmodified. Prior in-memory selections of a per-edition id are supported.
"""
from pathlib import Path
import hashlib,json,subprocess,sys

MARK='FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381'
HELPERS=r"""
/* FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381 */
function v18381CompetitionLabel(root,entry){
 const id=String(entry?.id||'');
 return String(root?.competitions?.[id]?.name||entry?.name||id).trim();
}
function v18381CompetitionKey(label){
 return String(label||'').normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'')
  .toLocaleLowerCase('pt-BR')
  .replace(/\s+/g,' ').trim();
}
function v18381CompetitionOptions(root,history){
 const unique=new Map();
 for(const record of history||[]){
  const label=v18381CompetitionLabel(root,record),key=v18381CompetitionKey(label);
  if(!key)continue;
  if(!unique.has(key))unique.set(key,{key,label});
 }
 return [...unique.values()].sort((a,b)=>a.label.localeCompare(b.label,'pt-BR'));
}
function v18381CompetitionSelection(root,history,selected){
 const value=String(selected||'all');
 if(value==='all'||value.startsWith('title:'))return value;
 // Compatibility with in-memory filters set by an old game build.
 const old=(history||[]).find(record=>String(record?.id||'')===value);
 return old?'title:'+v18381CompetitionKey(v18381CompetitionLabel(root,old)):value;
}
function v18381CompetitionMatches(root,history,selected,record){
 const value=v18381CompetitionSelection(root,history,selected);
 if(value==='all')return true;
 if(value.startsWith('title:'))
  return v18381CompetitionKey(v18381CompetitionLabel(root,record))===value.slice(6);
 return String(record?.id||'')===value;
}
"""

def change_once(src,old,new,label):
 count=src.count(old)
 if count!=1:raise RuntimeError(label+' expected once, found '+str(count))
 return src.replace(old,new,1)

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_national_history_competition_filter_18381.py <prepared-root>')
 root=Path(sys.argv[1]).resolve()
 path=root/'src/index.html'
 html=path.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('Already installed 18.381 national filter fix')
 for needed in ('FUTBR_CHAMPIONS_RETIREMENT_18322','FUTBR_COACH_HONORS_INLINE_SCORERS_18380',
                'FUTBR_SCORER_IDENTITY_18379'):
  if needed not in html:raise RuntimeError('Missing prior feature '+needed)
 start=html.index('function v18322HistoryPage(kind){')
 end=html.index('function v18322NationalScorers(',start)
 block=html[start:end]
 block=change_once(block,
   "   const options=[...new Set(h.map(x=>String(x.id||'')))].filter(Boolean).sort();",
   "   const options=v18381CompetitionOptions(root,h);\\n   const selection=v18381CompetitionSelection(root,h,f.competition);".replace('\\n','\n'),
   'old options from edition IDs')
 block=change_once(block,
   "(f.competition==='all'||x.id===f.competition)&&",
   "v18381CompetitionMatches(root,h,f.competition,x)&&",
   'old single-edition filter')
 block=change_once(block,
   "v18322Option('all','Todos',f.competition)+options.map(id=>v18322Option(id,root.competitions?.[id]?.name||h.find(x=>x.id===id)?.name||id,f.competition)).join('')+",
   "v18322Option('all','Todos',selection)+options.map(item=>v18322Option('title:'+item.key,item.label,selection)).join('')+",
   'competition options HTML')
 html=html[:start]+HELPERS+'\n'+block+html[end:]
 if html.count(MARK)!=1:raise RuntimeError('Feature marker duplicated')
 jscheck=subprocess.run(['node','--check','-'],input=HELPERS,text=True,capture_output=True,timeout=25)
 if jscheck.returncode:raise RuntimeError('JavaScript syntax regression: '+jscheck.stderr[-2500:])
 path.write_text(html,encoding='utf-8')
 report={
 'ok':True,'version':'18.381.0',
 'uniqueOptionsByNormalizedCompetitionName':True,
 'allHistoricalEditionIdsRetained':True,
 'singleOptionFiltersEveryEdition':True,
 'oldSelectedEditionIdSupported':True,
 'diacriticsAndWhitespaceNormalized':True,
 'namesSortedPtBR':True,
 'nationalHistoryAndGameSavesUnchanged':True,
 'scorersAndChampionsUnchanged':True,
 'sourceSha256':hashlib.sha256(html.encode('utf-8')).hexdigest()}
 (root/'national-history-filter-18381-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
