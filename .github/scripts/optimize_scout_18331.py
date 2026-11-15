from __future__ import annotations
import json
import re
import sys
from pathlib import Path

MARK = "/* FUTBR_SCOUT_RESPONSIVE_18331 */"
ANCHOR = "function v638CandidateUniverse(q){"
OLD_SEND = """const q=v572CloneScoutFilters(v529ScoutRead()),m=v638CreateMission(q);state.v638ScoutMissions.unshift(m);state.v638ScoutSelected=m.id;persist();render();toast(`Missão enviada. O scout ${m.department} precisa de cerca de ${m.target} jornadas para consolidar recomendações.`,'success');"""
NEW_SEND = """const q=v572CloneScoutFilters(v529ScoutRead());if(v638ScoutBusy)return;v638ScoutBusy=true;toast('Olheiro pesquisando atletas. A interface continuara disponivel.','info');setTimeout(async()=>{const career=state,club=state?.user;try{const m=await v638CreateMissionResponsive(q);if(state!==career||state?.user!==club)return;state.v638ScoutMissions.unshift(m);state.v638ScoutSelected=m.id;persist();render();toast(`Missão enviada. O scout ${m.department} precisa de cerca de ${m.target} jornadas para consolidar recomendações.`,'success');}catch(error){console.error('[Olheiro 18.331]',error);toast('Nao foi possivel concluir a busca do olheiro. Tente novamente.','warn');}finally{v638ScoutBusy=false;}},0);"""

ASYNC = r'''
/* FUTBR_SCOUT_RESPONSIVE_18331 */
let v638ScoutBusy=false;
function v638ScoutTopInsert(top, item){
  let pos=top.length;
  for(let i=0;i<top.length;i++){
    const old=top[i];
    if(item.score>old.score||(item.score===old.score&&item.row.fee<old.row.fee)){pos=i;break;}
  }
  if(pos>=18)return;
  top.splice(pos,0,item);
  if(top.length>18)top.length=18;
}
async function v638CandidateUniverseResponsive(q){
  const career=state, own=E.human(career), allTeams=career.teams;
  const exact=[], nearby=[];
  let exactTotal=0, visited=0;
  const score=(row,penalty)=>v638ScoutScore(row,q)-penalty;
  const process=(t,id,youth)=>{
    const p=E.player(career,id);
    if(!p||(youth&&p.age<18&&t.country!==own.country))return;
    const a=E.attributes(p),o=E.overall(p);
    const raw=youth?v529YouthFee(p,t):E.transferPrice(career,p.id);
    const fee=Number.isFinite(raw)?Math.max(0,raw):E.value(p);
    const row={p,t,a,o,fee,youth};
    const misses=v529ScoutMatch(row,q,true);
    if(misses===0){exactTotal++;v638ScoutTopInsert(exact,{row,score:score(row,0)});}
    v638ScoutTopInsert(nearby,{row,score:score(row,misses*9)});
  };
  for(let ti=0;ti<allTeams.length;ti++){
    const t=allTeams[ti];
    if(!t||t.id===own.id)continue;
    if(q.scope!=='youth'){
      for(const id of (t.roster||[])){
        process(t,id,false);
        if(++visited%192===0)await new Promise(resolve=>setTimeout(resolve,0));
        if(state!==career)throw new Error('Carreira substituida durante busca do olheiro');
      }
    }
    if(q.scope!=='senior'){
      for(const id of (t.academy||[])){
        process(t,id,true);
        if(++visited%192===0)await new Promise(resolve=>setTimeout(resolve,0));
        if(state!==career)throw new Error('Carreira substituida durante busca do olheiro');
      }
    }
  }
  const rows=(exactTotal>=18?exact:nearby).map(x=>x.row);
  return {rows,total:exactTotal,near:exactTotal<Math.min(18,rows.length)};
}
async function v638CreateMissionResponsive(q){
  const dept=v638Department(),found=await v638CandidateUniverseResponsive(q),id=v638MissionId();
  return {id,status:'active',clubId:state.user,requestedYear:Number(state.year),requestedDay:Number(state.day),scheduleLength:Number(state.schedule?.length??60),target:Number(dept.target),accuracy:Number(dept.accuracy),department:dept.name,filters:v572CloneScoutFilters(q),candidates:found.rows.map(x=>({id:x.p.id,clubId:x.t.id,youth:!!x.youth,fee:Math.round(x.fee||0)})),exactTotal:found.total,near:found.near,createdAt:Date.now()};
}
'''

def main(project):
    path=project/"src"/"index.html"
    source=path.read_text(encoding="utf-8")
    if MARK in source:
        print("Olheiro 18.331 ja instalado")
        return
    if source.count(ANCHOR)!=1:
        raise RuntimeError(f"Ancora candidata invalida {source.count(ANCHOR)}")
    if source.count(OLD_SEND)!=1:
        raise RuntimeError(f"Envio do olheiro mudou: encontrados {source.count(OLD_SEND)}")
    source=source.replace(ANCHOR,ASYNC+"\n"+ANCHOR,1)
    source=source.replace(OLD_SEND,NEW_SEND,1)
    if source.count(MARK)!=1 or source.count("v638CreateMissionResponsive(q)")!=2:
        raise RuntimeError("Integridade da instalacao do Olheiro 18.331 falhou")
    path.write_text(source,encoding="utf-8")
    report={"scope":"scout-only","async_batches":192,"max_candidates_kept_each_rank":18,"changed_html_bytes":len(source.encode('utf-8')),"mission_flow":"responsive dispatch"}
    (project/"scout-18331-install.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: optimize_scout_18331.py <project>")
    main(Path(sys.argv[1]))
