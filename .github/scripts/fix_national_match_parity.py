from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: fix_national_match_parity.py <project-dir>")
    project=Path(sys.argv[1]).resolve()
    p=project/"src"/"index.html"
    html=p.read_text(encoding="utf-8")

    # AI national teams must always be able to field a legal XI. Rebuild the
    # current call-up from all eligible nationals; create support players only
    # when the association itself lacks enough available depth.
    ai_helper=r'''function v18166PrepareAiNationalOpponent(s,code,f){
 const t=v640Team(s,code);if(!t)return [];
 const key=v641NationalDisciplineKey(s,f);
 const playable=()=>v640Eligible(s,code).filter(p=>p&&!Number(p.injury)&&!(E.disciplineRecord(p,key).ban>0));
 let pool=playable();
 if(pool.length<18||!pool.some(p=>p.pos==='GOL')){
  try{v643EnsureNationalStarterDepth(s,code);}catch(e){console.warn('[18.166] suporte nacional IA:',e?.message||e);}
  pool=playable();
 }
 if(pool.length<18||!pool.some(p=>p.pos==='GOL')){
  const counts={GOL:0,ZAG:0,LAT:0,VOL:0,MEI:0,ATA:0};
  for(const p of pool)if(Object.hasOwn(counts,p.pos))counts[p.pos]++;
  const target={GOL:2,ZAG:3,LAT:3,VOL:2,MEI:3,ATA:3},base=Math.round(V640_CONF_BASE[t.conf]||62),created=[];
  for(const pos of ['GOL','ZAG','LAT','VOL','MEI','ATA']){
   let need=Math.max(0,(target[pos]||0)-(counts[pos]||0));
   while(need-->0){
    const id=E.createPlayer(s,pos,base,21+Math.floor(E.rng(s)*8)),p=s.players[id];
    if(!p)continue;p.natCode=code;p.clubId=null;p.real=false;p.generatedNationalSupport=true;p.v18166EmergencyDepth=true;
    s.free??=[];if(!s.free.includes(id))s.free.push(id);created.push(id);
   }
  }
  pool=playable();
  while(pool.length<18){
   const pos=['ZAG','LAT','VOL','MEI','ATA'][pool.length%5];
   const id=E.createPlayer(s,pos,base,21+Math.floor(E.rng(s)*8)),p=s.players[id];
   if(!p)break;p.natCode=code;p.clubId=null;p.real=false;p.generatedNationalSupport=true;p.v18166EmergencyDepth=true;
   s.free??=[];if(!s.free.includes(id))s.free.push(id);pool=playable();
  }
 }
 const score=p=>typeof v165CallupScore==='function'?v165CallupScore(p):E.overall(p);
 pool.sort((a,b)=>score(b)-score(a)||(Number(a.age)||99)-(Number(b.age)||99));
 const auto=v640AutoRoster(s,code,26),ok=id=>{const p=s.players?.[id];return p&&!Number(p.injury)&&!(E.disciplineRecord(p,key).ban>0);};
 const roster=[];for(const id of auto)if(ok(id)&&!roster.includes(id)&&roster.length<26)roster.push(id);
 for(const p of pool)if(!roster.includes(p.id)&&roster.length<26)roster.push(p.id);
 t.roster=roster;
 return v1888NationalEligible(s,t,f);
}
'''
    marker='function v1888BeginNational(){'
    if marker not in html: fail('v1888BeginNational not found')
    html=html.replace(marker,ai_helper+'\n'+marker,1)

    old_enemy=""" const enemy=f.home===chosen.code?f.away:f.home,enemyT=v640Team(state,enemy);
 if(!enemyT)throw Error('Selecao adversaria nao encontrada.');
 const enemyList=v1888NationalEligible(state,enemyT,f);
 if(enemyList.length<11)throw Error('O adversario nao tem jogadores suficientes para esta partida.');"""
    new_enemy=""" const enemy=f.home===chosen.code?f.away:f.home,enemyT=v640Team(state,enemy);
 if(!enemyT)throw Error('Selecao adversaria nao encontrada.');
 const enemyList=v18166PrepareAiNationalOpponent(state,enemy,f);
 if(enemyList.length<11)throw Error('Nao foi possivel montar um elenco apto para a selecao adversaria.');"""
    if old_enemy not in html: fail('AI opponent roster block not found')
    html=html.replace(old_enemy,new_enemy,1)

    runtime=r'''
<script id="futbr-v18164-national-match-parity">
(()=>{
 function v18167SeedNationalPools(s){
  if(!s?.players||s.v18167NationalPoolSeed?.done)return s?.v18167NationalPoolSeed||null;
  const associations=typeof v640AssocCatalog==='function'?v640AssocCatalog():[];
  const byNat=new Map();
  for(const p of Object.values(s.players||{})){
   if(!p||Number(p.age)<16)continue;
   const code=String(p.natCode||'').toUpperCase();if(!code)continue;
   if(!byNat.has(code))byNat.set(code,[]);byNat.get(code).push(p);
  }
  const desired={GOL:3,ZAG:5,LAT:4,VOL:4,MEI:5,ATA:5},createdByNation={},positions=Object.keys(desired);
  s.free=Array.isArray(s.free)?s.free:[];
  const mean=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:0;
  for(const assoc of associations){
   const code=String(assoc.code||'').toUpperCase();if(!code)continue;
   const pool=byNat.get(code)||[];
   const byPos={GOL:[],ZAG:[],LAT:[],VOL:[],MEI:[],ATA:[]};
   for(const p of pool)if(byPos[p.pos])byPos[p.pos].push(p);
   const overallSample=pool.slice().sort((a,b)=>E.overall(b)-E.overall(a)).slice(0,18);
   const nationBase=Math.round(mean(overallSample.map(E.overall))||(V640_CONF_BASE[assoc.conf]||62));
   const created=[];
   const createOne=pos=>{
    const sample=byPos[pos].length?byPos[pos]:overallSample;
    const base=Math.max(48,Math.min(84,Math.round(mean(sample.map(E.overall))||nationBase)));
    const age=20+Math.floor(E.rng(s)*10);
    const id=E.createPlayer(s,pos,base,age),p=s.players[id];
    if(!p)return null;
    p.natCode=code;p.clubId=null;p.real=false;p.generatedNationalSupport=true;p.v18167InitialNationalPool=true;
    p.star=false;p.starCandidate=false;p.editorStarOverride=false;
    const now=E.overall(p);p.potential=Math.max(now,Math.min(90,now+(age<=22?5:age<=26?3:1)));
    if(!s.free.includes(id))s.free.push(id);
    pool.push(p);byPos[pos].push(p);created.push(id);return id;
   };
   for(const pos of positions){
    let missing=Math.max(0,(desired[pos]||0)-byPos[pos].length);
    while(missing-->0)createOne(pos);
   }
   while(pool.length<26){
    const pos=positions.slice().sort((a,b)=>(byPos[a].length/(desired[a]||1))-(byPos[b].length/(desired[b]||1)))[0]||'MEI';
    createOne(pos);
   }
   if(created.length)createdByNation[code]=created.length;
  }
  const total=Object.values(createdByNation).reduce((a,b)=>a+b,0);
  s.v18167NationalPoolSeed={done:true,year:s.year,totalCreated:total,nations:Object.keys(createdByNation).length,createdByNation,freeAgents:true,targetPerNation:26,ovrModel:'existing-nationality-position-average'};
  return s.v18167NationalPoolSeed;
 }
 const v18167BaseCall=v53Call;
 v53Call=async function(op,params={}){
  const out=await v18167BaseCall(op,params);
  if(out&&op==='create')v18167SeedNationalPools(out);
  return out;
 };
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.seedNationalPools18167=v18167SeedNationalPools;

 function v18167SortIds(ids){
  const order={GOL:0,ZAG:1,LAT:2,VOL:3,MEI:4,ATA:5};
  return [...new Set(ids||[])].sort((a,b)=>{
   const pa=E.player(state,a),pb=E.player(state,b);
   const oa=order[pa?.pos]??99,ob=order[pb?.pos]??99;
   if(oa!==ob)return oa-ob;
   const qa=pa?E.overall(pa):0,qb=pb?E.overall(pb):0;
   if(qa!==qb)return qb-qa;
   return String(pa?.name||'').localeCompare(String(pb?.name||''),'pt-BR');
  });
 }

 const v18167BaseNationalBench=v133NationalBench;
 v133NationalBench=function(t){return v18167SortIds(v133NormalizeNationalBench(t)).map(id=>v133NationalTile(id,t)).join('');};
 const v18167BaseNationalUnrelatedIds=v153NationalUnrelatedIds;
 v153NationalUnrelatedIds=function(t){return v18167SortIds(v18167BaseNationalUnrelatedIds(t));};
 const v18167BaseLiveBench=v5Bench;
 v5Bench=function(target,ctx){
  if(ctx==='live'&&Array.isArray(target?.bench))target.bench=v18167SortIds(target.bench);
  return v18167BaseLiveBench(target,ctx);
 };
 if(typeof v1893LiveNotRelated==='function'){
  const v18167BaseLiveNotRelated=v1893LiveNotRelated;
  v1893LiveNotRelated=function(t,side){return v18167SortIds(v18167BaseLiveNotRelated(t,side));};
 }
 if(typeof v1893ExtraRows==='function'){
  const v18167BaseExtraRows=v1893ExtraRows;
  v1893ExtraRows=function(ids,side){return v18167BaseExtraRows(v18167SortIds(ids),side);};
 }
 const isNationalLive=()=>!!state?.live?.v1888National;
 const ownLiveId=()=>isNationalLive()?state.live.v1888HumanId:state?.user;
 const isOwnLiveTeam=id=>!!id&&String(id)===String(ownLiveId()||'');
 let v18165OwnClickGuard=0;
 function v18165OwnTeamButton(target){
  const btn=target?.closest?.('[data-action="v513-match-team"],[data-action="v587-switch-board"],[data-action="v1897-switch-board"]');
  if(!btn||!state?.live||!isOwnLiveTeam(btn.dataset.team))return null;
  return btn;
 }
 function v18165OpenOwnFromPointer(event){
  const btn=v18165OwnTeamButton(event.target);if(!btn)return false;
  if(event.type==='pointerup'&&event.pointerType==='mouse'&&event.button!==0)return false;
  event.preventDefault();event.stopImmediatePropagation();
  v18165OwnClickGuard=performance.now()+800;
  v526OpenOwnTactics();
  return true;
 }
 // Window/capture runs before the legacy document pointer handler. This guarantees
 // the first click opens the editable board for clubs and national teams alike.
 window.addEventListener('pointerup',v18165OpenOwnFromPointer,true);
 window.addEventListener('click',event=>{
  const btn=v18165OwnTeamButton(event.target);if(!btn)return;
  event.preventDefault();event.stopImmediatePropagation();
  if(performance.now()>v18165OwnClickGuard)v526OpenOwnTactics();
 },true);

 const baseSetView=v513SetView;
 v513SetView=function(mode){
  if(mode==='tactics'&&isNationalLive()){
   v526OpenOwnTactics();
   return;
  }
  return baseSetView(mode);
 };

 const baseAct=act;
 act=function(el){
  const a=el?.dataset?.action;
  if(isNationalLive()&&['v513-match-team','v587-switch-board','v1897-switch-board'].includes(a)){
   const id=el.dataset.team;
   if(!id)return;
   if(isOwnLiveTeam(id))v526OpenOwnTactics();
   else v513OpenInspector(id);
   return;
  }
  if(a==='v18164-national-result-view'){
   const id=el.dataset.fixture;
   const found=v18164FindNationalFixture(id);
   if(!found){toast('Partida de seleções não encontrada.','warn');return;}
   v18164NationalFixtureDetails(found.f,found.stage,found.day);
   return;
  }
  return baseAct(el);
 };

 document.addEventListener('click',ev=>{
  if(!isNationalLive())return;
  const btn=ev.target?.closest?.('button');
  if(!btn)return;
  const txt=String(btn.textContent||'').trim().toLowerCase();
  if((txt==='táticas'||txt==='taticas'||txt.includes('prancheta detalhada'))&&!btn.dataset.v18164Pass){
   const a=btn.dataset.action||'';
   if(!['v1897-switch-board','v513-match-team'].includes(a)){
    ev.preventDefault();ev.stopImmediatePropagation();
    v526OpenOwnTactics();
   }
  }
 },true);

 const roObserver=new MutationObserver(()=>{
  if(!isNationalLive())return;
  const ro=document.querySelector('#modal-root .v1896-readonly-page');
  if(!ro)return;
  const ownName=E.team(state,ownLiveId())?.name||'';
  const title=ro.querySelector('h1')?.textContent||'';
  if(ownName&&title.includes(ownName))queueMicrotask(()=>v526OpenOwnTactics());
 });
 roObserver.observe(document.documentElement,{childList:true,subtree:true});

 let v18167NationalDrag=null;
 document.addEventListener('dragstart',e=>{
  const el=e.target?.closest?.('.v144-national-tactics [data-v5-player][data-v5-context="national"]');
  if(!el||el.disabled)return;
  v18167NationalDrag={id:el.dataset.v5Player,ctx:'national'};
  try{e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',JSON.stringify(v18167NationalDrag));}catch(_){}
 },true);
 document.addEventListener('dragover',e=>{
  if(!v18167NationalDrag)return;
  if(e.target?.closest?.('.v144-national-tactics [data-v5-board="national"],.v144-national-tactics [data-v5-player][data-v5-context="national"]')){
   e.preventDefault();try{e.dataTransfer.dropEffect='move';}catch(_){}
  }
 },true);
 document.addEventListener('drop',e=>{
  if(!v18167NationalDrag)return;
  const root=e.target?.closest?.('.v144-national-tactics');if(!root)return;
  e.preventDefault();e.stopImmediatePropagation();
  const dest=e.target.closest('[data-v5-player][data-v5-context="national"]')||e.target.closest('[data-v5-vacant]')||e.target.closest('[data-v5-board="national"]');
  const src=v18167NationalDrag;v18167NationalDrag=null;
  try{v5Execute(src,dest,e.clientX,e.clientY);}catch(err){toast(err?.message||String(err),'warn');}
 },true);
 document.addEventListener('dragend',()=>{v18167NationalDrag=null;},true);

 const style=document.createElement('style');
 style.id='v18164-national-match-parity-style';
 style.textContent=
 "#modal-root .v526-own-tactics .v600-bench-panel .panel-body,#modal-root .v1896-readonly-page .v600-bench-panel .panel-body{display:flex!important;flex-direction:column!important;width:100%!important;max-width:none!important;min-height:0!important;overflow:hidden!important;box-sizing:border-box!important}"+
 "#modal-root .v526-own-tactics #v526-own-bench,#modal-root .v1896-readonly-page .v1893-bench-host{display:flex!important;flex:1 1 auto!important;width:100%!important;max-width:none!important;min-width:0!important;height:100%!important;min-height:0!important;box-sizing:border-box!important}"+
 "#modal-root .v526-own-tactics #v526-own-bench>.v600-bench-list,#modal-root .v1896-readonly-page .v1896-readonly-bench{width:100%!important;max-width:none!important;min-width:0!important;height:100%!important;min-height:0!important;flex:1 1 auto!important;justify-items:stretch!important;align-items:stretch!important;box-sizing:border-box!important}"+
 "#modal-root .v526-own-tactics #v526-own-bench .v5-reserve,#modal-root .v1896-readonly-page .v1896-readonly-bench>.v5-reserve{width:100%!important;min-width:0!important;max-width:none!important;justify-self:stretch!important;align-self:stretch!important;box-sizing:border-box!important;margin-left:0!important;margin-right:0!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v600-bench-panel .panel-body{display:flex!important;flex-direction:column!important;min-height:0!important;overflow:hidden!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v1893-bench-host{width:100%!important;height:100%!important;min-height:0!important;display:flex!important;flex:1 1 auto!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v1896-readonly-bench{width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;flex:1 1 auto!important;display:grid!important;grid-template-rows:repeat(12,minmax(0,1fr))!important;grid-auto-rows:minmax(0,1fr)!important;gap:3px!important;overflow:hidden!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v1896-readonly-bench>.v5-reserve{width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;margin:0!important;padding:2px 5px!important;box-sizing:border-box!important;border-radius:6px!important;display:grid!important;grid-template-columns:34px minmax(0,1fr) 54px!important;grid-template-rows:1fr 1fr!important;gap:0 5px!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v1896-readonly-bench>.v5-reserve .v5-shirt{grid-row:1/3!important;align-self:center!important;width:auto!important;height:auto!important;min-width:0!important;min-height:0!important;padding:0!important;font-size:13px!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v1896-readonly-bench>.v5-reserve .v5-tile-name{font-size:9.2px!important;line-height:1.08!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v1896-readonly-bench>.v5-reserve .v5-tile-meta{font-size:7.2px!important;line-height:1.05!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}"+
 "body.v1888-national-live #modal-root .v1896-readonly-page .v1896-readonly-bench>.v5-reserve .v5-energy{grid-column:3!important;grid-row:1/3!important;align-self:center!important;justify-self:end!important;width:54px!important;min-width:54px!important;max-width:54px!important;height:12px!important;min-height:12px!important;max-height:12px!important}"+
 ".v18164-national-view-cell{width:88px!important;text-align:right!important}.v18164-national-view-btn{min-width:66px!important}.v18165-national-summary-row{grid-template-columns:minmax(0,1fr) 90px minmax(0,1fr) 150px!important}.v18165-national-summary-row>.btn{width:100%!important;justify-content:center!important}";
 document.head.appendChild(style);

 function v18164FindNationalFixture(id){
  for(const [day,stage] of (state?.schedule||[]).entries()){
   for(const f of stage?.nationalFixtures||[])if(String(f?.id)===String(id))return {f,stage,day};
  }
  return null;
 }
 window.v18164FindNationalFixture=v18164FindNationalFixture;

 function v18164NationalFixtureDetails(f,stage,day){
  const h=v640Team(state,f.home),a=v640Team(state,f.away),r=f.result;
  if(!h||!a)return;
  const root=v640EnsureState(state);
  const label=typeof v737NationalCompetitionLabel==='function'
   ?v737NationalCompetitionLabel(root,f,stage)
   :(f.competitionName||stage?.label||'Seleções');
  const events=(f.events||[]).map(e=>'<div class="event '+esc(e.type||'')+'"><span class="minute">'+(Number(e.minute)||0)+'&#39;</span><span>'+esc(e.text||'Acontecimento')+'</span></div>').join('');
  const shots=Array.isArray(r?.shots)?r.shots:null,xg=Array.isArray(r?.xg)?r.xg:null;
  let stats='';
  if(r){
   stats='<div class="v523-stat-strip">'+
    '<div class="v523-stat"><b>'+(shots?(shots[0]+'-'+shots[1]):'—')+'</b><small>Finalizações</small></div>'+
    '<div class="v523-stat"><b>'+(xg?(Number(xg[0]).toFixed(2)+'-'+Number(xg[1]).toFixed(2)):'—')+'</b><small>xG</small></div>'+
    '<div class="v523-stat"><b>'+(r.pens?(r.pens[0]+'-'+r.pens[1]):'—')+'</b><small>Pênaltis</small></div>'+
   '</div>';
  }
  const score=r?((Number(r.home)||0)+' : '+(Number(r.away)||0)):'VS';
  const pens=r?.pens?'<div class="center gold strong mt12">Pênaltis: '+r.pens[0]+' × '+r.pens[1]+'</div>':'';
  const status=r?'':'<div class="notice info mt16">Partida ainda não concluída nesta data.</div>';
  const log=events||(r?'<div class="empty">Sem acontecimentos detalhados registrados.</div>':'');
  modal('<div class="modal-header"><div><span class="eyebrow">'+esc(label)+'</span><h2>Detalhes da partida</h2></div>'+button('close','Fechar','small')+'</div>'+
   '<div class="modal-body"><div class="v640-match-hero"><div>'+v640Flag(f.home,'large')+'<strong>'+esc(h.name)+'</strong></div>'+
   '<b class="v640-big-score">'+score+'</b><div>'+v640Flag(f.away,'large')+'<strong>'+esc(a.name)+'</strong></div></div>'+
   pens+stats+status+'<div class="match-log mt16">'+log+'</div></div>'+
   '<div class="modal-footer">'+button('close','Fechar','primary')+'</div>','national-result-detail','wide');
 }
 window.v18164NationalFixtureDetails=v18164NationalFixtureDetails;

 if(typeof v737NationalDayHTML==='function'){
  const baseNationalDayHTML=v737NationalDayHTML;
  v737NationalDayHTML=function(index){
   const raw=baseNationalDayHTML(index),stage=state?.schedule?.[index];
   if(!stage||stage.type!=='national')return raw;
   const box=document.createElement('div');box.innerHTML=raw;
   const table=box.querySelector('.v737-national-day-table');
   if(!table)return raw;
   const head=table.querySelector('thead tr');
   if(head&&!head.querySelector('.v18164-national-view-cell')){
    const th=document.createElement('th');th.className='v18164-national-view-cell';th.textContent='';head.appendChild(th);
   }
   const fixtures=stage.nationalFixtures||[];
   [...table.querySelectorAll('tbody tr')].forEach((tr,i)=>{
    if(tr.querySelector('.empty')){const td=tr.querySelector('td');if(td)td.colSpan=5;return;}
    const f=fixtures[i];if(!f)return;
    const td=document.createElement('td');td.className='v18164-national-view-cell';
    td.innerHTML='<button type="button" class="btn small ghost v18164-national-view-btn" data-action="v18164-national-result-view" data-fixture="'+esc(f.id)+'">Detalhes</button>';
    tr.appendChild(td);
   });
   return box.innerHTML;
  };
 }

 if(typeof v640ShowStageResults==='function'){
  const v18165BaseStageResults=v640ShowStageResults;
  v640ShowStageResults=function(stage){
   const games=(stage?.nationalFixtures||[]).filter(f=>f?.result);
   if(!games.length)return v18165BaseStageResults(stage);
   const rows=games.map(f=>{
    const h=v640Team(state,f.home),a=v640Team(state,f.away),r=f.result;
    if(!h||!a)return '';
    const pen=r?.pens?' <small>('+r.pens[0]+'-'+r.pens[1]+' pen.)</small>':'';
    return '<div class="v640-result-row v18165-national-summary-row"><span>'+v640Flag(f.home)+' '+esc(h.name)+'</span><b>'+r.home+' x '+r.away+pen+'</b><span>'+esc(a.name)+' '+v640Flag(f.away)+'</span><button type="button" class="btn small secondary" data-action="v18164-national-result-view" data-fixture="'+esc(f.id)+'">Detalhes da partida</button></div>';
   }).join('');
   modal(modalHead('Resultados de seleções',stage.label)+'<div class="modal-body"><div class="v640-result-list">'+rows+'</div></div><div class="modal-footer">'+button('close','Fechar','primary')+'</div>','national-results','wide');
  };
 }

 window.GestorFC=window.GestorFC||{};
 window.GestorFC.nationalMatchParity18164={
  ownTeamResolver:'v1888HumanId',
  editableOwnBoard:true,
  opponentBenchSameGeometry:true,
  nationalFixtureDetails:true,
  careerOriginIndependent:true,
  liveBenchDragValid:true,
  nationalBenchOrderedByPosition:true,
  initialNationalFreeAgents:true
 };
})();
</script>
'''
    if 'futbr-v18164-national-match-parity' not in html:
        html=html+'\n'+runtime

    required=[
      "ownTeamResolver:'v1888HumanId'",
      "opponentBenchSameGeometry:true",
      "v18164-national-result-view",
      "careerOriginIndependent:true",
      "v513SetView=function(mode)",
      "v18165OwnClickGuard",
      "v18165BaseStageResults",
      "justify-self:stretch!important",
      "v18166PrepareAiNationalOpponent",
      "v18167SortIds",
      "liveBenchDragValid:true",
      "nationalBenchOrderedByPosition:true",
      "v18167SeedNationalPools",
      "initialNationalFreeAgents:true"
    ]
    for marker in required:
        if marker not in html:
            fail(f'missing parity marker: {marker}')

    p.write_text(html,encoding='utf-8')
    print("national match parity applied")

if __name__=="__main__":
    main()
