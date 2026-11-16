from pathlib import Path
import json, re, subprocess, sys, tempfile

def main():
    source=Path(__file__).with_name("feature_champions_retirement_18322.py").read_text(encoding="utf-8")
    match=re.search(r'function v18322InitClubFilters\(force=false\)\{[\s\S]*?\n\}', source)
    if not match:
        raise RuntimeError("Contextual history initializer missing")
    if "if(el.dataset.mode==='history')v18322InitClubFilters(true)" not in source:
        raise RuntimeError("History click does not refresh current competition context")
    code=r'''
const assert=require('node:assert/strict');
const state={name:'same career'};
let v54CompetitionMode='league',v4Competition='lib',country='bra',division=1;
const selectedCountry=()=>country,selectedDivision=()=>division;
const E={human:()=>({country:'bra',division:1})};
const v18322ClubFilters={country:'all',kind:'all',division:'all',competition:'all',year:'all'};
let v18322VisibleLimit=120,v18322ClubFilterState=null;
''' + match.group(0) + r'''
function verify(mode, c, d, selected, kind){
 v54CompetitionMode=mode;country=c;division=d;
 if(mode==='international')v4Competition=selected;
 v18322InitClubFilters(true);
 assert.equal(v18322ClubFilters.competition,mode==='international'?selected:
  mode==='cup'?'cup:'+c:'league:'+c+':'+d);
 assert.equal(v18322ClubFilters.kind,kind);
 assert.equal(v18322ClubFilters.year,'all');
}
verify('league','bra',1,null,'league');
verify('league','bra',2,null,'league');
verify('league','eng',1,null,'league');
verify('cup','bra',1,null,'cup');
verify('cup','eng',1,null,'cup');
verify('international','bra',1,'lib','international');
verify('international','bra',1,'sud','international');
v18322ClubFilters.competition='manual-user-filter';
v18322InitClubFilters();
assert.equal(v18322ClubFilters.competition,'manual-user-filter','Do not destroy manually selected filters');
v54CompetitionMode='league';country='bra';division=1;
v18322InitClubFilters(true);
assert.equal(v18322ClubFilters.competition,'league:bra:1','Switching back must never retain stale cup or international context');
console.log('PASS: 8 contextual competition scenarios, manual filter persistence and reset on re-open');
'''
    with tempfile.TemporaryDirectory(prefix='futbr-history-context-') as d:
        path=Path(d)/'context.js'
        path.write_text(code,encoding='utf-8')
        test=subprocess.run(['node',str(path)],capture_output=True,text=True)
        if test.returncode:
            raise RuntimeError(test.stderr)
        print(test.stdout.strip())
    print(json.dumps({'ok':True,'version':'18.339','competitionContext':True,
                      'leagueDivision':True,'nationalCups':True,'continentalCups':True,
                      'manualFilterPreserved':True,'staleFilterReset':True}))

if __name__=='__main__':
    main()
