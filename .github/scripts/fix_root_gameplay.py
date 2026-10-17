from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def once(text, old, new, label):
    n=text.count(old)
    if n!=1:
        fail(f"{label}: esperado 1, encontrado {n}")
    return text.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: fix_root_gameplay.py <project-dir>")
    project=Path(sys.argv[1]).resolve()
    path=project/"src"/"index.html"
    html=path.read_text(encoding="utf-8")

    if 'futbr-root-18170-fixes' in html:
        print("root gameplay fixes already present")
        return

    html=once(
        html,
        """function v53PaintStatus(){const el=$('#v53-live-status');if(el&&state)el.innerHTML=v53StatusHTML();if(v53Sim.active)document.title='Jornada '+(v53Sim.day+1)+' | FutBR Manager 5.3';}
/* clean-build: legacy render wrapper removed */""",
        """function v53PaintStatus(){const el=$('#v53-live-status');if(el&&state)el.innerHTML=v53StatusHTML();if(v53Sim.active)document.title='Jornada '+(v53Sim.day+1)+' | FutBR Manager 5.3';}
let v53NationalJumpPaintStamp='',v53NationalJumpPaintRAF=0;
function v53ScheduleNationalJumpPaint(){
 if(!state||document.hidden||v53Sim?.mode!=='nationaljump'||!['world','national'].includes(view))return false;
 const stamp=[state.year,state.day,view].join('|');if(stamp===v53NationalJumpPaintStamp)return false;
 v53NationalJumpPaintStamp=stamp;
 if(v53NationalJumpPaintRAF)return true;
 v53NationalJumpPaintRAF=requestAnimationFrame(()=>{
  v53NationalJumpPaintRAF=0;
  if(!state||document.hidden||v53Sim?.mode!=='nationaljump'||!['world','national'].includes(view))return;
  try{v53RefreshView(false);}catch(e){console.warn('[root] nationaljump live overview:',e?.message||e);}
 });
 return true;
}
/* clean-build: legacy render wrapper removed */""",
        "nationaljump scheduler"
    )

    html=once(
        html,
        """     try{E.invalidateMarket(state);}catch(e){}v52MarketIndex=null;v53Sim.day=Number(state.day)||Number(m.day)||v53Sim.day;v53Stats.patches++;
     if(v53Sim?.mode!=='dayfast'&&v53Sim?.mode!=='nationaljump'&&v53Sim?.mode!=='nextmatch')refresh=true;""",
        """     try{E.invalidateMarket(state);}catch(e){}v52MarketIndex=null;v53Sim.day=Number(state.day)||Number(m.day)||v53Sim.day;v53Stats.patches++;
     if(v53Sim?.mode==='nationaljump'){v53ScheduleNationalJumpPaint();}
     else if(v53Sim?.mode!=='dayfast'&&v53Sim?.mode!=='nextmatch')refresh=true;""",
        "nationaljump vac-live"
    )

    html=once(
        html,
        """   if(m.kind==='national-jump-day'){
    v53Sim.day=Number(m.day)||v53Sim.day;v53Sim.progress='Avancando ate a Selecao · jornada '+v53Sim.day;v53PaintStatus();continue;
   }""",
        """   if(m.kind==='national-jump-day'){
    v53Sim.day=Number(m.day)||v53Sim.day;v53Sim.progress='Avancando ate a Selecao · jornada '+v53Sim.day;v53PaintStatus();v53ScheduleNationalJumpPaint();continue;
   }""",
        "nationaljump day"
    )

    html=once(
        html,
        """     if(Number.isFinite(Number(m.day)))state.day=Number(m.day);if(Number.isFinite(Number(m.year)))state.year=Number(m.year);
     try{E.invalidateMarket(state);}catch(e){}v52MarketIndex=null;
    }
    continue;""",
        """     if(Number.isFinite(Number(m.day)))state.day=Number(m.day);if(Number.isFinite(Number(m.year)))state.year=Number(m.year);
     try{E.invalidateMarket(state);}catch(e){}v52MarketIndex=null;v53ScheduleNationalJumpPaint();
    }
    continue;""",
        "nationaljump sync"
    )

    html=once(
        html,
        """function v5Bench(target,ctx){const ids=ctx==='live'?target.bench:E.human(state).roster.filter(id=>!target.lineup.includes(id));return `<div class="v5-bench" data-v5-bench="${ctx}">${ids.map(id=>v5Tile(id,target,ctx)).join('')}</div>`;}""",
        """function v5Bench(target,ctx){let ids=ctx==='live'?target.bench:E.human(state).roster.filter(id=>!target.lineup.includes(id));if(typeof v602SortPlayerIds==='function')ids=v602SortPlayerIds(ids);return `<div class="v5-bench" data-v5-bench="${ctx}">${ids.map(id=>v5Tile(id,target,ctx)).join('')}</div>`;}""",
        "base bench order"
    )

    html=once(
        html,
        """ t.v600PreferredBench=list.slice(0,V600_BENCH_LIMIT);return t.v600PreferredBench;
}
function v133NationalBench(t){return v133NormalizeNationalBench(t).map(id=>v133NationalTile(id,t)).join('');}""",
        """ t.v600PreferredBench=v602SortPlayerIds(list.slice(0,V600_BENCH_LIMIT));return t.v600PreferredBench;
}
function v133NationalBench(t){return v133NormalizeNationalBench(t).map(id=>v133NationalTile(id,t)).join('');}""",
        "national bench order"
    )

    html=once(
        html,
        """  const ids=(target?.bench||[]).filter(Boolean).slice(0,V600_BENCH_LIMIT);
  return `<div class="v600-bench-list v1893-live-list" data-v5-bench="live">${ids.map(id=>v5Tile(id,target,'live')).join('')}</div>`;""",
        """  const raw=(target?.bench||[]).filter(Boolean).slice(0,V600_BENCH_LIMIT),ids=typeof v602SortPlayerIds==='function'?v602SortPlayerIds(raw):raw;
  return `<div class="v600-bench-list v1893-live-list" data-v5-bench="live">${ids.map(id=>v5Tile(id,target,'live')).join('')}</div>`;""",
        "live bench order"
    )

    html=once(
        html,
        """function v1893LiveNotRelated(t,side){
 const used=new Set([...(side?.lineup||[]).filter(Boolean),...(side?.bench||[]).filter(Boolean)]);
 return (t?.roster||[]).filter(id=>id&&!used.has(id));
}""",
        """function v1893LiveNotRelated(t,side){
 const used=new Set([...(side?.lineup||[]).filter(Boolean),...(side?.bench||[]).filter(Boolean)]),ids=(t?.roster||[]).filter(id=>id&&!used.has(id));
 return typeof v602SortPlayerIds==='function'?v602SortPlayerIds(ids):ids;
}""",
        "live unrelated order"
    )

    anchor="function v643ConvertNewCareerToNational(s,code){const root=v640EnsureState(s),t=root?.teams?.[code],me=v641NormalizeCoach(s.coaches?.[s.userCoachId]),old=me?.clubId?E.team(s,me.clubId):E.team(s,s.user);"
    if anchor not in html:
        fail("national conversion anchor missing")
    helper=r'''
const V18170_NATIONAL_POOL_TARGET=Object.freeze({GOL:3,ZAG:5,LAT:4,VOL:4,MEI:5,ATA:5});
function v18170NationalPoolBase(s,code,pos,conf){
 const all=v640Eligible(s,code),same=all.filter(p=>p.pos===pos).sort((a,b)=>E.overall(b)-E.overall(a)).slice(0,5),top=all.slice(0,18);
 const sample=same.length?same:top,avg=sample.length?E.avg(sample.map(E.overall)):(V640_CONF_BASE[conf]||62);
 return E.clamp(Math.round(avg),45,86);
}
function v18170EnsureNationalPool(s,code){
 const t=v640Team(s,code);if(!t||!s?.players)return {code,created:0};
 const target=V18170_NATIONAL_POOL_TARGET,pool=v640Eligible(s,code),counts={GOL:0,ZAG:0,LAT:0,VOL:0,MEI:0,ATA:0},created=[];
 for(const p of pool)if(Object.hasOwn(counts,p.pos))counts[p.pos]++;
 s.free=Array.isArray(s.free)?s.free:[];
 for(const pos of ['GOL','ZAG','LAT','VOL','MEI','ATA']){
  let missing=Math.max(0,(target[pos]||0)-(counts[pos]||0));
  while(missing-->0){
   const base=v18170NationalPoolBase(s,code,pos,t.conf),age=20+Math.floor(E.rng(s)*10),id=E.createPlayer(s,pos,base,age),p=s.players[id];
   if(!p)throw Error('Falha ao criar jogador livre para '+t.name+'.');
   p.natCode=code;p.clubId=null;p.real=false;p.generatedNationalSupport=true;p.v18170InitialNationalFreeAgent=true;
   p.star=false;p.starCandidate=false;p.editorStarOverride=false;
   try{v200ApplyDatabaseOVR(p,base);}catch(e){}
   const now=E.overall(p);p.potential=Math.max(now,Math.min(90,now+(age<=22?5:age<=26?3:1)));
   if(!s.free.includes(id))s.free.push(id);created.push(id);counts[pos]=(counts[pos]||0)+1;
  }
 }
 if(created.length)t.v18170InitialSupport=(t.v18170InitialSupport||0)+created.length;
 return {code,created:created.length};
}
function v18170EnsureAllNationalPools(s){
 if(!s||s.v18170NationalPools?.done)return s?.v18170NationalPools||null;
 v640EnsureState(s);let total=0,nations=0;const rows={};
 for(const a of v640AssocCatalog()){
  const r=v18170EnsureNationalPool(s,a.code);if(r.created){rows[a.code]=r.created;total+=r.created;nations++;}
 }
 s.v18170NationalPools={done:true,year:s.year,totalCreated:total,nations,createdByNation:rows,freeAgents:true,target:26,ovrModel:'existing-nationality-position-average'};
 return s.v18170NationalPools;
}
'''
    html=html.replace(anchor,helper+"\n"+anchor,1)

    html=once(
        html,
        " if(out&&op==='create'&&callParams?.options?.v643StartType==='national')v643ConvertNewCareerToNational(out,String(callParams.options.v643NationalCode||'BRA'));",
        " if(out&&op==='create')v18170EnsureAllNationalPools(out);\n if(out&&op==='create'&&callParams?.options?.v643StartType==='national')v643ConvertNewCareerToNational(out,String(callParams.options.v643NationalCode||'BRA'));",
        "seed all national pools"
    )

    html=once(
        html,
        """ const enemy=f.home===chosen.code?f.away:f.home,enemyT=v640Team(state,enemy);
 if(!enemyT)throw Error('Selecao adversaria nao encontrada.');
 const enemyList=v1888NationalEligible(state,enemyT,f);
 if(enemyList.length<11)throw Error('O adversario nao tem jogadores suficientes para esta partida.');""",
        """ const enemy=f.home===chosen.code?f.away:f.home,enemyT=v640Team(state,enemy);
 if(!enemyT)throw Error('Selecao adversaria nao encontrada.');
 v18170EnsureNationalPool(state,enemy);
 const enemyList=v1888NationalEligible(state,enemyT,f);
 if(enemyList.length<11)throw Error('Nao foi possivel montar 11 jogadores aptos para a selecao adversaria.');""",
        "old-save opponent repair"
    )

    html += r'''
<script id="futbr-root-18170-fixes">
window.GestorFC=window.GestorFC||{};
window.GestorFC.root18170={nationalJumpLiveOverview:true,benchPositionOrder:true,nationalFreeAgentsAtCreation:true,liveDragUsesCoreV5Execute:true};
</script>
'''

    path.write_text(html,encoding="utf-8")
    print("root gameplay fixes applied")

if __name__=="__main__":
    main()
