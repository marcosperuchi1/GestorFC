"""Balance AI team squads in real market with signed, audited transfers.

- No forced sale/release from the user club.
- Limit buyer positions; especially never allow a fourth goalkeeper.
- Use existing executeTransfer() so fees, ownership, transfer histories and
  season statistics remain consistent.
- Only one bounded 160-deal pre-season balancing pass per season, performed
  through existing market code. Never clone s.players.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
MARK='FUTBR_AI_ROLE_BALANCE_18384'
JS=r"""
/* FUTBR_AI_ROLE_BALANCE_18384
   One bounded yearly AI window, all transactions through executeTransfer.
   Existing saves get their first pass on the next market pulse. */
function v18384RoleMin(s,t,pos){
 const r=squadRolePlan(s,t).req||{};
 return pos==='MEI'?Math.max(4,r.MEI||3):
  pos==='ATA'?Math.max(4,r.ATA||3):
  pos==='VOL'?Math.max(3,r.VOL||2):
  Math.max(2,Number(r[pos])||2);
}
function v18384RoleMax(s,t,pos){
 const min=v18384RoleMin(s,t,pos);
 return pos==='GOL'?3:pos==='ZAG'?Math.max(6,min+1):
  pos==='LAT'?Math.max(5,min+1):pos==='VOL'?Math.max(5,min+1):
  pos==='MEI'?Math.max(6,min+1):Math.max(7,min+1);
}
function v18384RosterCount(s,t){
 const count={GOL:0,ZAG:0,LAT:0,VOL:0,MEI:0,ATA:0};
 for(const id of t.roster||[]){const p=player(s,id);if(p&&Object.hasOwn(count,p.pos))count[p.pos]++;}
 return count;
}
function v18384BalanceAiSquads(s){
 if(!s||Number(s.v18384RebalancedSeason)===Number(s.year))return 0;
 // Keep user-owned club entirely under human control, even on vacation.
 const teams=(s.teams||[]).filter(t=>t&&t.id!==s.user&&t.roster?.length>=15);
 const counts=new Map(),requests=Object.fromEntries(ROLES.map(pos=>[pos,[]])),
  supply=Object.fromEntries(ROLES.map(pos=>[pos,[]]));
 let listed=0,transferred=0;const touched=new Set();
 for(const t of teams){
  const c=v18384RosterCount(s,t);counts.set(t.id,c);
  for(const pos of ROLES){
   const n=c[pos]||0,min=v18384RoleMin(s,t,pos),max=v18384RoleMax(s,t,pos);
   const desired=pos==='GOL'?3:min;
   if(n<desired&&t.balance>800000&&(t.roster?.length||0)<37){
    requests[pos].push({t,needed:Math.min(3,desired-n),depth:desired-n});
   }
   if(n<=max||t.roster.length<=19)continue;
   const lineup=new Set((t.lineup||[]).filter(Boolean));
   const surplus=(t.roster||[]).map(id=>player(s,id)).filter(p=>
     p&&p.pos===pos&&!p.star&&!p.injury&&
     !(p.lastTransfer?.year===s.year&&
       s.day-(Number(p.lastTransfer.day)||0)<12))
    .sort((a,b)=>Number(lineup.has(a.id))-Number(lineup.has(b.id))||
       overall(a)-overall(b));
   let available=Math.min(6,n-max);
   for(const p of surplus){
    if(available<=0)break;
    if(!p.listed){p.listed=true;listed++;}
    supply[pos].push({p,seller:t});
    available--;
   }
  }
 }
 // Those with deepest shortages first. Keep this bounded, as the market
 // already runs sophisticated transfer waves throughout the new season.
 for(const pos of ROLES)requests[pos].sort((a,b)=>b.depth-a.depth||
   Number(b.t.base||0)-Number(a.t.base||0));
 outer:for(const pos of ['MEI','ATA','LAT','VOL','ZAG','GOL']){
  const stock=supply[pos];
  if(!stock?.length)continue;
  for(const req of requests[pos]){
   const buyer=req.t;
   if(transferred>=160)break outer;
   while(req.needed>0&&transferred<160){
    let match=-1,score=-Infinity;
    for(let i=0;i<stock.length;i++){
     const x=stock[i],p=x?.p,seller=x?.seller;
     if(!p||p.clubId!==seller.id||seller.id===buyer.id)continue;
     const fromCount=counts.get(seller.id);
     if(!fromCount||fromCount[pos]<=v18384RoleMax(s,seller,pos))continue;
     const quality=overall(p),strength=Number(buyer.base)||60;
     if(quality<Math.max(30,strength-23)||quality>strength+18)continue;
     const proposed=Math.max(30000,Math.round(value(p)*.23/1000)*1000);
     const wages=Number(p.wage)||0;
     if(proposed+signingCost58(p,seller,proposed)>
         Number(buyer.balance||0)*.28||wages>
         Math.max(6000,payroll(s,buyer)*.20))continue;
     const local=String(seller.country||'')===String(buyer.country||'')?12:0;
     const q=local-Math.abs(quality-strength)*1.5-
       proposed/Math.max(1,buyer.balance)*12;
     if(q>score){score=q;match=i;}
     if(q>11)break; // A strong local fit; avoid scanning entire world.
    }
    if(match<0)break;
    const x=stock[match],p=x.p,seller=x.seller;
    const fee=Math.max(30000,Math.round(value(p)*.23/1000)*1000);
    const wage=Math.max(Number(p.wage)||500,
      Math.ceil(salaryDemand58(p)*.93/100)*100);
    try{
     const previous=s.currentTradeReason;
     s.currentTradeReason='Reequilíbrio de posições: '+pos;
     try{executeTransfer(s,p.id,seller,buyer,fee,wage,Math.max(2,Number(p.contract)||3));}
     finally{
      if(typeof previous==='undefined')delete s.currentTradeReason;
      else s.currentTradeReason=previous;
     }
     counts.get(seller.id)[pos]--;
     counts.get(buyer.id)[pos]++;
     req.needed--;transferred++;
     touched.add(seller.id);touched.add(buyer.id);
     stock.splice(match,1);
    }catch(_e){
     stock.splice(match,1); // A refused transfer must not block the whole season.
    }
   }
  }
 }
 // Only squads actually affected by transfers need a lineup refresh.
 for(const t of teams)if(touched.has(t.id))try{autoLineup(s,t);}catch(_e){}
 s.v18384RebalancedSeason=Number(s.year);
 s.v18384RosterBalance={year:s.year,transfers:transferred,
  surplusListed:listed,reviewedClubs:teams.length,roleCapGK:3};
 return transferred;
}
"""
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: balance_ai_rosters_18384.py <prepared-root>')
 root=Path(sys.argv[1]);p=root/'src/index.html';s=p.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.384 role balancing applied twice')
 if 'FUTBR_LONG_CAREER_REALISM_18383' not in s:raise RuntimeError('Missing previously signed source')
 a=s.rfind('  function aiMarket(s){')
 if a<0:raise RuntimeError('Authoritative 17.2 market function missing')
 b=s.index('  // 5.85: reposicao garantida',a)
 block=s[a:b]
 before="  function aiMarket(s){\n    if(!s.transfers)return;"
 if not block.startswith(before):raise RuntimeError('Live AI market declaration changed; abort release')
 block=block.replace(before,
  "  function aiMarket(s){\n    if(!s.transfers)return;\n    if(Number(s.v18384RebalancedSeason)!==Number(s.year))v18384BalanceAiSquads(s);",1)
 old='const bigCenter=isBigCenter(buyer),needs=needsFor(buyer),saleNeed='
 if block.count(old)!=1:raise RuntimeError('Cannot find current needs selection exactly once')
 block=block.replace(old,
  'const bigCenter=isBigCenter(buyer),needs=needsFor(buyer).filter(x=>x.n<v18384RoleMax(s,buyer,x.pos)),saleNeed=',1)
 if 'executeTransfer(s,best.p.id' not in block:raise RuntimeError('Original automated transfer path changed')
 s=s[:a]+JS+'\n'+block+s[b:]
 out=subprocess.run(['node','--check','-'],input=JS,text=True,capture_output=True,timeout=30)
 if out.returncode:raise RuntimeError('Role balancing JS syntax '+out.stderr[-2500:])
 p.write_text(s,encoding='utf-8')
 report={'ok':True,'version':'18.384.0','aiSquadRoleBalancingEnabled':True,
 'goalkeeperPurchasesCappedAtThree':True,'meiasAndStrikersPrioritized':True,
 'surplusPlayersListedForSale':True,
 'surplusMovesUsingExistingTransferEngine':True,
 'humanManagedClubNotModified':True,
 'oncePerSeasonBounded160Moves':True,'positionCacheOnlyNoWholeWorldClone':True,
 'lineupsRefreshedOnlyWhenMoved':True,'saveAndPlayerHistoryUnchanged':True,
 'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'roster-balance-18384-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
