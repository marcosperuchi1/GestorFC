from __future__ import annotations
import json, sys
from pathlib import Path

TERMS = [
 'v18121NewSeasonPreparation',
 'Salvando o calendário da nova temporada',
 'v52SavePromise',
 'v52FlushSave',
 'v53Sim.starting',
 'v53Sim.progress',
 'v53StartVacation',
 'v53StartVac',
 'startVacation',
 'beginVacation',
 'v53WorkerReady',
 "v53Call('save'",
 'v53Creating',
 'await saveSharded',
 "mode==='employment'",
 'async function saveSharded',
 'function v53PaintStatus',
 'function v53Start',
 'function v18121',
 'v169NextSeason',
 'v169Season',
 'v18121NewSeason',
 'function v18311',
]
def main():
 if len(sys.argv)!=2:raise SystemExit("usage: diagnose_new_season_vacation_18311.py <project-dir>")
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 results={}
 total=0
 for term in TERMS:
  found=[]; pos=0
  while len(found)<9:
   i=html.find(term,pos)
   if i<0:break
   pos=i+len(term)
   start=max(0,i-2500);end=min(len(html),i+4500)
   snippet=html[start:end]
   found.append({'pos':i,'snippet':snippet})
  results[term]=found
  if found:
   print(f'=== {term}: {len(found)} matches shown ===',flush=True)
   for h in found:
    total+=1
    print(f"POSITION {h['pos']}\\n{h['snippet']}\\n-----",flush=True)
 report=root/'new-season-vacation-18311-diagnostic.json'
 report.write_text(json.dumps({'terms':results,'totalSnippets':total},ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Snippets: {total}, report={report}',flush=True)
 if not results['v18121NewSeasonPreparation']:raise RuntimeError('New season preparation state missing')
 if 'v18311VacationCheckpointFix' not in html:raise RuntimeError('Hotfix 18.311 not installed: diagnostic-only run, do not build')
if __name__=='__main__':main()
