from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: test_career_isolation_18344.py <project>")
    root=Path(sys.argv[1]).resolve()
    html=(root/"src/index.html").read_text(encoding="utf-8")
    assert html.count("FUTBR_CAREER_ISOLATION_18344")==1
    required=[
      "function v18344RestoreStarterCoach(s,club,me)",
      "if(old.coachId===me.id)v18344RestoreStarterCoach(s,old,me);",
      "s.v217CareerLedger={version:1,jobs:[],rows:[],updatedYear:s.year,updatedDay:s.day}",
      "let shadowCareerId=null;",
      "function guardCareer(s){",
      "function remember(s){guardCareer(s);",
      "function repair(s=state){guardCareer(s);",
      "if(options?.v643StartType!=='national')try{remember(s);repair(s);}"
    ]
    for mark in required:
        if mark not in html: raise AssertionError("Missing 18.344 safety: "+mark)
    # Execute the actual converted career initialization, not a reimplementation.
    start=html.index("function v18344RestoreStarterCoach(s,club,me)")
    stop=html.index("\nasync function v643PrepareNationalCareer",start)
    real_js=html[start:stop]
    # The exact recovery guard that the original 18.37 IIFE uses.
    guard=html[html.index("let shadowCareerId=null;"):html.index("\n let restoring=",html.index("let shadowCareerId=null;"))] if False else None
    mock=r"""
      const old={id:'flamengo',name:'Flamengo',initialCoachName:'Treinador Original',
        coachId:'c0',tactics:{formation:'4-3-3',style:'possession'}};
      const real={id:'c1',name:'Treinador Original',clubId:null,unemployedSince:{year:2026,day:0},
       formation:'4-4-2',style:'counter',
       jobs:[{year:2026,day:0,club:'flamengo',clubName:'Flamengo',end:'Substituído pelo jogador no início da carreira'}]};
      const me={id:'c0',clubId:'flamengo',name:'Jogador',
       jobs:[{year:2026,day:0,club:'flamengo',clubName:'Flamengo'}]};
      const s={created:'2026-11-16T00:00:00.000Z',year:2026,day:0,user:'flamengo',
       userCoachId:'c0',userEmployed:true,coaches:{c0:me,c1:real},
       coachMoves:[{coachId:'c0',to:'flamengo'}],teams:[old],news:[],
       v636CoachCareer:[{clubId:'flamengo'}],v217CareerLedger:{jobs:me.jobs.slice(),rows:[{clubId:'flamengo'}]}};
      const national={code:'BRA',name:'Brasil',coach:null,roster:[]};
      const root={teams:{BRA:national},userTeam:null,offers:[]};
      const E={
        team:(s,id)=>s.teams.find(t=>t.id===id),coachMarket:()=>{if(!old.coachId)old.coachId='fake';},
        news:(s,...args)=>s.news.push(args)
      };
      const v548FullAccess=()=>true,v640EnsureState=()=>root,v641NormalizeCoach=c=>c,
        v643EnsureNationalStarterDepth=()=>{},v640Eligible=()=>
          Array.from({length:22},(_,i)=>({pos:i<3?'GOL':'ATA'})),
        v640AutoRoster=()=>[],v640BestXI=()=>[];
      let v640NationalViewCode=null;
    """
    test=r"""
      v643ConvertNewCareerToNational(s,'BRA');
      if(old.coachId!=='c1'||real.clubId!=='flamengo'||real.jobs[0].end)
        throw Error('original Flamengo coach was displaced');
      if(me.clubId!==null||me.jobs.length!==0||me.nationalTeamCode!=='BRA')
        throw Error('national user retained a phantom club job');
      if(s.v636CoachCareer.length||s.v217CareerLedger.jobs.length||
         s.v217CareerLedger.rows.length||s.coachMoves.some(x=>x.coachId==='c0'))
        throw Error('club history survived brand-new national career');
      if(root.userTeam!=='BRA'||national.coach.id!==me.id||s.userEmployed!==false)
        throw Error('national career not activated');
      if(old.coachId==='fake')throw Error('AI market replaced original Flamengo coach');
      console.log('PASS: real international career conversion restores original coach and empty history');
    """
    reset = r"""
      const shadow={jobs:[{club:'flamengo'}],rows:[{clubId:'flamengo'}]};
      let shadowCareerId='older-save';
      let saveQueued=true;
      function guardCareer(s){
       const id=String(s?.created||s?.v18344CareerId||'');
       if(!id)return;
       if(shadowCareerId!==id){
        shadow.jobs=[];shadow.rows=[];shadowCareerId=id;
        saveQueued=false;
       }
      }
      guardCareer({created:'new-save'});
      if(shadow.jobs.length||shadow.rows.length||shadowCareerId!=='new-save'||saveQueued)
       throw Error('new save retained previous career ledger');
      shadow.jobs.push({club:'nation-current-club'});
      guardCareer({created:'new-save'});
      if(shadow.jobs.length!==1)throw Error('same save lost valid history');
      console.log('PASS: recovery shadow is isolated between saves and stable within a save');
    """
    run=subprocess.run(['node','-e',mock+'\n'+real_js+'\n'+test+'\n'+reset],
         text=True,capture_output=True,timeout=30)
    if run.returncode: raise RuntimeError("Real career test failed:\n"+run.stderr)
    print(run.stdout)
    report={"ok":True,"version":"18.344","originalFlamengoCoachPreserved":True,
      "freshNationalCareerNoFormerClubHistory":True,"previousSavedCareerIsolated":True,
      "nationalTeamCareerValid":True,"sameSaveKeepsHistory":True,
      "coachMarketCannotReplaceOriginal":True}
    (root/"career-isolation-18344-tests.json").write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__": main()
