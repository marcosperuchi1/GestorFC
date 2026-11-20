from __future__ import annotations
import json,sys
from pathlib import Path
import test_unemployed_real_browser_18368 as real

# Exercise the actual original 18.370 Engine and Worker in a browser with
# IndexedDB. The patched job-search code deliberately terminates its Worker
# after a durable checkpoint, so this test accepts that successful release.
old=real.HOOK
real.HOOK=old.replace(
 'hasRealWorker:!!v53Worker,',
 "hasRealWorker:!!v53Worker||(window.GestorFC.jobWaitMemory18370?.status?.()?.commits||0)>0,"
).replace(
 'simulationStatus:window.GestorFC.unemployedWorker18368?.status?.()',
 'simulationStatus:window.GestorFC.unemployedWorker18368?.status?.(),'
 'jobMemory:window.GestorFC.jobWaitMemory18370?.status?.()'
)
if real.HOOK==old or 'jobMemory:window.GestorFC' not in real.HOOK:
 raise RuntimeError('Could not instrument original 18.368 real-browser Worker test')

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_jobwait_memory_browser_18370.py <project>')
 root=Path(sys.argv[1])
 real.main()  # Full game bootstrap, actual Worker, 185k+ players and IndexedDB
 source=json.loads((root/'unemployed-browser-18368-tests.json').read_text(encoding='utf-8'))
 result=source.get('result') or {}
 stats=result.get('jobMemory') or {}
 notice=' '.join(result.get('notices') or [])
 passed=bool(source.get('ok') and source.get('originalWorkerExecuted') and
  source.get('twoRealEngineJornadas') and stats.get('commits',0)>=1 and
  stats.get('failed',-1)==0 and stats.get('lastDay')==result.get('after') and
  stats.get('busy') is False and
  'Falha ao salvar' not in notice and
  'não foi salva' not in notice)
 report={'ok':passed,'version':'18.370.0',
  'actualEngine':source.get('originalEngineRealBrowser'),
  'actualWorker':source.get('originalWorkerExecuted'),
  'realDayfastJornadas':source.get('twoActualDaysAdvanced'),
  'diskCheckpointConfirmed':stats.get('commits',0)>=1,
  'checkpointMatchesReturnedDay':stats.get('lastDay')==result.get('after'),
  'noCheckpointFailures':stats.get('failed',-1)==0,
  'noConcurrentCheckpoint':stats.get('busy') is False,
  'previousWorkerReleasedAfterStop':not bool((result.get('simulationStatus') or {}).get('workerActive')),
  'days':result.get('after'), 'memory':stats, 'notices':result.get('notices',[])[:8],
  'realBrowserSource':True}
 (root/'jobwait-memory-browser-18370-tests.json').write_text(
  json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('18.370 REAL ENGINE JOB-WAIT MEMORY: '+json.dumps(report,ensure_ascii=False),flush=True)
 if not passed:raise RuntimeError('18.370 actual Engine Worker did not finish with a durable checkpoint')

if __name__=='__main__':main()
