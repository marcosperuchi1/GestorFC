"""Validate AI market position caps and non-destructive pre-season transfers."""
from pathlib import Path
import json,hashlib,subprocess,sys
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_roster_balance_18384.py <prepared-root>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 a=s.index('/* FUTBR_AI_ROLE_BALANCE_18384')
 b=s.index('  function aiMarket(s){',a)
 js=s[a:b]
 market=s[b:s.index('  // 5.85: reposicao garantida',b)]
 for word in ['v18384BalanceAiSquads(s)','needsFor(buyer).filter(x=>x.n<v18384RoleMax(s,buyer,x.pos))',
              'executeTransfer(s,best.p.id','s.v18384RebalancedSeason']:
  if word not in market+js:raise RuntimeError('Market guard missing '+word)
 setup=r"""
const assert=require('node:assert/strict');
const ROLES=['GOL','ZAG','LAT','VOL','MEI','ATA'];
const FORMATIONS={'4-3-3':['GOL','ZAG','ZAG','LAT','LAT','VOL','MEI','MEI','ATA','ATA','ATA']};
const player=(s,id)=>s.players[id]||null,overall=p=>Number(p.ovr)||65,value=p=>p.ovr*40000;
const payroll=(s,t)=>t.roster.reduce((sum,id)=>sum+(s.players[id]?.wage||0),0);
const seniorTarget=(s,t)=>28;
const squadRolePlan=(s,t)=>({req:{GOL:2,ZAG:4,LAT:4,VOL:2,MEI:3,ATA:3}});
const salaryDemand58=p=>p.wage;
const signingCost58=()=>10000;
const autoLineup=(s,t)=>{t.lineup=t.roster.slice(0,11)};
const log=[];
const executeTransfer=(s,id,from,to,fee,wage,years)=>{
 const p=s.players[id];assert(from.roster.includes(id),'Source ownership required');
 assert(p.clubId===from.id);
 from.roster=from.roster.filter(x=>x!==id);
 to.roster.push(id);p.clubId=to.id;p.wage=wage;p.contract=years;
 from.balance+=fee;to.balance-=fee;
 s.transfers.unshift({year:s.year,day:s.day,id,from:from.id,to:to.id,pos:p.pos,fee});
 log.push({id,from:from.id,to:to.id,pos:p.pos});
};
let next=0;
const players={};
function make(role,club,ovr=70,star=false){
 const id='p'+(++next);
 players[id]={id,name:'Player'+next,pos:role,clubId:club.id,star,
  squad:'senior',ovr,wage:1500,contract:3,age:26,honors538:[{key:'cup:ger',year:2032}]};
 club.roster.push(id);return id;
}
const ip={id:'ips',name:'Ipswich Town',country:'eng',base:71,division:1,
 balance:120000000,roster:[],lineup:[]};
for(let i=0;i<9;i++)make('GOL',ip,70+i);
for(let i=0;i<6;i++)make('ZAG',ip,72+i);
for(let i=0;i<5;i++)make('LAT',ip,71+i);
for(let i=0;i<5;i++)make('VOL',ip,70+i);
for(let i=0;i<3;i++)make('MEI',ip,70+i);
for(let i=0;i<7;i++)make('ATA',ip,73+i);
ip.lineup=ip.roster.slice(0,11);
const buyers=[];
for(let j=0;j<8;j++){
 const b={id:'buyer'+j,name:'Buyer '+j,country:'eng',division:1,
  balance:110000000,base:71,roster:[],lineup:[]};
 for(let i=0;i<(j===0?1:2);i++)make('GOL',b,67+i);
 for(let i=0;i<4;i++)make('ZAG',b,69+i);
 for(let i=0;i<4;i++)make('LAT',b,69+i);
 for(let i=0;i<4;i++)make('VOL',b,69+i);
 for(let i=0;i<4;i++)make('MEI',b,69+i);
 for(let i=0;i<5;i++)make('ATA',b,69+i);
 b.lineup=b.roster.slice(0,11);buyers.push(b);
}
const own={id:'user',name:'Liverpool',country:'eng',base:90,division:1,
 balance:500000000,roster:[],lineup:[]};
for(let i=0;i<9;i++)make('GOL',own,87);
for(let i=0;i<22;i++)make(['ZAG','LAT','VOL','MEI','ATA'][i%5],own,80);
const state={year:2043,day:0,user:'user',userEmployed:true,
 transfers:[],teams:[ip,...buyers,own],players};
const originalPlayerCount=Object.keys(players).length;
const userRoster=own.roster.slice();
const honorsBefore=JSON.stringify(Object.fromEntries(Object.values(players).map(p=>[p.id,p.honors538])));
"""
 checks=r"""
const moved=v18384BalanceAiSquads(state);
assert(moved>=5&&moved<=160,'A club with 9 GKs should redistribute most excess players');
const count=v18384RosterCount(state,ip);
assert.equal(count.GOL,3,'Ipswich Town cannot retain 9 GKs if destinations have capacity');
for(const buyer of buyers)assert(v18384RosterCount(state,buyer).GOL<=3,'No buyer may overfill GK');
assert.deepEqual(own.roster,userRoster,'Human roster must not be altered');
assert.equal(Object.keys(state.players).length,originalPlayerCount,'No players created or deleted');
assert.equal(JSON.stringify(Object.fromEntries(Object.values(players).map(p=>[p.id,p.honors538]))),
 honorsBefore,'Historical player titles must remain intact');
for(const t of state.teams)for(const id of t.roster){
 assert.equal(state.players[id]?.clubId,t.id,'Every roster/player ownership consistent');
}
assert.equal(state.transfers.length,moved,'All moves recorded through real transfer engine');
const prev=JSON.stringify(state.transfers),countOld=state.v18384RosterBalance.transfers;
assert.equal(v18384BalanceAiSquads(state),0,'Rerunning same season is idempotent');
assert.equal(JSON.stringify(state.transfers),prev);
assert(v18384RoleMax(state,ip,'GOL')===3);
assert(v18384RoleMin(state,ip,'MEI')>=4);
assert(v18384RoleMin(state,ip,'ATA')>=4);
assert(state.v18384RosterBalance.surplusListed>=6);
console.log(JSON.stringify({ok:true,version:'18.384.0',goalkeepersReducedFromNineToThree:true,
 destinationCapThreeKeepers:true,shortagePositionsPrioritized:true,
 realTransfersPersisted:true,userManagedRosterProtected:true,
 noPlayersGeneratedOrRemoved:true,honorsUntouched:true,
 marketRunOncePerSeason:true,maximumTransferBatchBounded:true,
 moved,positions:count}));
"""
 f=root/'roster-balance-18384-fixture.cjs';f.write_text(setup+'\n'+js+'\n'+checks,encoding='utf-8')
 out=subprocess.run(['node',str(f)],text=True,capture_output=True,timeout=50)
 try:f.unlink()
 except OSError:pass
 if out.returncode:raise RuntimeError('Production market balance regression: '+out.stderr[-4000:])
 report=json.loads(out.stdout.strip().splitlines()[-1])
 report['sourceSha256']=hashlib.sha256(s.encode('utf-8')).hexdigest()
 (root/'roster-balance-18384-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
