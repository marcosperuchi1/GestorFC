"""Behavioral regression against the complete production Engine, not a model."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


TEST = r'''
const assert=require('node:assert/strict');
function club(id,levels=5){return {id,name:'Clube '+id,country:'bra',division:1,base:73,balance:3000000000,capacity:30000,ticket:35,
 trainingLevel:levels,youthLevel:levels,medicalLevel:levels,training:'balanced',sponsor:'balanced',roster:[],academy:[],ledger:[],stats:{form:['E','E','E'],p:3,w:0,d:3,l:0},tactics:{formation:'4-3-3'}};}
function athlete(id,clubId,age=20,ovr=60){return {id,clubId,name:'Atleta '+id,pos:'MEI',age,skills:{att:ovr,def:ovr,pas:ovr,pace:ovr,gk:ovr},potential:90,wage:10000,fitness:60,injury:0,xp:0,seasonGain:0,seasonStartOverall:ovr,stamina:65,attributes:{stamina:65},morale:80,contract:3,ratingHistory:[]};}
function fixture(){const s={seed:374,year:2028,day:153,user:'A',userEmployed:true,userCoachId:'me',live:null,vacation:{active:false},teams:[club('A'),club('B',1)],players:{},free:[],news:[],schedule:Array.from({length:154},()=>({type:'league',fixtures:[]})),difficulty:'normal',nextId:20};
 for(const t of s.teams){const p=athlete('p'+t.id,t.id);s.players[p.id]=p;t.roster=[p.id];}return s;}
function reload(s){return JSON.parse(JSON.stringify(s));}
const E=Engine;
let s=fixture(),t=E.human(s);
assert.equal(Object.keys(E.managementAreas18374).length,8);assert.equal(Object.keys(E.managementPlans18374).length,4);
assert.equal(E.facilityLevel18374(t,'training'),5);
const quote=E.managementQuote18374(s,t,'training');
assert.equal(quote.target,6);assert.equal(quote.max,false);assert.equal(quote.reason,'');
assert.equal(t.management18374,undefined,'reading the management screen must not rewrite old clubs');
const legacyFinancial={};for(const key of ['training','youth','medical'])assert.equal(E.facilityStrength18374(t,key),5);
let durationTotal=0,costTotal=0,lastCost=0,lastDuration=0;
for(let level=5;level<12;level++){const old={...t,trainingLevel:level},q=E.managementQuote18374(s,old,'training');
 assert.ok(q.cost>lastCost&&q.duration>lastDuration);durationTotal+=q.duration;costTotal+=q.cost;lastCost=q.cost;lastDuration=q.duration;}
assert.ok(durationTotal>200);assert.ok(costTotal>1000000000,'top facilities need a sustained financial commitment');
const balance=t.balance;E.upgrade(s,'training','A');
assert.equal(t.trainingLevel,5,'no instant benefit');assert.equal(t.balance,balance-quote.cost);assert.equal(t.management18374.projects.length,1);
assert.equal(t.management18374.projects[0].remaining,quote.duration);
assert.throws(()=>E.upgrade(s,'training','A'),/andamento/);assert.equal(t.balance,balance-quote.cost);
E.upgrade(s,'medical','A');assert.throws(()=>E.upgrade(s,'commercial','A'),/Duas obras/);
assert.throws(()=>E.upgrade(s,'youth','B'),/clube mudou/);
const beforeTick=reload(s),beforeFinances=t.balance;
E.__managementTest.stageFinances(s,t,false);
assert.equal(t.management18374.projects[0].remaining,quote.duration-1);
const firstFinanceBalance=t.balance,firstLedger=JSON.stringify(t.ledger);
E.__managementTest.stageFinances(s,t,false);
assert.equal(t.balance,firstFinanceBalance,'a repeated finance pass cannot charge twice');
assert.equal(JSON.stringify(t.ledger),firstLedger);assert.equal(t.management18374.projects[0].remaining,quote.duration-1);
s=reload(s);t=E.human(s);
E.__managementTest.stageFinances(s,t,false);assert.equal(t.balance,firstFinanceBalance,'finance stamp survives a reload');
s.year=2029;s.day=0;
E.__managementTest.stageFinances(s,t,false);assert.equal(t.management18374.projects[0].remaining,quote.duration-2,'new year advances despite resetting day');
const cancel=t.management18374.projects.find(p=>p.type==='medical'),costPaid=cancel.cost,remaining=cancel.remaining,total=cancel.total,beforeCancel=t.balance;
const refund=E.cancelProject18374(s,cancel.id,'A');assert.equal(refund,Math.floor(costPaid*remaining/total*.85));assert.equal(t.balance,beforeCancel+refund);assert.equal(t.medicalLevel,5);
assert.throws(()=>E.cancelProject18374(s,cancel.id,'A'),/terminou ou foi cancelado/);assert.equal(t.balance,beforeCancel+refund);
// Project ownership is the club, not the currently employed manager.
s.user='B';assert.equal(E.facilityLevel18374(E.human(s),'training'),1);
while(t.management18374.projects.length){s.day++;E.__managementTest.stageFinances(s,t,false);}
assert.equal(t.trainingLevel,6);assert.equal(E.human(s).trainingLevel,1);
const completedLevel=t.trainingLevel;E.__managementTest.stageFinances(s,t,false);assert.equal(t.trainingLevel,completedLevel);
s=reload(s);t=E.team(s,'A');assert.equal(t.trainingLevel,6);assert.equal(t.management18374.projects.length,0);
// Reject invalid funds, actions and injected facility keys without changing money.
s.user='A';const funds=t.balance;t.balance=0;assert.throws(()=>E.upgrade(s,'commercial','A'),/Caixa insuficiente/);assert.equal(t.balance,0);t.balance=funds;
for(const type of ['__proto__','constructor','not-an-area'])assert.throws(()=>E.upgrade(s,type,'A'));
s.live={};assert.throws(()=>E.upgrade(s,'commercial','A'),/partida/);s.live=null;
s.userEmployed=false;assert.throws(()=>E.upgrade(s,'commercial','A'),/Assuma/);s.userEmployed=true;
s.vacation.active=true;assert.throws(()=>E.upgrade(s,'commercial','A'),/simulação/);s.vacation.active=false;
s.v640National={userTeam:'BRA'};assert.throws(()=>E.upgrade(s,'commercial','A'),/seleções/);delete s.v640National;
s.coaches={me:{clubId:'B'}};assert.throws(()=>E.upgrade(s,'commercial','A'),/comando/);delete s.coaches;
const finiteBalance=t.balance;t.balance=NaN;assert.throws(()=>E.upgrade(s,'commercial','A'),/caixa/);t.balance=finiteBalance;
assert.throws(()=>E.setManagementPlan18374(s,'invalid','A'),/inválido/);
// Existing large stadiums must never lose seats. Existing 65k stadiums can grow.
t.capacity=65000;const stadium=E.managementQuote18374(s,t,'stadium');assert.equal(stadium.max,false);assert.equal(stadium.level,7);assert.equal(stadium.extraSeats,7000);
E.upgrade(s,'stadium','A');while(t.management18374.projects.length){s.day++;E.__managementTest.stageFinances(s,t,false);}assert.equal(t.capacity,72000);assert.equal(E.facilityLevel18374(t,'stadium'),8);
t.capacity=150000;assert.equal(E.managementQuote18374(s,t,'stadium').max,true);assert.equal(E.facilityLevel18374(t,'stadium'),12);assert.equal(t.capacity,150000);
t.trainingLevel=12;assert.throws(()=>E.upgrade(s,'training','A'),/concluída/);assert.equal(E.facilityStrength18374(t,'training'),6.75);
// Real stageFinances pays the commercial benefit and charges the new upkeep.
const plain=fixture(),invested=fixture(),a=E.human(plain),b=E.human(invested);
E.management18374(b).levels.commercial=12;
E.__managementTest.stageFinances(plain,a,false);E.__managementTest.stageFinances(invested,b,false);
const sponsor=x=>x.ledger.find(l=>l.category==='Patrocínio e comercial').amount;
assert.ok(Math.abs(sponsor(b)/sponsor(a)-1.22)<.00001);
const maintenance=x=>-x.ledger.find(l=>l.category==='Manutenção').amount;
assert.equal(maintenance(b)-maintenance(a),11*45000);
// Actual attendance functions (normal and turbo) use the supporter investment.
const demand=fixture(),dt=E.human(demand),opp=E.team(demand,'B');dt.base=60;opp.base=60;
const attendanceBefore=E.attendance(demand,dt,opp),turboBefore=E.__managementTest.v33TurboAttendance(demand,dt,opp);
E.management18374(dt).levels.supporters=12;
const attendanceAfter=E.attendance(demand,dt,opp),turboAfter=E.__managementTest.v33TurboAttendance(demand,dt,opp);
assert.ok(attendanceAfter>attendanceBefore);assert.ok(turboAfter>turboBefore);assert.ok(attendanceAfter<=dt.capacity*.98);
// The real per-match XP function applies analysis without changing ability caps.
function performance(level){const f=fixture(),t=E.human(f);E.management18374(t).levels.analytics=level;
 const m={events:[{type:'goal',pid:'pA'}],sides:[{id:'A',lineup:[],starting:[],minutes:{pA:80},goals:2},{id:'B',lineup:[],starting:[],minutes:{},goals:0}]};
 E.performanceDevelopment58(f,m);return {xp:f.players.pA.performanceXP58,ovr:E.overall(f.players.pA),cap:E.growthCap18123(f,f.players.pA)};}
const xp1=performance(1),xp12=performance(12);assert.ok(Math.abs(xp12.xp/xp1.xp-1.165)<1e-9);assert.equal(xp1.ovr,xp12.ovr);assert.equal(xp1.cap,xp12.cap);
// Scouting improves only future mission configuration; premium concurrency is untouched.
const scout=E.managementScout18374({management18374:{levels:{scouting:12}}},{level:2,name:'Profissional',target:10,accuracy:92});
assert.equal(scout.target,5);assert.equal(scout.accuracy,97.5);assert.equal(scout.level,2);
// Medical facilities and selected plans flow through the actual recovery routine.
const medical=fixture(),mt=E.human(medical),mp=medical.players.pA;
const medical5=E.__managementTest.recoveryAmount(medical,mt,mp,true);mt.medicalLevel=12;
const medical12=E.__managementTest.recoveryAmount(medical,mt,mp,true);assert.ok(Math.abs(medical12-medical5-2.1)<1e-9);
E.setManagementPlan18374(medical,'performance','A');assert.ok(Math.abs(E.__managementTest.recoveryAmount(medical,mt,mp,true)-medical12-1.5)<1e-9);
const upkeepPerformance=E.managementUpkeep18374(medical,mt);E.setManagementPlan18374(medical,'economy','A');
assert.ok(E.managementUpkeep18374(medical,mt)<upkeepPerformance);assert.equal(E.managementDevelopment18374(mt,mp),.92);
E.setManagementPlan18374(medical,'development','A');assert.equal(E.managementDevelopment18374(mt,{age:20}),1.1);assert.equal(E.managementDevelopment18374(mt,{age:29}),.95);
// Original training and academy routines still enforce player potential.
function training(level,plan='balanced'){const f=fixture(),t=E.human(f);t.trainingLevel=level;E.setManagementPlan18374(f,plan,'A');
 E.__managementTest.trainAndRecover(f,t,true);return f.players.pA.xp;}
assert.ok(training(12)>training(5));assert.ok(training(12)<training(5)*1.3);
assert.ok(Math.abs(training(5,'development')/training(5)-1.1)<1e-9);
function academy(level){const f=fixture(),t=E.human(f),p=athlete('young','A',17,40);p.squad='youth';p.v577YouthInitialOVR=40;f.players.young=p;t.academy=['young'];t.youthLevel=level;
 E.academyTrain(f,t);return p.development;}
assert.ok(academy(12)>academy(5));assert.ok(academy(12)<academy(5)*1.3);
// Construction needs only the existing club: no player/history/world scan.
const noWorld=fixture();E.upgrade(noWorld,'training','A');const noWorldClub=E.human(noWorld);delete noWorld.players;
Object.defineProperty(noWorld,'players',{get(){throw Error('Unexpected world scan');}});E.tickManagement18374(noWorld,noWorldClub);
const worldDate=fixture();E.upgrade(worldDate,'medical','A');const worldTeam=E.human(worldDate),worldProject=worldTeam.management18374.projects[0],worldBefore=worldProject.remaining;
worldDate.schedule[worldDate.day].type='world';E.__managementTest.trainAndRecover(worldDate,worldTeam,false);assert.equal(worldProject.remaining,worldBefore-1);
E.__managementTest.stageFinances(worldDate,worldTeam,false);assert.equal(worldProject.remaining,worldBefore-1,'recovery and finance passes share a progress stamp');
const malformed=fixture(),malformedTeam=E.human(malformed);malformedTeam.management18374={levels:{},projects:[null,{type:'__proto__',remaining:2},{}]};
E.__managementTest.stageFinances(malformed,malformedTeam,false);assert.ok(Number.isFinite(malformedTeam.balance));
console.log(JSON.stringify({ok:true,fullProductionEngineExecuted:true,eightAreasAndTwelveLevels:true,legacyLevelFivePreserved:true,
 multiSeasonProgression:{trainingFromFiveToTwelveJornadas:durationTotal,trainingFromFiveToTwelveCost:costTotal},
 constructionNotInstant:true,twoConcurrentProjectsEnforced:true,paymentExactlyOnce:true,financeAndProgressIdempotent:true,
 seasonBoundaryAndReloadPreserved:true,worldAndNationalDatesAdvanceProjects:true,clubOwnershipAcrossManagerChanges:true,cancellationRefundAndNoDoubleRefund:true,
 insufficientFundsAndInvalidActionsRejected:true,stadiumCapacityPreserved:true,boundedMedicalTrainingAndYouthEffects:true,
 actualCommercialAndSupporterEffects:true,actualPerformanceLearningEffect:true,scoutFutureMissionImprovement:true,
 fourManagementPlansHaveTradeoffs:true,noExtraWorldScan:true,potentialAndGrowthCapsPreserved:true}));
'''


def main():
    root=Path(sys.argv[1]).resolve();source=(root/'src/index.html').read_text(encoding='utf-8')
    assert 'FUTBR_CLUB_MANAGEMENT_18374' in source
    assert 'FUTBR_CLUB_MANAGEMENT_UI_18374' in source
    assert 'TEST_ONLY_CLUB_MANAGEMENT_18374' not in source
    start=source.index('const Engine = (() => {')
    end=source.index("if(typeof module!=='undefined'&&module.exports)module.exports=Engine;",start)
    engine=source[start:end]
    anchor='managementAreas18374:MANAGEMENT18374,'
    assert engine.count(anchor)==1
    engine=engine.replace(anchor,'__managementTest:{stageFinances,recoveryAmount,trainAndRecover,v33TurboAttendance},'+anchor,1)
    js='const WorldCatalog={countries:[],clubs:[]},BundledRosters={};\n'+engine+'\n'+TEST
    with tempfile.TemporaryDirectory(prefix='futbr-management-374-') as td:
        path=Path(td)/'test.js';path.write_text(js,encoding='utf-8')
        run=subprocess.run(['node',str(path)],text=True,capture_output=True,timeout=90)
    if run.returncode:raise RuntimeError(run.stderr[-9000:])
    result=json.loads(run.stdout.strip().splitlines()[-1]);result.update(version='18.374.0',
        sourceSha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),testHooksNotShipped=True)
    (root/'club-management-18374-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
