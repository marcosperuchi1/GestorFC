from __future__ import annotations
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_mls_vacation_ui.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")
    if "futbr-mls-vacation-18201-ui" in html:
        print("MLS vacation UI already patched")
        return
    if "mlsVacation18200" not in html:
        raise RuntimeError("correcao estrutural 18.200 da MLS ausente")

    terminal = r'''
<script id="futbr-mls-vacation-18201-ui">
(()=>{
 const G=window.GestorFC=window.GestorFC||{};
 function v18201PausedVacation(){
  const v=state?.vacation||{},sim=v53Sim||{};
  return !!state&&!state.seasonDone&&!sim.active&&!sim.starting&&!sim.syncing&&!!v.paused&&Number(v.remaining)>0;
 }
 function v18201NextButton(css='secondary small'){
  return button('v18201-vac-nextmatch',icon('arrow')+' Próxima partida',css,'title="Encerrar as férias e avançar até o próximo jogo do seu clube"');
 }
 function v18201RecoverNotice(){
  const v=state?.vacation;if(!v)return false;
  if(!/Playoff da MLS sem vencedor/i.test(String(v.reason||'')))return false;
  try{E.validate?.(state);}catch(e){console.warn('[FutBR] recuperação MLS:',e?.message||e);}
  v.active=false;v.paused=true;
  v.reason='Playoffs da MLS recuperados. Retome as férias ou avance até a próxima partida.';
  try{persist(false);}catch(e){}
  return true;
 }
 if(typeof v107HeaderButtons==='function'){
  const v18201BaseHeaderButtons=v107HeaderButtons;
  v107HeaderButtons=function(mode){
   const base=v18201BaseHeaderButtons(mode);
   return mode==='paused'?v18201NextButton('secondary small')+base:base;
  };
 }
 function v18201Decorate(){
  v18201RecoverNotice();
  const paused=v18201PausedVacation();
  const header=document.querySelector('#v109-header-vac-controls');
  if(paused&&header&&!header.querySelector('[data-action="v18201-vac-nextmatch"]')){
   delete header.dataset.sig;
   try{v107PaintVacationHeader?.(document.getElementById('app'));}catch(e){}
  }
  document.querySelectorAll('.v557-vac-actions').forEach(holder=>{
   const existing=holder.querySelector('[data-action="v18201-vac-nextmatch"]');
   if(!paused){existing?.remove();return;}
   if(!existing)holder.insertAdjacentHTML('afterbegin',v18201NextButton('secondary'));
  });
 }
 async function v18201TakeCommandAndAdvance(){
  if(!state||v53Sim?.active||v53Sim?.starting||v53Creating)return;
  if(state.seasonDone){toast('A temporada terminou. Use Próxima temporada.','warn');return;}
  const v=state.vacation||(state.vacation={});
  v.active=false;v.paused=false;v.remaining=0;v.untilSeason=false;
  v.reason='Você voltou ao comando para avançar até a próxima partida.';
  try{if(typeof vacationEpoch!=='undefined')vacationEpoch++;}catch(e){}
  try{await Promise.resolve(persist(false));}catch(e){console.warn('[FutBR] save ao retomar comando:',e?.message||e);}
  try{render();}catch(e){}
  return v1891AdvanceToNextMatch();
 }
 document.addEventListener('click',event=>{
  const target=event.target?.closest?.('[data-action="v18201-vac-nextmatch"]');
  if(!target)return;
  event.preventDefault();event.stopImmediatePropagation();target.disabled=true;
  Promise.resolve(v18201TakeCommandAndAdvance()).catch(e=>{
   toast('Falha ao avançar até a próxima partida: '+(e?.message||e),'error');
   target.disabled=false;
  });
 },true);
 const observer=new MutationObserver(()=>v18201Decorate());
 if(document.documentElement)observer.observe(document.documentElement,{subtree:true,childList:true});
 setTimeout(v18201Decorate,0);
 G.mlsVacationUI18201={version:'18.201',pausedVacationNextMatch:true,takesCommandBeforeAdvance:true,oldSafetyPauseNoticeRecovered:true};
})();
</script>
'''
    index_path.write_text(html.rstrip() + "\n\n" + terminal + "\n", encoding="utf-8")
    print("MLS paused-vacation next-match UI 18.201 applied")


if __name__ == "__main__":
    main()
