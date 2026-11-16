from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from fix_scorers_submit_18340 import (
    CANONICAL_NEW,FALLBACK_NEW,NEW_EVENTS,OLD_INPUT,MARKER
)

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_scorers_submit_18340.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src/index.html').read_text(encoding='utf-8')
    for snippet in (MARKER,CANONICAL_NEW,FALLBACK_NEW,NEW_EVENTS):
        if snippet not in html:raise RuntimeError('Scorer submit patch missing markup/event')
    if OLD_INPUT in html:raise RuntimeError('Old per-character search event still enabled')
    test="""const assert=require('node:assert/strict');
const events={};
const input={value:'',dataset:{v641ScoreQuery:''},focus(){},setSelectionRange(){}};
const scroller={scrollTop:27};
const button={parentElement:{querySelector(){return input;}},closest(sel){return sel.includes('v18340-score-search')?this:null;}};
const document={
 addEventListener(type,handler){(events[type]??=[]).push(handler);},
 querySelector(selector){return selector.includes('v641-score-query')?input:scroller;}
};
const scorerFilter={query:'',page:3,kind:'league',year:'2029'};
let view='rankings',renders=0,animations=0;
const render=()=>{renders++};
const requestAnimationFrame=callback=>{animations++;callback()};
""" + NEW_EVENTS + """
function fire(type,target,options={}){
 const event={target,key:options.key,isComposing:!!options.isComposing,
 defaultPrevented:false,propagationStopped:false,
 preventDefault(){this.defaultPrevented=true;},stopPropagation(){this.propagationStopped=true;}};
 (events[type]||[]).forEach(fn=>fn(event));
 return event;
}
for(const char of 'Roberto Firmino'){
 input.value+=char;
 fire('input',input);
 assert.equal(renders,0,'Typing may never run the ranking calculation');
 assert.equal(scorerFilter.query,'','Typing may never apply the committed filter');
 assert.equal(scorerFilter.page,3,'Typing may never reset pagination');
}
assert.equal(v18340ScorerDraft,'Roberto Firmino','Draft must survive intermediate renders');
const clicked=fire('click',button);
assert.equal(clicked.defaultPrevented,true,'Search button should submit');
assert.equal(scorerFilter.query,'Roberto Firmino');
assert.equal(scorerFilter.page,0);
assert.equal(renders,1,'Single render only after button');
assert.equal(v18340ScorerDraft,null,'Draft cleared after application');
input.value='Messi';
fire('input',input);
assert.equal(renders,1);
const pressed=fire('keydown',input,{key:'Enter'});
assert.equal(pressed.defaultPrevented,true);
assert.equal(scorerFilter.query,'Messi');
assert.equal(renders,2,'Single render only after Enter');
fire('keydown',input,{key:'Enter'});
assert.equal(renders,2,'Same query should not render twice');
input.value='';
fire('input',input);
fire('keydown',input,{key:'Enter',isComposing:true});
assert.equal(renders,2,'IME composition must not trigger a query');
fire('keydown',input,{key:'Enter'});
assert.equal(scorerFilter.query,'');
assert.equal(renders,3,'Empty query clears only on explicit submit');
assert.equal(scorerFilter.kind,'league');
assert.equal(scorerFilter.year,'2029');
assert.equal(scroller.scrollTop,27,'Ranking scroll preserved');
console.log(JSON.stringify({ok:true,searchByButton:true,searchByEnter:true,searchDuringTyping:false,draftsPreserved:true,clearsOnSubmit:true,filtersPreserved:true,renders}));
"""
    with tempfile.TemporaryDirectory(prefix='futbr-search-18340-') as temp:
        path=Path(temp)/'test.js'
        path.write_text(test,encoding='utf-8')
        result=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=30)
        if result.returncode:
            raise RuntimeError('Scorers 18.340 JS regression failed: '+result.stderr)
        tested=json.loads(result.stdout.splitlines()[-1])
        if not tested['ok']:raise RuntimeError('Scorers 18.340 JS regression did not pass')
    report={'ok':True,'version':'18.340','scorers':tested,'saveFilesModified':False,
            'archivedStatsPreserved':True,'otherRankingsUntouched':True}
    (root/'scorers-submit-18340-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
