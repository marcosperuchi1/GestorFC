"""Add career-aware sporting-fit checks to manual player purchases."""
from __future__ import annotations
import json,sys,hashlib
from pathlib import Path

MARK='FUTBR_TRANSFER_INTEREST_18375'
ENGINE=r'''
  /* FUTBR_TRANSFER_INTEREST_18375
     A high salary alone cannot buy every footballer. This is a pure function:
     it changes no world object and makes no full-roster or history scan. */
  function transferInterest18375(s,p,destination,origin,offeredWage){
    if(!p||!destination)return {ok:false,reason:'Jogador ou clube indisponível.'};
    const strengthPlayer=overall(p),prestige=Math.max(1,Number(destination.base)||50),
      division=Math.max(1,Number(destination.division)||1),
      sourcePrestige=Number(origin?.base)||strengthPlayer,
      wasListed=!!p.listed,age=Math.max(15,Number(p.age)||25),
      deficit=Math.max(0,strengthPlayer-prestige),
      downgrade=Math.max(0,sourcePrestige-prestige),
      star=!!p.star||strengthPlayer>=85,
      salaryReference=Math.max(500,Number(p.wage)||500),
      ratio=Math.max(0,Number(offeredWage)||0)/salaryReference,
      expensiveButRealistic=Math.min(8,Math.max(0,ratio-1)*3),
      divisionPenalty=Math.max(0,division-1)*9;
    // Hard sporting mismatch: even a huge salary cannot bypass it.
    if(star&&(deficit>=13||(division>=2&&deficit>=8)))
      return {ok:false,reason:'O jogador considera a reputação e a divisão do clube incompatíveis com sua carreira.'};
    if(division>=3&&strengthPlayer>=78&&deficit>=7)
      return {ok:false,reason:'O jogador prefere competir em uma divisão superior.'};
    if(!wasListed&&age<=31&&downgrade>=19&&deficit>=11)
      return {ok:false,reason:'O jogador não deseja trocar seu clube atual por um projeto esportivo muito inferior.'};
    // Moderate opportunities account for wages, quality, age and club status.
    // A listed veteran is more open than an unlisted prospect.
    const interest=clamp(75-deficit*3-divisionPenalty-downgrade*.8+
      (wasListed?12:0)+(age>=33?9:0)+expensiveButRealistic,0,98);
    // Deterministic across retry / reload; user cannot reset the outcome by
    // repeatedly clicking purchase on the same career, day and player.
    let hash=2166136261;const seed=[s.v1903CareerId||s.seed||'',s.year,s.day,p.id,destination.id].join('|');
    for(let i=0;i<seed.length;i++){hash^=seed.charCodeAt(i);hash=Math.imul(hash,16777619);}
    const draw=(hash>>>0)%100;
    if(draw>=interest)
      return {ok:false,reason:'O jogador recusou o projeto esportivo. Reputação, divisão e perspectivas de carreira pesaram na decisão.'};
    return {ok:true,reason:'',interest,draw};
  }

'''
def main():
 root=Path(sys.argv[1]).resolve();path=root/'src/index.html';s=path.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('Already installed')
 anchor='  function buy(s,id,bid,wage,years){'
 if s.count(anchor)!=1:raise RuntimeError('Unexpected buy function')
 s=s.replace(anchor,ENGINE+anchor,1)
 start=s.index(anchor);end=s.index('  function saleOffer(s,id)',start)
 buy=s[start:end]
 validity="if(!Number.isFinite(bid)||!Number.isFinite(wage)||!Number.isFinite(years)||bid<0||wage<500||years<1||years>5||years%1)throw Error('Proposta inválida.');"
 if buy.count(validity)!=1:raise RuntimeError('Cannot find offer input guard')
 buy=buy.replace(validity,validity+"\n    const sportingFit18375=transferInterest18375(s,p,t,from,wage);if(!sportingFit18375.ok)throw Error(sportingFit18375.reason);",1)
 s=s[:start]+buy+s[end:]
 export='return {jobMarketStamp18374,'
 if s.count(export)!=1:raise RuntimeError('Cannot find Engine exports')
 s=s.replace(export,'return {transferInterest18375,jobMarketStamp18374,',1)
 path.write_text(s,encoding='utf-8')
 (root/'transfer-interest-18375-install.json').write_text(json.dumps({'ok':True,'version':'18.375-candidate','sourceSha256':hashlib.sha256(s.encode()).hexdigest(),'checksBeforeTransfer':True,'neverClonesWorld':True},indent=2),encoding='utf-8')
if __name__=='__main__':main()
