from pathlib import Path
import sys,json,time
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_vacation_resume_browser_18369 import HOOK,browser_path
root=Path(sys.argv[1]);html=(root/'src/index.html').read_text()
a=html.index('let state=null,saved=null');b=html.index('</script>',a);anchor=html.rfind('})();',a,b)
probe=r'''
window.__repeat371={done:false,result:null,progress:[],
 snapshot(){return {day:state?.day,user:state?.user,employed:state?.userEmployed,vacation:state?.vacation,
 sim:{active:v53Sim.active,starting:v53Sim.starting,finished:!!v53Sim.finished,syncing:v53Sim.syncing,patching:v53Sim.patching,session:v53Sim.session,mode:v53Sim.mode,progress:v53Sim.progress},
 incoming:!!v125VacIncoming,creating:v53Creating,save:!!v52SavePromise,rpc:v53RPC.size,advance:v18326AdvanceBusy,
 season:!!v18119SeasonTransfer?.active,seasonPreparation:!!v18121NewSeasonPreparation,
 roll168:!!v168RolloverRunning,roll91:!!v91RolloverActive,
 vacPromise:!!v18359VacationPromise,vacOrigin:!!v18362VacationOrigin,
 usable:v18363CanUseJobWait(),blocker:v18363LastBlocker,
 lifecycle:window.GestorFC.lifecycle18362.status(),handoff:window.GestorFC.jobHandoff18365.status(),
 pending:v18112Dismissal.pending,notices:window.__vacResume369.notices.slice(-6)}} ,
 start(){
 const initial=window.__vacResume369.makeCareer();state.vacation.active=false;
 const original=v53StartSimulation;let rounds=0;
 v53StartSimulation=async function(mode,...args){const out=await original(mode,...args);if(mode==='dayfast'&&++rounds>=2)v89JobWait.stop=true;return out;};
 (async()=>{try{
  for(let cycle=1;cycle<=3;cycle++){
   const club=E.team(state,state.user),coach=state.coaches[state.userCoachId];
   const division=state.teams.filter(t=>t.country===club.country&&Number(t.division)===Number(club.division));
   club.stats.pts=Math.min(...division.filter(t=>t.id!==club.id).map(t=>Number(t.stats.pts)))-10;
   state.allowUserDismissal=true;coach.jobGames=20;coach.pressure=100;coach.recent=Array(10).fill(0);coach.lastTitleDay=-100;
   E.startVacation(state,24,false);this.progress.push({stage:'start-vacation',cycle,snapshot:this.snapshot()});
   await v53StartSimulation('vacation',{liveStateNoPreSave:true});
   const afterVacation=this.snapshot();this.progress.push({stage:'after-vacation',cycle,snapshot:afterVacation});
   if(state.userEmployed!==false)throw Error('No dismissal in cycle '+cycle);
   if(!afterVacation.usable)throw Error('Job wait disabled in cycle '+cycle+': '+afterVacation.blocker);
   rounds=0;const before=Number(state.day);await v89RunJobWait();
   this.progress.push({stage:'after-jobwait',cycle,advanced:Number(state.day)-before,rounds,snapshot:this.snapshot()});
   if(rounds<1)throw Error('No actual job-search round in cycle '+cycle);
   if(cycle<3){
    const jobs=E.availableJobs(state).filter(t=>t.id!==state.user);if(!jobs.length)throw Error('No next job');
    const t=jobs.find(t=>state.schedule.slice(Number(state.day),Number(state.day)+20).some(d=>d.type==='league'&&d.fixtures?.some(f=>f.home===t.id||f.away===t.id)))||jobs[0];
    E.takeJob(state,t.id);this.progress.push({stage:'new-job',cycle,team:t.id,snapshot:this.snapshot()});
   }
  }
  this.result={ok:true,initial,progress:this.progress};
 }catch(e){this.result={ok:false,error:String(e),stack:String(e.stack),progress:this.progress,snapshot:this.snapshot()};}
 finally{v53StartSimulation=original;this.done=true;}})();return initial;
 }};
'''
html=html[:anchor]+'\n'+HOOK+'\n'+probe+'\n'+html[anchor:]
with sync_playwright() as p:
 br=p.chromium.launch(executable_path=browser_path(),headless=True,args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
 page=br.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/*',lambda r:r.fulfill(status=200,content_type='text/html; charset=utf-8',body=html) if r.request.resource_type=='document' else r.abort())
 page.goto('http://localhost:8744',wait_until='domcontentloaded',timeout=180000)
 page.wait_for_function('()=>!!window.__repeat371',timeout=90000)
 page.wait_for_timeout(2000)
 print('INITIAL',json.dumps(page.evaluate('()=>window.__repeat371.start()')),flush=True)
 for i in range(80):
  page.wait_for_timeout(5000)
  x=page.evaluate('()=>({done:window.__repeat371.done,progress:window.__repeat371.progress.map(x=>({stage:x.stage,cycle:x.cycle,day:x.snapshot?.day,usable:x.snapshot?.usable,blocker:x.snapshot?.blocker,advanced:x.advanced})),snapshot:window.__repeat371.snapshot()})')
  print('PROGRESS',json.dumps({'done':x['done'],'progress':x['progress'],'snapshot':{k:v for k,v in x['snapshot'].items() if k!='vacation'}}),flush=True)
  if x['done']:break
 result=page.evaluate('()=>window.__repeat371.result')
 if not result:result={'ok':False,'timeout':True,'progress':x,'errors':errors}
 result['errors']=errors
 (root/'career-transitions-browser-18371-tests.json').write_text(json.dumps(result,indent=2))
 print('RESULT',json.dumps(result),flush=True)
 br.close()
 if not result.get('ok'):sys.exit(1)
