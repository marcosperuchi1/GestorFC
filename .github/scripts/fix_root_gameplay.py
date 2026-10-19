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
        """// Painéis deixam de ser pretos puros: derivam tons escuros da cor principal do clube ativo/consultado.
const v530BaseTheme=v51Theme;
v51Theme=function(t,preview){
 v530BaseTheme(t,preview);if(!t)return;
 const p=preview||v51Colors(t),primary=p[0];
 const r=document.documentElement;
 const vars={
  '--bg':v51Mix(primary,'#080c0b',.86),
  '--panel':v51Mix(primary,'#151b18',.80),
  '--panel2':v51Mix(primary,'#202622',.74),
  '--line':v51Mix(primary,'#6d7b71',.70)
 };
 Object.entries(vars).forEach(([k,v])=>r.style.setProperty(k,v));
};""",
        """// A superficie inteira deriva da cor do tema ativo. Em telas normais o tema
// ativo e a equipe comandada; fichas consultadas recebem a propria paleta.
function v18172SurfaceVars(primary){
 primary=v51Hex(primary)||'#386a8a';
 return {
  '--bg':v51Mix(primary,'#070b09',.78),
  '--panel':v51Mix(primary,'#111915',.70),
  '--panel2':v51Mix(primary,'#1b241f',.62),
  '--line':v51Mix(primary,'#829087',.54)
 };
}
function v18172ApplySurfaceToElement(el,primary){
 if(!el)return false;const vars=v18172SurfaceVars(primary);
 Object.entries(vars).forEach(([k,v])=>el.style.setProperty(k,v));
 el.style.setProperty('--v18172-career-primary',v51Hex(primary)||'#386a8a');
 return true;
}
function v18172ApplyCareerSurface(primary){return v18172ApplySurfaceToElement(document.documentElement,primary);}
const v530BaseTheme=v51Theme;
v51Theme=function(t,preview){
 v530BaseTheme(t,preview);if(!t)return;
 const p=preview||v51Colors(t),primary=p[0];
 v18172ApplyCareerSurface(primary);
};""",
        "career surface theme"
    )

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
        """function v128NationalTheme(code){
 if(!code||typeof v650NationalPalette!=='function')return false;
 const p=v650NationalPalette(code),r=document.documentElement;
 r.classList.add('v51-active');
 const mix=(a,b,w)=>{try{return v51Mix(a,b,w);}catch(e){return a;}};
 let accent=p.accent||p.primary;
 const vars={'--club-primary':p.primary,'--club-secondary':p.secondary,'--club-third':p.third,'--club-accent':accent,'--club-soft':p.primary+'26','--club-border':mix(p.primary,'#ffffff',.18)+'7a','--club-gradient':p.primary,'--on-accent':p.on||'#ffffff'};
 Object.entries(vars).forEach(([k,v])=>r.style.setProperty(k,v));r.dataset.visualClub='national:'+code;
 try{v664ApplyContrast?.();}catch(e){}try{v665ApplySolidSidebar?.();}catch(e){}
 return true;
}""",
        """function v128NationalTheme(code){
 if(!code||typeof v650NationalPalette!=='function')return false;
 const p=v650NationalPalette(code),r=document.documentElement;
 r.classList.add('v51-active');r.classList.remove('v664-welcome-blue');
 const mix=(a,b,w)=>{try{return v51Mix(a,b,w);}catch(e){return a;}};
 let accent=p.accent||p.primary;
 const vars={'--club-primary':p.primary,'--club-secondary':p.secondary,'--club-third':p.third,'--club-accent':accent,'--club-soft':p.primary+'26','--club-border':mix(p.primary,'#ffffff',.18)+'7a','--club-gradient':p.primary,'--on-accent':p.on||'#ffffff'};
 Object.entries(vars).forEach(([k,v])=>r.style.setProperty(k,v));r.dataset.visualClub='national:'+code;
 try{v18172ApplyCareerSurface(p.primary);}catch(e){}
 // A selecao consultada deve dominar a superficie inteira enquanto a ficha estiver aberta.
 if(typeof v18176NationalModalCode!=='undefined'&&v18176NationalModalCode){
  try{document.documentElement.dataset.visualClub='national:'+String(v18176NationalModalCode).toUpperCase();}catch(e){}
 }
 try{v664ApplyContrast?.();}catch(e){}try{v665ApplySolidSidebar?.();}catch(e){}
 return true;
}""",
        "national career surface theme"
    )

    html=once(
        html,
        """function v650ApplyNationalModalTheme(code){
 const modalEl=document.querySelector('#modal-root .v645-national-modal');if(!modalEl)return;
 modalEl.classList.add('v650-national-theme');modalEl.dataset.nationalTheme=String(code||'');modalEl.style.cssText+=';'+v650NationalThemeVars(code);
}""",
        """function v650ApplyNationalModalTheme(code){
 const modalEl=document.querySelector('#modal-root .v645-national-modal');if(!modalEl)return;
 const p=v650NationalPalette(code),mix=(a,b,w)=>{try{return v51Mix(a,b,w);}catch(e){return a;}};
 modalEl.classList.add('v650-national-theme');modalEl.dataset.nationalTheme=String(code||'');
 modalEl.style.cssText+=';'+v650NationalThemeVars(code);
 const vars={'--club-primary':p.primary,'--club-secondary':p.secondary,'--club-third':p.third,'--club-accent':p.accent||p.primary,'--club-soft':p.primary+'26','--club-border':mix(p.primary,'#ffffff',.18)+'7a','--club-gradient':p.primary,'--on-accent':p.on||'#ffffff'};
 Object.entries(vars).forEach(([k,v])=>modalEl.style.setProperty(k,v));
 try{v18172ApplySurfaceToElement(modalEl,p.primary);}catch(e){}
}""",
        "national profile full surface theme"
    )

    html=once(
        html,
        """function v657ApplyNationalModalTheme(code){
 const modalEl=document.querySelector('#modal-root .v645-national-modal');if(!modalEl)return;
 const p=typeof v650NationalPalette==='function'?v650NationalPalette(code):{primary:'#386A8A',secondary:'#D9E6EF',third:'#dfe6ee',accent:'#6b9bb7',on:'#11151b'};
 const accent=p.accent||p.primary,on=p.on||'#ffffff';
 const vars={
  '--national-primary':p.primary,'--national-secondary':p.secondary,'--national-third':p.third||p.secondary,
  '--national-accent':accent,'--national-on-accent':on,
  '--club-primary':p.primary,'--club-secondary':p.secondary,'--club-third':p.third||p.secondary,
  '--club-accent':accent,'--club-soft':`color-mix(in srgb,${p.primary} 15%,transparent)`,
  '--club-border':`color-mix(in srgb,${p.primary} 45%,var(--line))`,'--on-accent':on
 };
 modalEl.classList.add('v650-national-theme','v657-national-club-theme');
 modalEl.dataset.nationalTheme=String(code||'');
 for(const [k,v] of Object.entries(vars))modalEl.style.setProperty(k,v);
 const profile=modalEl.querySelector('.v645-national-profile');
 if(profile){profile.classList.add('v650-national-theme');for(const [k,v] of Object.entries(vars))profile.style.setProperty(k,v);}
}""",
        """function v657ApplyNationalModalTheme(code){
 const modalEl=document.querySelector('#modal-root .v645-national-modal');if(!modalEl)return;
 const p=typeof v650NationalPalette==='function'?v650NationalPalette(code):{primary:'#386A8A',secondary:'#D9E6EF',third:'#dfe6ee',accent:'#6b9bb7',on:'#11151b'};
 const accent=p.accent||p.primary,on=p.on||'#ffffff';
 const surface=typeof v18172SurfaceVars==='function'?v18172SurfaceVars(p.primary):{
  '--bg':p.primary,'--panel':p.primary,'--panel2':p.primary,'--line':p.primary
 };
 const vars={
  '--national-primary':p.primary,'--national-secondary':p.secondary,'--national-third':p.third||p.secondary,
  '--national-accent':accent,'--national-on-accent':on,
  '--club-primary':p.primary,'--club-secondary':p.secondary,'--club-third':p.third||p.secondary,
  '--club-accent':accent,'--club-soft':`color-mix(in srgb,${p.primary} 15%,transparent)`,
  '--club-border':`color-mix(in srgb,${p.primary} 45%,${surface['--line']})`,'--on-accent':on,
  ...surface
 };
 modalEl.classList.add('v650-national-theme','v657-national-club-theme');
 modalEl.dataset.nationalTheme=String(code||'');
 for(const [k,v] of Object.entries(vars))modalEl.style.setProperty(k,v);
 try{v18172ApplySurfaceToElement(modalEl,p.primary);}catch(e){}
 const profile=modalEl.querySelector('.v645-national-profile');
 if(profile){
  profile.classList.add('v650-national-theme');
  for(const [k,v] of Object.entries(vars))profile.style.setProperty(k,v);
  try{v18172ApplySurfaceToElement(profile,p.primary);}catch(e){}
 }
}""",
        "v657 national profile full surface theme"
    )

    # Criacao de carreira: a primeira passagem ja conhece o registro compacto que
    # originou cada jogador real. Guarda somente essa referencia transitoria para
    # a segunda passagem, evitando reconstruir milhares de Maps por nome.
    html=once(
        html,
        """        p.name=String(rp.name).slice(0,80);p.real=true;p.clubId=t.id;p.providerId=String(rp.providerId||'');p.ageEstimated=!rp.age;p.positionEstimated=!!rp.positionEstimated;p.sourceOrder=i;p.listed=i>14&&rng(s)<.15;""",
        """        p.name=String(rp.name).slice(0,80);p.real=true;p.clubId=t.id;p.providerId=String(rp.providerId||'');p.ageEstimated=!rp.age;p.positionEstimated=!!rp.positionEstimated;p.sourceOrder=i;p.listed=i>14&&rng(s)<.15;p.v18175SeedRoster=rp;""",
        "career seed direct reference"
    )

    html=once(
        html,
        """      const info=db[t.id],map=new Map((info?.players||[]).map(p=>[normName(p.name),p]));""",
        """      const info=db[t.id];""",
        "avoid repeated roster name maps"
    )

    html=once(
        html,
        """        const p=player(s,id),rp=p.real?map.get(normName(p.name)):null;""",
        """        const p=player(s,id),rp=p.real?(p.v18175SeedRoster||null):null;""",
        "reuse direct source record"
    )

    html=once(
        html,
        """        }else localizeGenerated(s,p,t.country);
      }""",
        """        }else localizeGenerated(s,p,t.country);
        if(p.v18175SeedRoster)delete p.v18175SeedRoster;
      }""",
        "drop transient source record"
    )

    # Plano Gratuito: bloqueio autoritativo de carreira por selecao.
    # Corrige a regra final 11.5C que antes fazia uma excecao explicita para
    # v128NationalStart e, portanto, deixava o Gratuito iniciar em selecao.
    html=once(
        html,
        """ const v128NationalStart=params?.options?.v643StartType==='national';
 const v128NationalStartCode=v128NationalStart?String(params?.options?.v643NationalCode||'BRA').toUpperCase():null;
 if(!v548FullAccess()&&!v128NationalStart){
  const allowed=v4Catalog.get(params?.options?.club);""",
        """ const v128NationalStart=params?.options?.v643StartType==='national';
 const v128NationalStartCode=v128NationalStart?String(params?.options?.v643NationalCode||'BRA').toUpperCase():null;
 if(!v548FullAccess()&&v128NationalStart){
  toast('Comecar uma carreira por selecao e um recurso exclusivo do Premium.','error');
  return;
 }
 if(!v548FullAccess()){
  const allowed=v4Catalog.get(params?.options?.club);""",
        "authoritative free national start gate"
    )

    html=once(
        html,
        """function v643ConvertNewCareerToNational(s,code){const root=v640EnsureState(s),t=root?.teams?.[code]""",
        """function v643ConvertNewCareerToNational(s,code){if(!v548FullAccess())throw Error('Carreira por selecao requer Premium.');const root=v640EnsureState(s),t=root?.teams?.[code]""",
        "national conversion premium guard"
    )

    html=once(
        html,
        """function v647CleanCareerStart(){
 const card=document.querySelector('.setup-card');if(!card)return;
 const modeSelect=card.querySelector('#v643-start-mode');
 if(modeSelect){const field=modeSelect.closest('.field');if(field)field.remove();else modeSelect.remove();}
 document.querySelectorAll('[data-v643-start]').forEach(x=>x.classList.toggle('active',x.dataset.v643Start===(v643StartMode||'club')));
 v643ApplyWelcomeMode();
}""",
        """function v647CleanCareerStart(){
 const card=document.querySelector('.setup-card');if(!card)return;
 const modeSelect=card.querySelector('#v643-start-mode');
 if(modeSelect){const field=modeSelect.closest('.field');if(field)field.remove();else modeSelect.remove();}
 if(typeof v548FullAccess==='function'&&!v548FullAccess()){
  v643StartMode='club';
  card.querySelectorAll('[data-v643-start="national"]').forEach(x=>x.remove());
  card.querySelector('#v643-national-start')?.remove();
  card.querySelectorAll('[data-v643-club-only="1"]').forEach(x=>x.classList.remove('v643-club-only-hidden'));
  const note=card.querySelector('.v548-free-notice');if(note)note.style.display='';
  const btn=card.querySelector('[data-action="new-career"]');if(btn)btn.innerHTML=icon('play')+' Comecar minha carreira';
  return;
 }
 document.querySelectorAll('[data-v643-start]').forEach(x=>x.classList.toggle('active',x.dataset.v643Start===(v643StartMode||'club')));
 v643ApplyWelcomeMode();
}""",
        "free start UI national removal"
    )

    html=once(
        html,
        """document.addEventListener('dragstart',e=>{const el=e.target.closest('[data-v5-player]');if(!el||el.disabled)return;v5Drag={id:el.dataset.v5Player,ctx:el.dataset.v5Context};v5Selection=v5Drag;if(v5Drag.ctx==='live')stopTimer();e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',JSON.stringify(v5Drag));v5MarkSelection();});""",
        """document.addEventListener('dragstart',e=>{const el=e.target.closest('[data-v5-player]');if(!el||el.disabled)return;if(el.dataset.v5Slot===undefined){e.preventDefault();return;}v5Drag={id:el.dataset.v5Player,ctx:el.dataset.v5Context};v5Selection=v5Drag;if(v5Drag.ctx==='live')stopTimer();e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',JSON.stringify(v5Drag));v5MarkSelection();});""",
        "reserve native drag guard"
    )

    html=once(
        html,
        """document.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse')return;const el=e.target.closest('[data-v5-player]');if(!el||el.disabled)return;v5Pointer={id:el.dataset.v5Player,ctx:el.dataset.v5Context,x:e.clientX,y:e.clientY,moved:false};});""",
        """let v18172PointerGhost=null;
function v18172RemovePointerGhost(){if(v18172PointerGhost){v18172PointerGhost.remove();v18172PointerGhost=null;}}
function v18172PointerGhostAt(p,e){
 if(!p?.el)return;
 if(!v18172PointerGhost){
  const rect=p.el.getBoundingClientRect(),cs=getComputedStyle(p.el),g=p.el.cloneNode(true);
  g.removeAttribute('id');g.removeAttribute('data-v5-player');g.removeAttribute('data-v5-slot');g.removeAttribute('draggable');
  g.disabled=true;g.setAttribute('aria-hidden','true');g.classList.add('v18172-drag-ghost');
  Object.assign(g.style,{position:'fixed',left:'0',top:'0',width:rect.width+'px',height:rect.height+'px',maxWidth:'none',margin:'0',zIndex:'2147483000',pointerEvents:'none',opacity:'.96',transition:'none',transformOrigin:'top left',background:cs.background,backgroundColor:cs.backgroundColor,border:cs.border,boxShadow:'0 14px 34px #0009',borderRadius:cs.borderRadius,color:cs.color});
  document.body.appendChild(g);v18172PointerGhost=g;
 }
 const ox=e.pointerType==='touch'?18:14,oy=e.pointerType==='touch'?18:14;
 v18172PointerGhost.style.transform='translate3d('+(e.clientX+ox)+'px,'+(e.clientY+oy)+'px,0) scale(.98)';
}
document.addEventListener('pointerdown',e=>{const el=e.target.closest('[data-v5-player]');if(!el||el.disabled)return;if(e.pointerType==='mouse'&&el.dataset.v5Slot!==undefined)return;v18172RemovePointerGhost();v5Pointer={id:el.dataset.v5Player,ctx:el.dataset.v5Context,x:e.clientX,y:e.clientY,moved:false,el,pid:e.pointerId};if(e.pointerType==='mouse'){v5Selection=v5Pointer;v5MarkSelection();}});""",
        "reserve pointer drag"
    )

    html=once(
        html,
        """document.addEventListener('pointermove',e=>{if(!v5Pointer)return;if(Math.hypot(e.clientX-v5Pointer.x,e.clientY-v5Pointer.y)>7){v5Pointer.moved=true;if(v5Pointer.ctx==='live')stopTimer();e.preventDefault();}},{passive:false});""",
        """document.addEventListener('pointermove',e=>{const p=v5Pointer;if(!p||p.pid!==e.pointerId)return;if(!p.moved&&Math.hypot(e.clientX-p.x,e.clientY-p.y)>7){p.moved=true;if(p.ctx==='live')stopTimer();}if(p.moved){e.preventDefault();v18172PointerGhostAt(p,e);}},{passive:false});""",
        "pointer drag ghost move"
    )

    html=once(
        html,
        """document.addEventListener('pointerup',e=>{const p=v5Pointer;v5Pointer=null;if(!p?.moved)return;v5IgnoreClick=Date.now()+500;e.preventDefault();const target=document.elementFromPoint(e.clientX,e.clientY),dest=target?.closest('[data-v5-player]')||target?.closest('[data-v5-vacant]')||target?.closest('[data-v5-board]');v5Execute(p,dest,e.clientX,e.clientY);});""",
        """document.addEventListener('pointerup',e=>{const p=v5Pointer;if(!p||p.pid!==e.pointerId)return;v5Pointer=null;if(!p.moved){v18172RemovePointerGhost();return;}v5IgnoreClick=Date.now()+500;e.preventDefault();const target=document.elementFromPoint(e.clientX,e.clientY),dest=target?.closest('[data-v5-player]')||target?.closest('[data-v5-vacant]')||target?.closest('[data-v5-board]');v18172RemovePointerGhost();v5Execute(p,dest,e.clientX,e.clientY);});""",
        "pointer drag ghost drop"
    )

    html=once(
        html,
        """document.addEventListener('pointercancel',()=>{v5Pointer=null;});""",
        """document.addEventListener('pointercancel',e=>{if(v5Pointer&&(!e.pointerId||v5Pointer.pid===e.pointerId))v5Pointer=null;v18172RemovePointerGhost();});""",
        "pointer drag ghost cancel"
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

    anchor="function v643ConvertNewCareerToNational(s,code){if(!v548FullAccess())throw Error('Carreira por selecao requer Premium.');const root=v640EnsureState(s),t=root?.teams?.[code],me=v641NormalizeCoach(s.coaches?.[s.userCoachId]),old=me?.clubId?E.team(s,me.clubId):E.team(s,s.user);"
    if anchor not in html:
        fail("national conversion anchor missing")
    helper=r'''
const V18170_NATIONAL_POOL_TARGET=Object.freeze({GOL:3,ZAG:5,LAT:4,VOL:4,MEI:5,ATA:5});
const V18171_NAME_POOLS=Object.freeze({
 PRK:{familyFirst:true,g:['Kwang-song','Tae-song','Chol-min','Yong-il','Song-guk','Kuk-chol','Hyok-chol','Il-gwan','Kum-song','Jong-hyok','Myong-song','Kwang-jin','Chol-jin','Yong-gwang','Song-chol','Hyok-jun','Min-chol','Kuk-jin','Tae-hyon','Chol-song'],s:['Kim','Ri','Pak','Choe','Kang','Han','Jang','Ro','Mun','An','Jon','Sin']},
 KOR:{familyFirst:true,g:['Min-jun','Ji-hoon','Seung-hyun','Dong-hyun','Hyun-woo','Jun-ho','Sung-min','Tae-ho','Young-su','Jae-sung','Woo-jin','Sang-ho'],s:['Kim','Lee','Park','Choi','Jung','Kang','Cho','Yoon','Jang','Lim','Han','Shin']},
 JPN:{familyFirst:false,g:['Haruto','Yuto','Sota','Riku','Ren','Kaito','Takumi','Daichi','Hiroto','Yuki','Ryota','Keita'],s:['Sato','Suzuki','Takahashi','Tanaka','Watanabe','Ito','Yamamoto','Nakamura','Kobayashi','Kato','Yoshida','Yamada']},
 CHN:{familyFirst:true,g:['Wei','Jun','Hao','Tao','Lei','Ming','Peng','Jian','Bo','Qiang','Kai','Chen'],s:['Wang','Li','Zhang','Liu','Chen','Yang','Huang','Zhao','Wu','Zhou','Xu','Sun']},
 LUS:{g:['Joao','Lucas','Gabriel','Matheus','Rafael','Pedro','Bruno','Caio','Felipe','Diego','Andre','Gustavo'],s:['Silva','Santos','Oliveira','Costa','Pereira','Almeida','Ferreira','Gomes','Martins','Carvalho','Ribeiro','Rocha']},
 HIS:{g:['Santiago','Mateo','Nicolas','Tomas','Joaquin','Martin','Diego','Facundo','Agustin','Franco','Ignacio','Federico'],s:['Garcia','Rodriguez','Martinez','Lopez','Gonzalez','Perez','Sanchez','Torres','Vargas','Castro','Herrera','Rojas']},
 ENG:{g:['James','Oliver','Jack','Harry','George','Noah','Liam','Ethan','Daniel','Samuel','Ryan','Nathan'],s:['Smith','Taylor','Brown','Wilson','Davies','Evans','Johnson','Walker','White','Clark','Lewis','Morgan']},
 FRA:{g:['Hugo','Theo','Lucas','Louis','Nathan','Enzo','Maxime','Antoine','Yanis','Romain','Julien','Adrien'],s:['Martin','Bernard','Dubois','Thomas','Robert','Durand','Leroy','Moreau','Laurent','Roux','Girard','Blanc']},
 GER:{g:['Lukas','Leon','Jonas','Felix','Niklas','Julian','Tim','Tobias','Florian','Simon','Jan','Moritz'],s:['Muller','Schmidt','Schneider','Fischer','Weber','Meyer','Wagner','Becker','Schulz','Hoffmann','Klein','Neumann']},
 SLA:{g:['Luka','Marko','Nikola','Ivan','Milan','Stefan','Aleksandar','Filip','Petar','Matej','Andrej','Viktor'],s:['Jovanovic','Petrovic','Markovic','Nikolic','Pavlovic','Kovacevic','Horvat','Novak','Kovac','Popovic','Ilic','Savic']},
 ARA:{g:['Omar','Ahmed','Mohamed','Youssef','Karim','Ali','Hassan','Mahmoud','Ibrahim','Mustafa','Hamza','Rami'],s:['Hassan','Ali','Mahmoud','Khalil','Saleh','Nasser','Hamdan','Mansour','Rahman','Hussein','Salem','Rashid']},
 AFR:{g:['Samuel','Daniel','Emmanuel','Joseph','David','Victor','Isaac','Ibrahim','Moussa','Yaya','Kofi','Thabo'],s:['Mensah','Boateng','Diallo','Traore','Keita','Camara','Toure','Kone','Ndlovu','Mokoena','Sow','Diop']},
 SEA:{g:['Adi','Rizky','Bayu','Fajar','Dimas','Agung','Arif','Minh','Quang','Huy','Arun','Vikram'],s:['Putra','Santoso','Pratama','Saputra','Nugroho','Wijaya','Nguyen','Tran','Le','Pham','Singh','Kumar']},
 INT:{g:['Alex','Daniel','Lucas','Martin','Victor','Nicolas','David','Samuel','Adrian','Marco','Leo','Elias'],s:['Martin','Costa','Novak','Meyer','Rossi','Garcia','Petrov','Nielsen','Kovac','Marin','Bauer','Jensen']}
});
function v18171NameFallback(code){
 const n=String(code||'').toUpperCase();
 if(V18171_NAME_POOLS[n])return V18171_NAME_POOLS[n];
 if(['HKG','TPE','MAC'].includes(n))return V18171_NAME_POOLS.CHN;
 if(['BRA','POR','ANG','MOZ','CPV','GNB'].includes(n))return V18171_NAME_POOLS.LUS;
 if(['ESP','ARG','URU','CHI','COL','PAR','ECU','PER','BOL','VEN','MEX','CRC','HON','GUA','SLV','PAN','DOM'].includes(n))return V18171_NAME_POOLS.HIS;
 if(['ENG','SCO','WAL','NIR','IRL','USA','CAN','JAM','TRI','GUY','AUS','NZL','FIJ','PNG','SOL','VAN'].includes(n))return V18171_NAME_POOLS.ENG;
 if(['FRA','BEL','SUI'].includes(n))return V18171_NAME_POOLS.FRA;
 if(['GER','AUT','NED','DEN','NOR','SWE','FIN','ISL'].includes(n))return V18171_NAME_POOLS.GER;
 if(['CRO','SRB','BIH','SVN','SVK','CZE','POL','UKR','BUL','MKD','MNE','ROU','HUN','GEO','ARM','AZE','KAZ'].includes(n))return V18171_NAME_POOLS.SLA;
 if(['MAR','ALG','TUN','EGY','KSA','QAT','UAE','IRN','IRQ','JOR','LBN','SYR','PSE','LBY','SDN','OMA','YEM','BHR','KUW'].includes(n))return V18171_NAME_POOLS.ARA;
 if(['GHA','NGA','CMR','KEN','UGA','TAN','ZAM','ZIM','RSA','SEN','CIV','MLI','BFA','GUI','GAM','SLE','LBR','BEN','TOG','COD','CGO'].includes(n))return V18171_NAME_POOLS.AFR;
 if(['THA','MAS','IDN','IND','VIE','SGP','PHI','MYA','CAM','LAO','BAN','PAK','NEP','SRI'].includes(n))return V18171_NAME_POOLS.SEA;
 return V18171_NAME_POOLS.INT;
}
function v18171NameKey(name){return String(name||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();}
function v18171NationalGeneratedName(s,code,id,used=new Set()){
 const n=String(code||'').toUpperCase(),familyFirst=['PRK','KOR','CHN','HKG','TPE','MAC'].includes(n);
 const originals=v640Eligible(s,n).filter(p=>p?.name&&!p.generatedNationalSupport&&!p.v18170InitialNationalFreeAgent);
 const givens=[],families=[];
 for(const p of originals){
  const parts=String(p.name||'').trim().split(/\s+/).filter(Boolean);if(parts.length<2)continue;
  if(familyFirst){families.push(parts[0]);givens.push(parts.slice(1).join(' '));}
  else{givens.push(parts[0]);families.push(parts.slice(1).join(' '));}
 }
 const fb=v18171NameFallback(n),g=[...new Set([...givens,...fb.g])].filter(Boolean),sn=[...new Set([...families,...fb.s])].filter(Boolean);
 let h=2166136261;for(const ch of String(n+'|'+id)){h^=ch.codePointAt(0);h=Math.imul(h,16777619);}h>>>=0;
 const pairTotal=Math.max(1,g.length*sn.length),pairStart=h%pairTotal;
 for(let k=0;k<pairTotal;k++){
  const z=(pairStart+k)%pairTotal,first=g[z%g.length],last=sn[Math.floor(z/g.length)%sn.length],name=(familyFirst?last+' '+first:first+' '+last).trim(),key=v18171NameKey(name);
  if(name&&key&&!used.has(key))return name;
 }
 const tripleTotal=Math.max(1,g.length*sn.length*Math.max(1,sn.length-1)),tripleStart=(h>>>5)%tripleTotal;
 for(let k=0;k<tripleTotal;k++){
  const z=(tripleStart+k)%tripleTotal,first=g[z%g.length],a=Math.floor(z/g.length)%sn.length,b=(a+1+Math.floor(z/(g.length*sn.length))%Math.max(1,sn.length-1))%sn.length;
  const last1=sn[a],last2=sn[b],name=(familyFirst?last1+' '+first+' '+last2:first+' '+last1+' '+last2).trim(),key=v18171NameKey(name);
  if(name&&key&&!used.has(key))return name;
 }
 const first=g[h%g.length]||'Alex',last=sn[(h>>>8)%sn.length]||'Silva',extra=sn[(h>>>16)%sn.length]||'Costa';
 return (familyFirst?last+' '+first+' '+extra:first+' '+last+' '+extra).trim();
}
function v18182NationalIndex(s){
 const map=new Map();
 for(const p of Object.values(s?.players||{})){
  const code=String(p?.natCode||'').toUpperCase();if(!code)continue;
  let list=map.get(code);if(!list){list=[];map.set(code,list);}list.push(p);
 }
 return map;
}
function v18171RepairNationalSupportNames(s,code,poolOverride=null){
 const n=String(code||'').toUpperCase(),players=poolOverride||v640Eligible(s,n),support=players.filter(p=>p?.generatedNationalSupport||p?.v18170InitialNationalFreeAgent),supportSet=new Set(support),used=new Set(players.filter(p=>!supportSet.has(p)).map(p=>v18171NameKey(p.name)).filter(Boolean));
 support.sort((a,b)=>String(a.id).localeCompare(String(b.id))).forEach(p=>{const clean=p.v18171LocalizedName&&p.natCode===n&&!/\d/.test(String(p.name||''));if(clean){used.add(v18171NameKey(p.name));return;}p.natCode=n;p.name=v18171NationalGeneratedName(s,n,p.id,used).replace(/\s*\d+\s*$/,'').trim();p.localized=true;p.nationalityKnown=true;p.v18171LocalizedName=true;used.add(v18171NameKey(p.name));});
 return support.length;
}
function v18171RepairAllNationalSupportNames(s){
 if(!s?.players)return 0;const index=v18182NationalIndex(s);let n=0;
 for(const a of v640AssocCatalog()){const code=String(a.code||'').toUpperCase();n+=v18171RepairNationalSupportNames(s,code,index.get(code)||[]);}
 return n;
}
function v18170NationalPoolBase(s,code,pos,conf,poolOverride=null){
 const all=poolOverride||v640Eligible(s,code),same=all.filter(p=>p.pos===pos).sort((a,b)=>E.overall(b)-E.overall(a)).slice(0,5),top=all.slice(0,18);
 const sample=same.length?same:top,avg=sample.length?E.avg(sample.map(E.overall)):(V640_CONF_BASE[conf]||62);
 return E.clamp(Math.round(avg),45,86);
}
function v18170EnsureNationalPool(s,code,f=null,poolOverride=null){
 const t=v640Team(s,code);if(!t||!s?.players)return {code,created:0};
 const target=V18170_NATIONAL_POOL_TARGET,pool=poolOverride||v640Eligible(s,code),key=f?v641NationalDisciplineKey(s,f):null;
 const available=f?pool.filter(p=>p&&!Number(p.injury)&&!(E.disciplineRecord(p,key).ban>0)):pool;
 const counts={GOL:0,ZAG:0,LAT:0,VOL:0,MEI:0,ATA:0},created=[],usedNames=new Set(pool.map(x=>v18171NameKey(x.name)).filter(Boolean));
 for(const p of available)if(Object.hasOwn(counts,p.pos))counts[p.pos]++;
 s.free=Array.isArray(s.free)?s.free:[];
 for(const pos of ['GOL','ZAG','LAT','VOL','MEI','ATA']){
  let missing=Math.max(0,(target[pos]||0)-(counts[pos]||0));
  while(missing-->0){
   const base=v18170NationalPoolBase(s,code,pos,t.conf,pool),age=20+Math.floor(E.rng(s)*10),id=E.createPlayer(s,pos,base,age),p=s.players[id];
   if(!p)throw Error('Falha ao criar jogador livre para '+t.name+'.');
   p.natCode=code;p.clubId=null;p.real=false;p.generatedNationalSupport=true;p.v18170InitialNationalFreeAgent=true;
   p.name=v18171NationalGeneratedName(s,code,id,usedNames);usedNames.add(v18171NameKey(p.name));p.localized=true;p.nationalityKnown=true;p.v18171LocalizedName=true;
   p.star=false;p.starCandidate=false;p.editorStarOverride=false;
   try{v200ApplyDatabaseOVR(p,base);}catch(e){}
   const now=E.overall(p);p.potential=Math.max(now,Math.min(90,now+(age<=22?5:age<=26?3:1)));
   pool.push(p);if(!s.free.includes(id))s.free.push(id);created.push(id);counts[pos]=(counts[pos]||0)+1;
  }
 }
 if(created.length)t.v18170InitialSupport=(t.v18170InitialSupport||0)+created.length;
 if(f){
  const playable=pool.filter(p=>p&&!Number(p.injury)&&!(E.disciplineRecord(p,key).ban>0))
   .sort((a,b)=>(typeof v165CallupScore==='function'?v165CallupScore(b)-v165CallupScore(a):E.overall(b)-E.overall(a))||(Number(a.age)||99)-(Number(b.age)||99));
  t.roster=playable.slice(0,26).map(p=>p.id);
 }
 return {code,created:created.length};
}
function v18170EnsureAllNationalPools(s){
 if(!s||s.v18170NationalPools?.done)return s?.v18170NationalPools||null;
 v640EnsureState(s);const index=v18182NationalIndex(s);let total=0,nations=0;const rows={};
 for(const a of v640AssocCatalog()){
  const code=String(a.code||'').toUpperCase();let pool=index.get(code);if(!pool){pool=[];index.set(code,pool);}
  const r=v18170EnsureNationalPool(s,code,null,pool);if(r.created){rows[code]=r.created;total+=r.created;nations++;}
 }
 s.v18170NationalPools={done:true,year:s.year,totalCreated:total,nations,createdByNation:rows,freeAgents:true,target:26,ovrModel:'existing-nationality-position-average',indexedBuild:true};
 return s.v18170NationalPools;
}
'''
    html=html.replace(anchor,helper+"\n"+anchor,1)

    html=once(
        html,
        " if(out&&op==='create'&&callParams?.options?.v643StartType==='national')v643ConvertNewCareerToNational(out,String(callParams.options.v643NationalCode||'BRA'));",
        " if(out&&op==='create')v18170EnsureAllNationalPools(out);\n if(out&&(op==='create'||op==='load'))v18171RepairAllNationalSupportNames(out);\n if(out&&op==='create'&&callParams?.options?.v643StartType==='national')v643ConvertNewCareerToNational(out,String(callParams.options.v643NationalCode||'BRA'));",
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
 v18170EnsureNationalPool(state,enemy,f);
 const enemyList=v1888NationalEligible(state,enemyT,f);
 if(enemyList.length<11)throw Error('Nao foi possivel montar 11 jogadores aptos para a selecao adversaria.');""",
        "old-save opponent repair"
    )


    # 18.179 - equilibrio de selecoes.
    # A simulacao automatica nacional deixa de depender quase so do Elo/rating.
    # O OVR real do melhor XI passa a ser a base; Elo vira apenas um ajuste pequeno.
    root_sig="function v640SimFixture(s,f){"
    root_helper=r"""function v18179NationalSimPower(s,code){
 const t=v640Team(s,code),xi=typeof v640BestXI==='function'?v640BestXI(s,code):[];
 const vals=(xi||[]).map(id=>s.players?.[id]).filter(Boolean).map(p=>Number(E.overall(p))).filter(Number.isFinite).sort((a,b)=>b-a).slice(0,11);
 const avg=vals.length?vals.reduce((sum,x)=>sum+x,0)/vals.length:65,elo=Number(t?.rating)||1400;
 return E.clamp(avg+E.clamp((elo-1400)/45,-4,4),45,94);
}
"""
    html=once(html,root_sig,root_helper+root_sig,"national root power helper")
    html=once(
        html,
        "const [h,a]=v640FixtureTeams(s,f),hp=v640TeamPower(s,f.home)+(f.neutral?0:1.2),ap=v640TeamPower(s,f.away),diff=(hp-ap)/11,lh=E.clamp(1.28*Math.exp(diff*.34),.18,3.9),la=E.clamp(1.16*Math.exp(-diff*.34),.16,3.7);let gh=v640Poisson(s,lh),ga=v640Poisson(s,la),pens=null,winner=null;",
        "const [h,a]=v640FixtureTeams(s,f),hp=v18179NationalSimPower(s,f.home),ap=v18179NationalSimPower(s,f.away),gap=E.clamp(hp-ap+(f.neutral?0:1.4),-30,30),lh=E.clamp(1.25*Math.exp(gap*.038),.14,3.8),la=E.clamp(1.25*Math.exp(-gap*.038),.14,3.8);let gh=v640Poisson(s,lh),ga=v640Poisson(s,la),pens=null,winner=null;",
        "national root OVR-weighted xG"
    )
    root_pen_old="if(f.knockout&&gh===ga){let ph=3+Math.floor(E.rng(s)*3),pa=3+Math.floor(E.rng(s)*3);if(ph===pa){if(E.rng(s)<.5)ph++;else pa++;}pens=[ph,pa];winner=ph>pa?f.home:f.away;}else if(gh!==ga)winner=gh>ga?f.home:f.away;"
    root_pen_new="if(f.knockout&&gh===ga){const pHome=E.clamp(.5+gap*.008,.32,.68),homePenWin=E.rng(s)<pHome,loser=2+Math.floor(E.rng(s)*4),win=loser+1;pens=homePenWin?[win,loser]:[loser,win];winner=homePenWin?f.home:f.away;}else if(gh!==ga)winner=gh>ga?f.home:f.away;"
    root_pos=html.find("hp=v18179NationalSimPower(s,f.home)")
    root_pen_pos=html.find(root_pen_old,root_pos)
    if root_pos<0 or root_pen_pos<0: fail("national root strength-aware penalties: ancora nao encontrada")
    html=html[:root_pen_pos]+root_pen_new+html[root_pen_pos+len(root_pen_old):]

    worker_sig="function simulateFixture(s,f){if(f.result)return f.result;"
    worker_helper=r"""function nationalPower(s,code){
 const t=team(s,code),xi=typeof natXI==='function'?natXI(s,code):[];
 const vals=(xi||[]).map(id=>s.players?.[id]).filter(Boolean).map(p=>Number(E.overall(p))).filter(Number.isFinite).sort((a,b)=>b-a).slice(0,11);
 const avg=vals.length?vals.reduce((sum,x)=>sum+x,0)/vals.length:65,elo=Number(t?.rating)||1400;
 return E.clamp(avg+E.clamp((elo-1400)/45,-4,4),45,94);
}
"""
    html=once(html,worker_sig,worker_helper+worker_sig,"national worker power helper")
    html=once(
        html,
        "const h=team(s,f.home),a=team(s,f.away),rh=Number(h?.rating)||1400,ra=Number(a?.rating)||1400,diff=(rh-ra)/210+(f.neutral?0:.12),lh=E.clamp(1.30*Math.exp(diff*.34),.18,3.8),la=E.clamp(1.16*Math.exp(-diff*.34),.16,3.6);let gh=poisson(s,lh),ga=poisson(s,la),pens=null,winner=null;",
        "const h=team(s,f.home),a=team(s,f.away),hp=nationalPower(s,f.home),ap=nationalPower(s,f.away),gap=E.clamp(hp-ap+(f.neutral?0:1.4),-30,30),lh=E.clamp(1.25*Math.exp(gap*.038),.14,3.8),la=E.clamp(1.25*Math.exp(-gap*.038),.14,3.8);let gh=poisson(s,lh),ga=poisson(s,la),pens=null,winner=null;",
        "national worker OVR-weighted xG"
    )
    worker_pen_old="if(f.knockout&&gh===ga){let ph=3+Math.floor(E.rng(s)*3),pa=3+Math.floor(E.rng(s)*3);if(ph===pa){if(E.rng(s)<.5)ph++;else pa++;}pens=[ph,pa];winner=ph>pa?f.home:f.away;}else if(gh!==ga)winner=gh>ga?f.home:f.away;"
    worker_pen_new="if(f.knockout&&gh===ga){const pHome=E.clamp(.5+gap*.008,.32,.68),homePenWin=E.rng(s)<pHome,loser=2+Math.floor(E.rng(s)*4),win=loser+1;pens=homePenWin?[win,loser]:[loser,win];winner=homePenWin?f.home:f.away;}else if(gh!==ga)winner=gh>ga?f.home:f.away;"
    worker_pos=html.find("hp=nationalPower(s,f.home)")
    worker_pen_pos=html.find(worker_pen_old,worker_pos)
    if worker_pos<0 or worker_pen_pos<0: fail("national worker strength-aware penalties: ancora nao encontrada")
    html=html[:worker_pen_pos]+worker_pen_new+html[worker_pen_pos+len(worker_pen_old):]

    html += r'''
<script id="futbr-root-18170-fixes">
window.GestorFC=window.GestorFC||{};

// A ficha nacional foi redefinida novamente em v737, depois dos wrappers v650/v657.
// Este wrapper fica no fim do documento e, portanto, sempre captura a implementacao
// final da ficha. A paleta vem do codigo da selecao CONSULTADA, nunca de state.userTeam.
function v18174ForceNationalProfileTheme(code){
 const modalEl=document.querySelector('#modal-root .v645-national-modal');if(!modalEl||typeof v650NationalPalette!=='function')return false;
 const p=v650NationalPalette(String(code||'').toUpperCase()),surface=typeof v18172SurfaceVars==='function'?v18172SurfaceVars(p.primary):{};
 const set=(el,k,v,important=false)=>{if(el&&v!=null)el.style.setProperty(k,String(v),important?'important':'');};
 const vars={...surface,'--national-primary':p.primary,'--national-secondary':p.secondary,'--national-third':p.third||p.secondary,'--national-accent':p.accent||p.primary,'--national-on-accent':p.on||'#fff','--club-primary':p.primary,'--club-secondary':p.secondary,'--club-third':p.third||p.secondary,'--club-accent':p.accent||p.primary,'--club-soft':p.primary+'26','--on-accent':p.on||'#fff'};
 for(const [k,v] of Object.entries(vars))set(modalEl,k,v,true);
 const profile=modalEl.querySelector('.v645-national-profile');for(const [k,v] of Object.entries(vars))set(profile,k,v,true);
 modalEl.dataset.nationalTheme=String(code||'').toUpperCase();
 const bg=surface['--bg']||'#09100c',panel=surface['--panel']||'#101814',panel2=surface['--panel2']||panel,line=surface['--line']||p.primary;
 set(modalEl,'background',`radial-gradient(ellipse at 88% 0,${p.primary}26,transparent 58%),${bg}`,true);
 set(modalEl,'border-color',line,true);
 const head=modalEl.querySelector(':scope>.modal-header');set(head,'background',`linear-gradient(90deg,${p.primary}26,transparent 72%),${panel2}`,true);set(head,'border-bottom-color',line,true);
 const body=modalEl.querySelector(':scope>.modal-body');set(body,'background',`radial-gradient(ellipse at 92% 0,${p.primary}1f,transparent 54%),${bg}`,true);
 const hero=modalEl.querySelector('.v737-national-profile-hero,.v640-hero');set(hero,'background',`radial-gradient(ellipse at top left,${p.primary}24,transparent 58%),${panel}`,true);set(hero,'border-color',line,true);
 const roster=modalEl.querySelector('.v737-national-profile-roster,.v640-roster');set(roster,'background',panel,true);set(roster,'border-color',line,true);
 const panelHead=roster?.querySelector(':scope>.panel-head');set(panelHead,'background',`linear-gradient(90deg,${p.primary}20,transparent 72%),${panel2}`,true);set(panelHead,'border-bottom-color',line,true);
 modalEl.querySelectorAll('.v737-national-profile-roster thead th,.v640-roster thead th').forEach(el=>set(el,'background',panel,true));
 return true;
}
function v18173PaintConsultedNationalProfile(code){
 const paint=()=>{
  try{if(v18176NationalModalCode&&v18176NationalModalCode!==String(code).toUpperCase())return;}catch(e){}
  try{if(typeof v650ApplyNationalModalTheme==='function')v650ApplyNationalModalTheme(code);}catch(e){}
  try{if(typeof v657ApplyNationalModalTheme==='function')v657ApplyNationalModalTheme(code);}catch(e){}
  try{v18174ForceNationalProfileTheme(code);}catch(e){}
 };
 paint();
 queueMicrotask(paint);
 if(typeof requestAnimationFrame==='function')requestAnimationFrame(paint);
 setTimeout(paint,0);
}
// A raiz visual (html) tambem precisa apontar para a selecao consultada.
let v18176NationalModalCode=null,v18176OpeningNationalCode=null;
const v18176BaseNationalTheme=typeof v128NationalTheme==='function'?v128NationalTheme:null;
if(v18176BaseNationalTheme){
 v128NationalTheme=function(code){
  const use=v18176NationalModalCode||v18176OpeningNationalCode||code;
  return v18176BaseNationalTheme(String(use||'').toUpperCase());
 };
}
const v18176BaseRefreshTheme=typeof v51RefreshTheme==='function'?v51RefreshTheme:null;
if(v18176BaseRefreshTheme){
 v51RefreshTheme=function(){
  if((v18176NationalModalCode||v18176OpeningNationalCode)&&typeof v128NationalTheme==='function'){
   return v128NationalTheme(v18176NationalModalCode||v18176OpeningNationalCode);
  }
  return v18176BaseRefreshTheme();
 };
}
const v18176BaseCloseModal=typeof closeModal==='function'?closeModal:null;
if(v18176BaseCloseModal){
 closeModal=function(...args){
  const opening=!!v18176OpeningNationalCode,hadNational=!!v18176NationalModalCode;
  if(!opening)v18176NationalModalCode=null;
  const out=v18176BaseCloseModal(...args);
  if(hadNational&&!opening){try{v18176BaseRefreshTheme?.();}catch(e){}}
  return out;
 };
}

const v18173BaseOpenNationalProfile=typeof v645OpenNationalProfile==='function'?v645OpenNationalProfile:null;
if(v18173BaseOpenNationalProfile){
 v645OpenNationalProfile=function(code){
  const n=String(code||'').toUpperCase();
  v18176OpeningNationalCode=n;
  try{
   const out=v18173BaseOpenNationalProfile(n);
   document.querySelectorAll('#modal-root .v645-national-modal').forEach(el=>{el.dataset.consultedNational=n;});
   v18176NationalModalCode=n;v18176OpeningNationalCode=null;
   try{v128NationalTheme?.(n);}catch(e){}
   try{v51RefreshTheme?.();}catch(e){}
   v18173PaintConsultedNationalProfile(n);
   requestAnimationFrame(()=>{if(v18176NationalModalCode===n){try{v128NationalTheme?.(n);v18173PaintConsultedNationalProfile(n);}catch(e){}}});
   return out;
  }catch(e){
   v18176OpeningNationalCode=null;v18176NationalModalCode=null;
   try{v18176BaseRefreshTheme?.();}catch(_){}
   throw e;
  }
 };
}

// Plano Gratuito: carreira por selecao e recurso Premium. A restricao existe
// tanto na interface quanto no caminho autoritativo de criacao.
function v18177FullAccess(){try{return typeof v548FullAccess==='function'&&!!v548FullAccess();}catch(e){return false;}}
function v18177EnforceFreeStartUI(){
 if(v18177FullAccess())return;
 try{
  v643StartMode='club';
  const sel=document.querySelector('#v643-start-mode');if(sel){sel.value='club';sel.querySelector('option[value="national"]')?.remove();}
  document.querySelectorAll('[data-v643-start="national"]').forEach(el=>el.remove());
  document.querySelector('#v643-national-start')?.classList.remove('active');
  document.querySelectorAll('[data-v643-club-only="1"]').forEach(el=>el.classList.remove('v643-club-only-hidden'));
  const note=document.querySelector('.v548-free-notice');if(note)note.style.display='';
  const card=document.querySelector('.setup-card');
  if(card&&!card.querySelector('#v18178-buy-premium')){
   const buy=document.createElement('button');
   buy.type='button';buy.id='v18178-buy-premium';buy.className='btn primary';buy.textContent='Comprar Premium';
   buy.style.cssText='display:inline-flex;align-items:center;justify-content:center;margin:12px 0;gap:8px';
   buy.onclick=()=>{try{window.open('https://futbrmanager.com.br/','_blank','noopener,noreferrer');}catch(e){toast('Acesse futbrmanager.com.br para comprar o Premium.','warn');}};
   (note||card).insertAdjacentElement('afterend',buy);
  }
  const btn=document.querySelector('[data-action="new-career"]');if(btn)btn.innerHTML=icon('play')+' Comecar minha carreira';
 }catch(e){}
}
const v18177BaseRenderWelcome=typeof renderWelcome==='function'?renderWelcome:null;
if(v18177BaseRenderWelcome){
 renderWelcome=function(...args){const out=v18177BaseRenderWelcome(...args);queueMicrotask(v18177EnforceFreeStartUI);return out;};
}
document.addEventListener('click',e=>{
 const b=e.target?.closest?.('[data-v643-start="national"]');if(!b||v18177FullAccess())return;
 e.preventDefault();e.stopImmediatePropagation();v643StartMode='club';toast('Carreira iniciando por selecao e exclusiva do Premium.','warn');v18177EnforceFreeStartUI();
},true);
const v18177BaseAct=typeof act==='function'?act:null;
if(v18177BaseAct){
 act=function(el){
  const a=el?.dataset?.action;
  if(a==='new-career'&&!v18177FullAccess()&&typeof v643WelcomeMode==='function'&&v643WelcomeMode()==='national'){toast('Carreira iniciando por selecao e exclusiva do Premium.','error');v18177EnforceFreeStartUI();return;}
  return v18177BaseAct(el);
 };
}
const v18177BasePrepare=typeof v53Prepare==='function'?v53Prepare:null;
if(v18177BasePrepare){
 v53Prepare=async function(op,params={}){
  if(op==='create'&&params?.options?.v643StartType==='national'&&!v18177FullAccess()){toast('Carreira por selecao requer Premium.','error');return;}
  return v18177BasePrepare(op,params);
 };
}
if(typeof v643PrepareNationalCareer==='function'){
 const v18177BaseNationalPrepare=v643PrepareNationalCareer;
 v643PrepareNationalCareer=async function(options={}){if(!v18177FullAccess()){toast('Carreira por selecao requer Premium.','error');return;}return v18177BaseNationalPrepare(options);};
}

window.GestorFC.root18170={nationalJumpLiveOverview:true,benchPositionOrder:true,nationalFreeAgentsAtCreation:true,localizedNationalFreeAgentNames:true,reservePointerSwap:true,dragGhost:true,dynamicCareerSurfaceTheme:true,consultedProfileOwnTheme:true,nationalProfileFinalOwnTheme:true,nationalProfileForcedSurface:true,nationalModalOwnRootTheme:true,nationalModalThemePinsV128:true,nationalRootSurfaceFollowsConsulted:true,premiumBuyOnWelcome:true,freeNationalStartBlocked:true,freeNationalStartCoreGate:true,nationalNamesNeverNumeric:true,fastCareerSeedRefs:true,liveDragUsesCoreV5Execute:true};
</script>
'''

    path.write_text(html,encoding="utf-8")
    print("root gameplay fixes applied")

if __name__=="__main__":
    main()
