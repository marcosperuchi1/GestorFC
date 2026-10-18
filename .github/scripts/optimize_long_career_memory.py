from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def once(text, old, new, label):
    if old not in text:
        fail(label + ': ancora nao encontrada')
    return text.replace(old, new, 1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: optimize_long_career_memory.py <project-dir>')
    path=Path(sys.argv[1]).resolve()/'src'/'index.html'
    html=path.read_text(encoding='utf-8')

    # 1) Historical collections must not travel inside the monolithic root object.
    old="const SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','crestOverrides'];"
    new="const SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive','crestOverrides'];"
    html=once(html,old,new,'long-career sharded histories')

    # 2) Bound the per-season league-table cache even before rollover.
    old="const rows=v540RawTable(s,c,d);m.set(token,rows.slice());return rows;"
    new="const rows=v540RawTable(s,c,d);m.set(token,rows.slice());if(m.size>48)m.delete(m.keys().next().value);return rows;"
    html=once(html,old,new,'bounded table cache')

    # 3) Keep historical scorer screens useful without retaining thousands of full rows
    # per competition/year. UI shows 150 rows, so retain a safety margin of 180.
    start=html.find('function v94CompactScorerArchive(stats){')
    if start<0: fail('v94CompactScorerArchive ausente')
    end=html.find('\nfunction v94PackCurrentCareerArchive',start)
    if end<0: fail('fim v94CompactScorerArchive ausente')
    compact=r"""function v94CompactScorerArchive(stats){
 const out={};
 for(const [key,rows] of Object.entries(stats||{})){
  const ranked=[];
  for(const [pid,r] of Object.entries(rows||{})){
   const goals=Number(r?.goals)||0,assists=Number(r?.assists)||0,apps=Number(r?.apps)||0,minutes=Number(r?.minutes)||0;
   if(goals<=0&&assists<=0)continue;
   ranked.push({id:r.id||pid,name:r.name||'',natCode:r.natCode||'UNK',real:!!r.real,star:!!r.star,goals,assists,apps,minutes,clubs:r.clubs||{}});
  }
  ranked.sort((a,b)=>b.goals-a.goals||b.assists-a.assists||a.minutes-b.minutes);
  if(ranked.length)out[key]=Object.fromEntries(ranked.slice(0,180).map(r=>[r.id,r]));
 }
 return out;
}"""
    html=html[:start]+compact+html[end:]

    # 4) Avoid allocating a filtered transfers array once for every player while
    # building the annual career archive.
    old="const names={},packed={};\n  const append="
    new="const names={},packed={},lastTransferTo=new Map();for(const m of s.transfers||[])if(Number(m?.year)===Number(year)&&m?.id&&m?.to)lastTransferTo.set(m.id,m.to);\n  const append="
    html=once(html,old,new,'career archive transfer index')
    old="last=(s.transfers||[]).filter(m=>Number(m.year)===Number(year)&&m.id===pid&&m.to).at(-1)?.to||null"
    new="last=lastTransferTo.get(pid)||null"
    html=once(html,old,new,'career archive transfer lookup')

    # 5) Drop known transient state before and after the rollover. These objects can
    # otherwise coexist with the newly-created schedule during peak allocation.
    old="const tNext=performance.now();E.nextSeason(state);v168Stats.nextSeasonMs=performance.now()-tNext;"
    new="v168DropStateCaches(state);v168StopBackground();try{if(typeof v53PatchQueue!=='undefined')v53PatchQueue.length=0;}catch(e){}const tNext=performance.now();E.nextSeason(state);v168Stats.nextSeasonMs=performance.now()-tNext;"
    html=once(html,old,new,'pre-rollover transient purge')

    # 6) v169 is the final rollover authority. Purge caches/workers BEFORE its
    # E.nextSeason call too, otherwise the old derived world can coexist with the
    # freshly-created calendar at the exact peak that caused the OOM.
    old="try{G.v168?.stop?.();}catch(e){}try{G.v100?.repair?.stopBackground?.(true);}catch(e){}"
    new="try{G.v168?.stop?.();G.v168?.purge?.();}catch(e){}try{G.v170?.release?.();}catch(e){}try{G.v100?.repair?.stopBackground?.(true);}catch(e){}"
    html=once(html,old,new,'v169 pre-rollover purge')

    # 7) Expose diagnostics for long-career testing.
    marker="window.GestorFC.v168={"
    if marker not in html: fail('v168 diagnostics ausente')
    diag=r"""
window.GestorFC.longCareerMemory={
 version:'18.180-long-career-bounded-memory',
 scorerArchiveLimitPerCompetition:180,
 tableCacheEntries:48,
 shardedHistories:['scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive'],
 snapshot:()=>({
  year:state?.year||0,day:state?.day||0,
  players:Object.keys(state?.players||{}).length,
  scorerYears:state?.scorerArchive?.length||0,
  scorerRows:(state?.scorerArchive||[]).reduce((n,a)=>n+Object.values(a?.competitions||{}).reduce((m,db)=>m+Object.keys(db||{}).length,0),0),
  careerYears:Object.keys(state?.v555CareerArchive||{}).length,
  transfers:state?.transfers?.length||0,
  retirements:state?.retirements?.length||0,
  nationalArchive:state?.v735NationalArchive?.length||0,
  heapMiB:performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null,
  workerResident:!!v53Worker
 })
};
"""
    html=html.replace(marker,diag+marker,1)

    path.write_text(html,encoding='utf-8')
    print('Long-career memory optimization applied.')

if __name__=='__main__':
    main()
