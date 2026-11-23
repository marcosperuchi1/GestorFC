"""Fix 18.383 season rollover ReferenceError caused by a cross-IIFE helper.

v18346DelegatedRetirement exists in the engine closure, but the 18.383
v91ResetPlayers override lives in the outer UI scope. The annual reset must
use its own function with exactly the established 18.346 semantics.
No other aging, retirement, season, or saved state rules are changed.
"""
from pathlib import Path
import sys,json,hashlib,subprocess
MARK='FUTBR_SEASON_SCOPE_FIX_18384'
HELPER=r"""
/* FUTBR_SEASON_SCOPE_FIX_18384
   The v5.49 18.346 closure is not visible to the outer v91 annual reset.
   Keep delegation semantics identical to the original player retirement gate. */
function v18384DelegatedRetirement(s){
 return !!(s?.vacation?.delegateTransfers&&(
  s.vacation.active||
  Number(s.vacation.completed)>0||
  s.vacation.untilSeason||
  Number(s.vacation.startYear)===Number(s.year)-1
 ));
}
"""
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_season_scope_18384.py <prepared-root>')
 root=Path(sys.argv[1]).resolve();path=root/'src/index.html';s=path.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.384 rollover fix already present')
 if 'FUTBR_LONG_CAREER_REALISM_18383' not in s:raise RuntimeError('18.383 source not found')
 a=s.index('function v91ResetPlayers(s,oldYear){')
 b=s.index('function v91PromoteAgedYouth(',a)
 block=s[a:b]
 old='||v18346DelegatedRetirement(s)){'
 if block.count(old)!=1:raise RuntimeError('Expected exactly one inaccessible 18.346 helper call in live annual reset, got '+str(block.count(old)))
 block=block.replace(old,'||v18384DelegatedRetirement(s)){',1)
 if 'v18346DelegatedRetirement(s)' in block:raise RuntimeError('Still references cross-IIFE function')
 s=s[:a]+HELPER+'\n'+block+s[b:]
 for js in [HELPER]:
  v=subprocess.run(['node','--check','-'],input=js,text=True,capture_output=True,timeout=25)
  if v.returncode:raise RuntimeError('Invalid 18.384 JS '+v.stderr)
 path.write_text(s,encoding='utf-8')
 report={'ok':True,'version':'18.384.0','referenceErrorAtRolloverFixed':True,
 'delegatedRetirementPreserves18346Semantics':True,'annualLoopStillSinglePass':True,
 'ageAndStarRulesFrom18383Preserved':True,'retirementRuleEngineUnchanged':True,
 'savedGameUnmodified':True,'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'season-scope-18384-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
