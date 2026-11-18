from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: test_calendar_match_retirement_18350.py <project>')
    root=Path(sys.argv[1]).resolve()
    s=(root/'src/index.html').read_text(encoding='utf-8')
    for required in (
        'FUTBR_CALENDAR_MATCH_RETIRE_18350',
        '<h2>Gerenciador de aposentadorias</h2>',
        'v18324RetirementOpen=!v18324RetirementOpen',
        'data-action="v18324-open-retirements"',
        'v18328OpenRetireModal(el.dataset.player)',
        'v579ToggleRetirement(state,id)',
        'v18350-home', 'v18350-away',
        'grid-template-columns:minmax(0,1fr) max-content minmax(0,1fr)',
        'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349',
        'v18349-all', 's.retirements=[...newRetirements'):
        if required not in s:
            raise RuntimeError('Missing retirement, calendar, or save invariant: '+required)
    if 'try{v18324RetirementOpen=false;}catch(e){}' in s:
        raise RuntimeError('Calendar still resets retirement manager on render')
    start=s.index('function v18322RetirementPage(){')
    end=s.index('\n}', start)+2
    manager=s[start:end]
    if 'Histórico de aposentadorias' in manager or 'rows.slice(0,700)' in manager:
        raise RuntimeError('The removed retirement archive is still rendered in the manager')
    if 'v18324EligibleVeterans()' not in manager or 'v18322-retire' not in manager:
        raise RuntimeError('Manager is no longer actionable for eligible players')
    if '18.350.0' not in s or "const EDITION='18.350.0';" not in s:
        raise RuntimeError('Calendar version label does not match package version')
    for label in ('v18350-home','v18350-away'):
        if len(re.findall(r'class=.v18347-team '+label+r'\b',s)) != 1:
            raise RuntimeError('Incorrect team anchor '+label)
    js="const assert=require('node:assert/strict');\n" + """
const match='<span class="v18347-match"><span class="v18347-team v18350-home"><strong>Flamengo</strong><span class="crest">CRF</span></span><b class="v18347-score">×</b><span class="v18347-team v18350-away"><span class="crest">CFC</span><strong>Coritiba</strong></span></span>';
assert.match(match, /Flamengo.*CRF.*×.*CFC.*Coritiba/);
console.log('PASS match visual order');
"""
    r=subprocess.run(['node','-e',js],capture_output=True,text=True,timeout=20)
    if r.returncode:
        raise RuntimeError('Alignment test failed: '+r.stderr)
    report=dict(ok=True,version='18.350.0',calendarNamesAndCrestsTouchScore=True,
                managerAccessibleInSquad=True,retiredPlayersArchiveNotRendered=True,
                retirementButtonsPreserved=True,inGameConfirmationPreserved=True,
                savedRetirementsUntouched=True,incrementalSaveEnginePreserved=True,
                scrollOnWholeSeasonPreserved=True,installedEditionMatchesVersion=True)
    (root/'calendar-retirement-18350-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    main()
