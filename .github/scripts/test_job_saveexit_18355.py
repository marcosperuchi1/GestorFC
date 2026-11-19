from __future__ import annotations
import json,re,subprocess,sys,tempfile
from pathlib import Path
def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_job_saveexit_18355.py <project>')
    root=Path(sys.argv[1])
    html=(root/'src/index.html').read_text(encoding='utf-8')
    assert 'FUTBR_JOB_SAVE_EXIT_18355' in html
    def section(start,end):
        a=html.index(start);b=html.index(end,a)
        return html[a:b]
    job=section('function availableJobs(s){','function takeJob(s,id){')
    offers=section('function v636GenerateCoachOffer(s,afterUserMatch=false){','function v636CoachOfferModal(')
    save=section('async function ensureSaved(){','async function archiveCurrent(')
    assert 'roundsFree>=8' in job and 'else return [];' not in job
    assert 'yearsFree>0?' in offers and 'v636CreateCoachOffer' in offers
    assert 'Promise.race' in save and '90000' in save and 'clearTimeout(v18355Timer)' in save
    assert 'if(!matches(x)||!saveOK||v52SaveDirty||v52SavePromise)' in save
    assert "String(x.root?.v1903CareerId||'')===String(state.v1903CareerId||'')" in save
    assert 'Number(x.year)===Number(state.year)' in save
    prelude=r"""
const assert=require('assert');
function team(s,id){return s.teams.find(t=>t.id===id)}
function country(){return {confederation:'CONMEBOL'}}
function v636CoachState(s){s.v636CoachOfferMeta??={rejected:{},lastOfferDay:-99};s.v636CoachOffers??=[]}
function v636PendingCoachOffers(s){return s.v636CoachOffers.filter(x=>x.year===s.year&&x.expiresDay>=s.day)}
function v636CleanCoachOffers(s){v636CoachState(s);s.v636CoachOffers=v636PendingCoachOffers(s)}
function v636CreateCoachOffer(s,t,why){s.v636CoachOffers.push({teamId:t.id,year:s.year,expiresDay:s.day+4});return true}
function v636OfferHash(){return 0}
const E={availableJobs,clamp:(v,lo,hi)=>Math.min(hi,Math.max(lo,v)),team,strength:(s,t)=>t.base,sum:a=>a.reduce((x,y)=>x+y,0)};
function v636ClubOVR(s,t){return t?.base||0}
"""
    tests=r"""
function runScenario(oldDay,newDay,pressure){
 const s={year:2031,day:newDay,user:'old',userEmployed:false,userCoachId:'me',schedule:Array(38),
 teams:[{id:'old',base:70,division:1,country:'BRA',fanPressure:0,coachId:'ai'},
 {id:'new',base:68,division:1,country:'BRA',fanPressure:pressure,coachId:'ai2'}],
 coaches:{me:{id:'me',reputation:75,unemployedSince:{year:2030,day:oldDay}}},
 v636CoachOffers:[],v636CoachOfferMeta:{rejected:{},lastOfferDay:-99}};
 assert.equal(availableJobs(s).length,1,'Unemployed coach must have eligible same-level prospects');
 assert.equal(v636GenerateCoachOffer(s,false),1,'New season must generate job offer');
 assert.equal(s.v636CoachOffers[0].teamId,'new');
}
runScenario(37,1,50);
runScenario(48,1,10);
const same={year:2030,day:1,user:'old',userEmployed:false,userCoachId:'me',schedule:Array(38),
teams:[{id:'old',base:70,division:1,country:'BRA',coachId:'ai'},
{id:'new',base:65,division:1,country:'BRA',fanPressure:60,coachId:'ai2'}],
coaches:{me:{id:'me',reputation:70,unemployedSince:{year:2030,day:0}}},
v636CoachOffers:[],v636CoachOfferMeta:{rejected:{}}};
assert.equal(v636GenerateCoachOffer(same,false),0,'Do not offer before two actual rounds');
console.log(JSON.stringify({ok:true,crossSeason:true,longTermUnemployed:true,minimumWait:true,saveWatchdog:true}));
"""
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/'test.cjs'
        file.write_text(prelude+'\n'+job+'\n'+offers+'\n'+tests,encoding='utf-8')
        check=subprocess.run(['node',str(file)],capture_output=True,text=True,timeout=25)
        if check.returncode:raise RuntimeError(check.stderr[-4500:])
        report=json.loads(check.stdout.strip().splitlines()[-1])
    (root/'job-save-exit-18355-tests.json').write_text(json.dumps({**report,'version':'18.355.0','checkpointYearDayVerified':True,'doesNotInterruptInFlightSave':True},indent=2),encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':main()
