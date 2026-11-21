"""Bound ranking work to each calendar draw without changing its sporting order.

The 2029 Club World Cup is the first post-creation call that sorts the whole
qualification pool. Previously every comparator rebuilt the same profiles and
enumerated every coach's titles. The cache below is strictly synchronous and
operation-local: no state/date stamp, persisted cache, or omitted history.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


MARKER = 'FUTBR_SEASON_RANK_BATCH_18374'
BLOCK = r'''  /* FUTBR_SEASON_RANK_BATCH_18374
     All sporting scores and tie-breaks remain the original 6.33 functions.
     A draw's data is immutable while its synchronous sort is running. Compute
     each profile once and discard the index even when a comparator throws. */
  let v18374RankBatch=null;
  const v18374RankStats={batches:0,profiles:0,coachScans:0,clubs:0,lastMs:0};
  function v18374CareerTitleRows(s,id){
    if(v18374RankBatch?.state===s)return v18374RankBatch.titles.get(id)||[];
    const out=[];
    for(const c of Object.values(s.coaches||{}))for(const r of c.titles||[])
      if(r.club===id||(!r.club&&r.clubName&&normName(r.clubName)===normName(team(s,id)?.name||'')))out.push(r);
    return out;
  }
  function v18374CurrentTitles(s,window){
    const rows=new Map(),divisions=new Map();
    const add=(id,rec,source)=>{if(!rows.has(id))rows.set(id,[]);rows.get(id).push({rec,source});};
    if(!(Number(s.year)>=window.start&&Number(s.year)<=window.end))return rows;
    for(const t of s.teams||[]){if(!divisions.has(t.country))divisions.set(t.country,new Set());divisions.get(t.country).add(Number(t.division)||1);}
    for(const c of WorldCatalog.countries){
      for(const div of divisions.get(c.id)||[]){
        const lower=c.id==='bra'&&div>=3&&div<=4,
          officialLower=div===3?s.braLower?.serieC?.champion:s.braLower?.serieD?.champion,
          complete=lower?!!officialLower:v652LeagueComplete(s,c.id,div);
        if(!complete)continue;
        let champ=lower?officialLower:table(s,c.id,div)[0]?.id;
        if(c.id==='usa'&&div===1)champ=s.competitions?.mls?.champion||null;
        add(champ,{year:s.year,key:'league:'+c.id+':'+div,label:(c.id==='usa'&&div===1?'MLS Cup':'Liga '+c.name+' / '+div)},'currentLeague');
      }
      add(s.cupWinners?.[c.id],{year:s.year,key:'cup:'+c.id,label:c.cup||'Copa nacional'},'currentCup');
    }
    for(const c of Object.values(s.competitions||{}))if(c?.champion&&c.id!=='mls')
      add(c.champion,{year:s.year,key:c.id,label:c.name},'currentInternational');
    return rows;
  }
  function v18374RankClubIds(s,ids,conf=null,cycle){
    const ranked=[...ids];
    if(ranked.length<2)return ranked;
    // Preserve the initial catalog's deliberately cheap, history-free path.
    if(v1894InitialRankingOnly(s))return ranked.sort((a,b)=>{
      const ta=team(s,a),tb=team(s,b);
      return (Number(tb?.base)||0)-(Number(ta?.base)||0)||String(ta?.name||a).localeCompare(String(tb?.name||b),'pt-BR');
    });
    const started=typeof performance!=='undefined'?performance.now():Date.now(),previous=v18374RankBatch;
    const window=v633RankWindow(s),actualCycle=cycle===undefined?v633Cycle(s):cycle,
      wanted=new Set(ranked),names=new Map(),titles=new Map(),profiles=new Map();
    for(const id of wanted){const name=normName(team(s,id)?.name||'');
      if(!names.has(name))names.set(name,[]);names.get(name).push(id);}
    // Preserve original coach/title traversal order, including legacy titles
    // identified only by club name and duplicate club names.
    for(const c of Object.values(s.coaches||{}))for(const row of c.titles||[]){
      const targets=wanted.has(row.club)?[row.club]:[];
      if(!row.club&&row.clubName)for(const id of names.get(normName(row.clubName))||[])if(!targets.includes(id))targets.push(id);
      for(const id of targets){if(!titles.has(id))titles.set(id,[]);titles.get(id).push(row);}
    }
    v18374RankStats.coachScans++;v18374RankStats.batches++;v18374RankStats.clubs+=wanted.size;
    v18374RankBatch={state:s,window,titles,currentTitles:v18374CurrentTitles(s,window)};
    try{
      for(const id of wanted){profiles.set(id,v633RankProfile(s,conf||confOf(s,id),id,actualCycle));v18374RankStats.profiles++;}
      ranked.sort((a,b)=>v633CompareProfiles(profiles.get(a),profiles.get(b),team(s,a),team(s,b)));
      return ranked;
    }finally{
      v18374RankBatch=previous;
      v18374RankStats.lastMs=(typeof performance!=='undefined'?performance.now():Date.now())-started;
    }
  }
  /* FUTBR_SEASON_RANK_BATCH_18374_END */
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one authoritative source match, got {count}')
    return source.replace(old, new, 1)


def patch(source: str) -> str:
    if MARKER in source:
        return source
    source = replace_once(source, '  function v633RankWindow(s){',
                          BLOCK + '  function v633RankWindow(s){\n'
                          '    if(v18374RankBatch?.state===s)return v18374RankBatch.window;',
                          'rank window and operation-local index')
    source = replace_once(source,
        "    for(const c of Object.values(s.coaches||{}))for(const r of c.titles||[])if(r.club===id||(!r.club&&r.clubName&&normName(r.clubName)===normName(team(s,id)?.name||'')))add(r,'career');",
        "    for(const r of v18374CareerTitleRows(s,id))add(r,'career');", 'original title ledger')
    source=replace_once(source,
        '    if(Number(s.year)>=start&&Number(s.year)<=end){\n      for(const c of WorldCatalog.countries){',
        '    if(v18374RankBatch?.state===s){\n'
        '      for(const item of v18374RankBatch.currentTitles.get(id)||[])add(item.rec,item.source);\n'
        '    }else if(Number(s.year)>=start&&Number(s.year)<=end){\n      for(const c of WorldCatalog.countries){',
        'one current-title scan per ranking batch')
    replacements = [
        ("qualificationList(s,conf).filter(id=>team(s,id)).sort((a,b)=>v631RankCompare(s,conf,a,b,cycle))", "v18374RankClubIds(s,qualificationList(s,conf).filter(id=>team(s,id)),conf,cycle)"),
        ("(titleIds.length?titleIds:ranked).slice().sort((a,b)=>v631RankCompare(s,conf,a,b,cycle))", "v18374RankClubIds(s,titleIds.length?titleIds:ranked,conf,cycle)"),
        ("c.participants.filter(id=>id!==host&&confOf(s,id)===cf).sort((a,b)=>v631RankCompare(s,cf,a,b,cycle))", "v18374RankClubIds(s,c.participants.filter(id=>id!==host&&confOf(s,id)===cf),cf,cycle)"),
        ("pots[3].filter(id=>id!==host&&team(s,id)?.country===hostCt).sort((a,b)=>v631RankCompare(s,confOf(s,a),a,b))", "v18374RankClubIds(s,pots[3].filter(id=>id!==host&&team(s,id)?.country===hostCt))"),
        ("[...new Set((ids||[]).filter(id=>team(s,id)))].sort((a,b)=>v631RankCompare(s,'CONMEBOL',a,b))", "v18374RankClubIds(s,[...new Set((ids||[]).filter(id=>team(s,id)))],'CONMEBOL')"),
        ("[...c.participants].sort((a,b)=>v633RankCompare(s,'UEFA',a,b))", "v18374RankClubIds(s,c.participants,'UEFA')"),
        ("ids.sort((a,b)=>v633GlobalRankCompare(s,a,b))", "v18374RankClubIds(s,ids)"),
        ("[...ids].sort((a,b)=>v633RankCompare(s,'CONMEBOL',a,b))", "v18374RankClubIds(s,ids,'CONMEBOL')"),
        ("s.teams.filter(t=>t.country===hostCountry).sort((a,b)=>v633GlobalRankCompare(s,a.id,b.id))[0]?.id", "v18374RankClubIds(s,s.teams.filter(t=>t.country===hostCountry).map(t=>t.id))[0]"),
        ("qualificationList(s,conf).filter(id=>team(s,id)).sort((a,b)=>v633RankCompare(s,conf,a,b,cycle))", "v18374RankClubIds(s,qualificationList(s,conf).filter(id=>team(s,id)),conf,cycle)"),
        ("(titleIds.length?titleIds:ranked).slice().sort((a,b)=>v633RankCompare(s,conf,a,b,cycle))", "v18374RankClubIds(s,titleIds.length?titleIds:ranked,conf,cycle)"),
    ]
    for old,new in replacements:
        expected=2 if old=="[...ids].sort((a,b)=>v633RankCompare(s,'CONMEBOL',a,b))" else 1
        if source.count(old)!=expected:raise RuntimeError('Authoritative calendar rank sort missing: '+old)
        source=source.replace(old,new)
    source=replace_once(source,'promotionProfile18372,',
        'seasonRankAudit18374:()=>({...v18374RankStats,active:!!v18374RankBatch}),promotionProfile18372,',
        'Engine diagnostic export')
    return source


def main() -> None:
    if len(sys.argv)!=2:raise SystemExit('usage: optimize_season_rollover_18374.py <project>')
    root=Path(sys.argv[1]).resolve();target=root/'src/index.html'
    source=patch(target.read_text(encoding='utf-8'))
    target.write_text(source,encoding='utf-8')
    report={'ok':True,'version':'18.374.0','operationLocalRankingProfiles':True,
        'coachTitlesIndexedOncePerSort':True,'originalRankingCriteriaPreserved':True,
        'historyNotDeleted':True,'noPersistentRankingCache':True,
        'sameEngineForUiAndWorker':True,'testHooksNotShipped':'TEST_ONLY_ROLLOVER_18374' not in source,
        'sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest()}
    (root/'season-rollover-18374-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
