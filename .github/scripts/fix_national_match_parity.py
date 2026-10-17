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

    runtime=r'''
<script id="futbr-v18164-national-match-parity">
(()=>{
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
  careerOriginIndependent:true
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
      "justify-self:stretch!important"
    ]
    for marker in required:
        if marker not in html:
            fail(f'missing parity marker: {marker}')

    p.write_text(html,encoding='utf-8')
    print("national match parity applied")

if __name__=="__main__":
    main()
