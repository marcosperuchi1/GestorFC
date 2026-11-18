from __future__ import annotations
import json
import sys
from pathlib import Path

VERSION='18.346'
MARK='FUTBR_DELEGATED_RETIREMENT_18346'
# This is read at rollover *after* s.year increment; the vacation began in the previous year.
# The completed counter is cleared after the annual reset, so a stale selection alone
# does not put an actively managed squad under delegated control the following year.
DELEGATED="""!!(s?.vacation?.delegateTransfers&&(
    s.vacation.active||
    Number(s.vacation.completed)>0||
    s.vacation.untilSeason||
    Number(s.vacation.startYear)===Number(s.year)-1
  ))"""

def replace_once(src,old,new,label):
    n=src.count(old)
    if n!=1:raise RuntimeError(f'{label}: expected 1 anchor, got {n}')
    return src.replace(old,new,1)

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_retirement_vacation_18346.py <project>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src/index.html'
    html=path.read_text(encoding='utf-8')
    if MARK in html:raise RuntimeError('18.346 retirement patch installed twice')
    # Core v5.49 decides retirement for AI clubs, but explicitly blocks the
    # user club even during delegated vacations. Keep human agency otherwise.
    old="function shouldAutoRetire549(s,p,m={},chance=retirementChance549(s,p,m),roll=null){if(!p||p.squad==='youth'||p.clubId===s.user||chance<=0)return false;const r=roll==null?rng(s):Number(roll);return r<chance;}"
    new="""/* FUTBR_DELEGATED_RETIREMENT_18346: delegated vacation and finite playing career */
function v18346DelegatedRetirement(s){return """+DELEGATED+""";}
function shouldAutoRetire549(s,p,m={},chance=retirementChance549(s,p,m),roll=null){
 if(!p||p.squad==='youth')return false;
 const age=Number(p.age)||0,ceiling=p.pos==='GOL'?47:45;
 // Allow outstanding veterans to play longer, but never indefinitely.
 if(age>=ceiling)return true;
 if(age<35||chance<=0)return false;
 const userClub=p.clubId===s?.user&&s?.userEmployed!==false;
 if(userClub&&!v18346DelegatedRetirement(s))return false;
 const r=roll==null?rng(s):Number(roll);
 return r<chance;
}"""
    html=replace_once(html,old,new,'5.49 auto retirement gate')
    # v4 (legacy) path and v9.1 (authoritative) each have an additional
    # human-club veto before calling shouldAutoRetire549.
    old="const clubBefore=p.clubId,protectedByUser=clubBefore===s.user;"
    new="const clubBefore=p.clubId,protectedByUser=clubBefore===s.user&&s.userEmployed!==false&&!v18346DelegatedRetirement(s);"
    html=replace_once(html,old,new,'v4 retirement protected club')
    old="const retireChance=p.squad!=='youth'&&!protectedByUser?retirementChance549(s,p,seasonSnapshot):0;"
    new="const retireChance=p.squad!=='youth'&&(!protectedByUser||Number(p.age)>=(p.pos==='GOL'?47:45))?retirementChance549(s,p,seasonSnapshot):0;"
    html=replace_once(html,old,new,'v4 retirement chance early gate')
    old="protectedByUser=!!(s.userEmployed&&clubBefore===s.user);v91UpdateMarketReputation(p);"
    new="protectedByUser=!!(s.userEmployed&&clubBefore===s.user&&!("+DELEGATED+"));v91UpdateMarketReputation(p);"
    if old not in html:
        import re
        start=html.find('function v91ResetPlayers(s,oldYear)')
        snippet=html[max(0,start):start+2300] if start>=0 else ''
        print('V91_18346_DIAG',repr(snippet[:2300]))
        for match in list(re.finditer('protectedByUser',html))[-5:]:
            print('GUARD_18346_DIAG',match.start(),repr(html[max(0,match.start()-130):match.start()+290]))
    html=replace_once(html,old,new,'v91 retirement protected club')
    old="if(!manual&&p.squad!=='youth'&&!protectedByUser&&Number(p.age)>=35){try{const chance=E.retirementChance549?E.retirementChance549(s,p,snap):0;auto=!!(E.shouldAutoRetire549&&E.shouldAutoRetire549(s,p,snap,chance));}catch(e){auto=false;}}"
    new="if(!manual&&p.squad!=='youth'&&(!protectedByUser||Number(p.age)>=(p.pos==='GOL'?47:45))&&Number(p.age)>=35){try{const chance=E.retirementChance549?E.retirementChance549(s,p,snap):0;auto=!!(E.shouldAutoRetire549&&E.shouldAutoRetire549(s,p,snap,chance));}catch(e){auto=false;}}"
    html=replace_once(html,old,new,'v91 active retirement gate')
    # The general help page still says human-club players "never" auto retire.
    old="Jogadores do seu clube nunca são aposentados automaticamente. A partir dos 35 anos, abra a ficha do atleta e use <b>Aposentar ao fim da temporada</b>; a decisão pode ser cancelada antes da virada do ano."
    new="No seu clube, a IA também avalia aposentadorias durante férias com compras e vendas delegadas. Idade, desempenho e desgaste influenciam a decisão, e atletas em excelente fase podem continuar até mais tarde. A carreira tem limite de 45 anos para jogadores de linha e 47 para goleiros. A partir dos 35 anos, você também pode anunciar uma aposentadoria manualmente e cancelar antes da virada."
    if old in html:html=replace_once(html,old,new,'in-game help text')
    old="Jogadores do seu clube podem anunciar a aposentadoria a partir de 35 anos; aos 40 anos ou mais também poderão se aposentar automaticamente."
    new="Jogadores a partir de 35 anos podem anunciar a aposentadoria. Durante férias com gestão de compras e vendas delegada, a IA também avalia a aposentadoria considerando idade, desgaste e desempenho; há limite excepcional de carreira (45 anos para jogadores de linha e 47 para goleiros)."
    if old in html:html=replace_once(html,old,new,'retirement manager help text')
    path.write_text(html,encoding='utf-8')
    report={
      'ok':True,'version':VERSION,
      'delegateTransfersRetirementIntegrated':True,
      'noDelegationKeepsHumanControlUntilCareerCeiling':True,
      'aiAgePerformanceFatigueGoalkeeperBalancePreserved':True,
      'fieldPlayersAge45Ceiling':True,'goalkeepersAge47Ceiling':True,
      'otherAiTeamsRemainEligible':True,
      'existingManualRetirementPreserved':True,
      'retirementArchivePreserved':True,
      'annualRosterReplenishmentUnchanged':True,
      'noSaveMigrationRequired':True
    }
    (root/'retirement-vacation-18346-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
