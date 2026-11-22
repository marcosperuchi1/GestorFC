"""Move 18.375 display controls into existing Settings; scale fonts, never viewport."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

MARK='FUTBR_FONT_SETTINGS_18376'
BEGIN='/* FUTBR_SUPPORT_UI_18375 */'
END='window.GestorFC.render=render;v375Schedule();'

UI=r"""
/* FUTBR_SUPPORT_UI_18375 */
/* FUTBR_FONT_SETTINGS_18376 */
const v375StorageKey='futbr-display-18375';
const v376FontSteps=[90,100,110,120,125];
function v375Preferences(){
 try{const d=JSON.parse(localStorage.getItem(v375StorageKey)||'{}');
  return {scale:v376FontSteps.includes(Number(d.scale))?Number(d.scale):100};
 }catch(e){return {scale:100};}
}
let v375Pref=v375Preferences(),v375Pending=false;
// 18.375 had HTML zoom; remove it instead of scaling layout and buttons.
document.documentElement.style.removeProperty('zoom');
const v376FontBase=new WeakMap();
const v376FontSelector='h1,h2,h3,h4,h5,h6,p,label,a,button,td,th,small,summary,li,input,select,textarea,.tiny,.pill,.badge';
function v376TextCandidate(el){
 if(!el||!el.isConnected||el.closest('script,style,svg,[data-v376-font-ignore]'))return false;
 if(el.matches('span,.tiny,.pill,.badge')){
  if(el.parentElement?.closest('h1,h2,h3,h4,h5,h6,p,label,a,button,td,th,small,summary,li'))return false;
 }
 return true;
}
function v376CollectText(root=document){
 const nodes=[];
 if(root.nodeType===1&&root.matches(v376FontSelector)&&v376TextCandidate(root))nodes.push(root);
 for(const el of root.querySelectorAll(v376FontSelector))if(v376TextCandidate(el))nodes.push(el);
 return nodes;
}
function v376ApplyFontSize(){
 const nodes=v376CollectText();
 // Measure all original sizes first to avoid cumulative scaling of children.
 for(const el of nodes){
  if(v376FontBase.has(el))continue;
  const original=window.getComputedStyle(el);
  const px=Number.parseFloat(original.fontSize);
  if(!Number.isFinite(px)||px<=0)continue;
  v376FontBase.set(el,{px,inline:el.style.getPropertyValue('font-size'),
                      priority:el.style.getPropertyPriority('font-size')});
 }
 for(const el of nodes){
  const original=v376FontBase.get(el);
  if(!original)continue;
  if(v375Pref.scale===100){
   if(original.inline){
    if(el.style.getPropertyValue('font-size')!==original.inline||el.style.getPropertyPriority('font-size')!==original.priority)
     el.style.setProperty('font-size',original.inline,original.priority);
   }else if(el.style.getPropertyValue('font-size'))el.style.removeProperty('font-size');
  }else{
   const px=Math.round(original.px*v375Pref.scale)/100;
   if(el.style.getPropertyValue('font-size')!==px+'px'||el.style.getPropertyPriority('font-size')!=='important')
    el.style.setProperty('font-size',px+'px','important');
  }
 }
}
function v376SetFontScale(raw){
 const scale=Number(raw);
 if(!v376FontSteps.includes(scale))return;
 v375Pref.scale=scale;
 try{localStorage.setItem(v375StorageKey,JSON.stringify({scale}));}catch(e){}
 document.documentElement.style.removeProperty('zoom');
 v376ApplyFontSize();
}
const v375Style=document.createElement('style');v375Style.id='futbr-support-ui-style';
v375Style.textContent=`
.sidebar>.fbr-language-control{display:none!important}
.v376-display-card .v376-mode-actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:8px}
.v376-display-card .v376-mode-actions button{border:1px solid var(--line,#865e5e);border-radius:8px;padding:9px 13px;color:inherit;background:var(--panel-soft,#552121);cursor:pointer}
.v376-display-card .v376-mode-actions button:hover{filter:brightness(1.12)}
.v376-display-card .v376-mode-status{margin-top:8px}
.v376-display-card .field{margin-top:16px}
.v375-help{display:inline-flex;align-items:center;justify-content:center;font-size:12px;min-width:18px;height:18px;border:1px solid currentColor;background:transparent;color:inherit;border-radius:50%;margin-left:6px;cursor:help}
`;document.head.appendChild(v375Style);
function v375RemoveStrayText(){
 for(const n of [...document.body.childNodes,...(document.getElementById('app')?.childNodes||[])]){
  if(n.nodeType!==Node.TEXT_NODE)continue;
  const raw=(n.nodeValue||'').trim();
  if(raw&&!raw.replaceAll('/n','').replaceAll(String.fromCharCode(92)+'n','').trim())n.remove();
 }
}
async function v375Fullscreen(set){
 const w=window.__TAURI__?.window?.getCurrentWindow?.();
 if(w?.setFullscreen)return w.setFullscreen(set);
 if(set&&document.documentElement.requestFullscreen)return document.documentElement.requestFullscreen();
 if(!set&&document.fullscreenElement&&document.exitFullscreen)return document.exitFullscreen();
 throw Error('Modo janela indisponível neste ambiente.');
}
function v376BuildSettingsCard(grid){
 if(grid.querySelector('#v376-display-card'))return;
 const card=document.createElement('div');card.id='v376-display-card';card.className='v622-setting-card v376-display-card';
 card.innerHTML=`<h3>Exibição e acessibilidade</h3>
 <p>Altere somente as letras, sem ampliar a tela, os menus, os cartões ou os espaçamentos do jogo.</p>
 <div class="field"><label for="v376-font-size">Tamanho das fontes</label>
 <select id="v376-font-size"><option value="90">Pequena (90%)</option>
 <option value="100">Normal (100%)</option><option value="110">Grande (110%)</option>
 <option value="120">Muito grande (120%)</option><option value="125">Máxima (125%)</option></select></div>
 <div class="field"><label>Modo de exibição</label><div class="v376-mode-actions">
 <button type="button" data-v376-full="0">Modo janela</button>
 <button type="button" data-v376-full="1">Tela cheia</button></div>
 <p class="tiny muted v376-mode-status" role="status" aria-live="polite"></p></div>`;
 const first=grid.querySelector('.v622-setting-card');
 if(first)grid.insertBefore(card,first);else grid.appendChild(card);
 const picker=card.querySelector('#v376-font-size');picker.value=String(v375Pref.scale);
 picker.addEventListener('change',()=>v376SetFontScale(picker.value));
 card.querySelectorAll('[data-v376-full]').forEach(btn=>btn.addEventListener('click',async()=>{
  if(btn.disabled)return;
  btn.disabled=true;
  const status=card.querySelector('.v376-mode-status');
  try{await v375Fullscreen(btn.dataset.v376Full==='1');
   if(status)status.textContent=btn.dataset.v376Full==='1'?'Modo tela cheia ativado.':'Modo janela ativado.';
  }catch(e){if(status)status.textContent=e.message||String(e);}
  finally{btn.disabled=false;}
 }));
}
const v375Tooltips={
 'Modelo de desafio financeiro':'Altera custos operacionais e juros do clube ao longo da carreira. Compare as despesas no menu Clube & Finanças.',
 'Responsável pelas renovações':'No modo manual você controla cada contrato. No automático a diretoria negocia e a escolha acompanha o treinador.',
 'Renovação de contratos':'Automática: diretoria negocia. Manual: você controla as renovações; a preferência acompanha a carreira.'
};
function v375Mount(){
 v375RemoveStrayText();
 // The new controls are in the EXISTING Settings page, not a second sidebar item.
 const grid=document.querySelector('.v622-settings-grid');
 if(grid)v376BuildSettingsCard(grid);
 for(const label of document.querySelectorAll('label')){
  const key=Object.keys(v375Tooltips).find(k=>(label.textContent||'').includes(k));
  if(!key||label.querySelector('.v375-help'))continue;
  const b=document.createElement('button');b.className='v375-help';b.type='button';b.textContent='?';b.title=v375Tooltips[key];b.setAttribute('aria-label',v375Tooltips[key]);
  b.addEventListener('click',e=>{e.stopPropagation();e.preventDefault();if(typeof toast==='function')toast(v375Tooltips[key],'info');});label.appendChild(b);
 }
 if(v375Pref.scale!==100)v376ApplyFontSize();
}
function v375Schedule(){
 if(v375Pending)return;
 v375Pending=true;
 const schedule=window.requestAnimationFrame||((cb)=>setTimeout(cb,0));
 schedule(()=>{v375Pending=false;v375Mount();});
}
function v375NegotiateHints(){
 for(const id of ['bid-value','bid-wage']){
  const input=document.getElementById(id);
  if(!input||input.closest('.field')?.querySelector('.v375-money-preview'))continue;
  const output=document.createElement('small');output.className='v375-money-preview';
  output.style.display='block';output.style.marginTop='6px';output.style.opacity='.85';
  const update=()=>{const value=Number(input.value)||0;output.textContent='Valor: '+new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0}).format(value)+(id==='bid-wage'?' por jornada':'');};
  input.insertAdjacentElement('afterend',output);input.addEventListener('input',update);input.addEventListener('change',update);update();
 }
}
const v375OldShowBuy=showBuy;
showBuy=function(...args){const result=v375OldShowBuy.apply(this,args);queueMicrotask(v375NegotiateHints);return result;};
const v375PreviousRender=render;
render=function(...args){const value=v375PreviousRender.apply(this,args);v375Schedule();return value;};
window.GestorFC.render=render;
window.GestorFC.fontSettings18376={getScale:()=>v375Pref.scale,
 applyScale:scale=>v376SetFontScale(scale),
 hasPageZoom:()=>!!document.documentElement.style.getPropertyValue('zoom')};
v375Schedule();
"""
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_font_settings_18376.py <prepared-game-root>')
 root=Path(sys.argv[1]).resolve();path=root/'src/index.html';html=path.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('18.376 font patch applied twice')
 if html.count(BEGIN)!=1 or html.count(END)!=1:raise RuntimeError('18.375 UI anchors changed')
 a=html.index(BEGIN);b=html.index(END,a)+len(END);old=html[a:b]
 for required in ('document.documentElement.style.zoom=','.v375-open','v375Open()','v375NegotiateHints','v375RemoveStrayText','v375Tooltips'):
  if required not in old:raise RuntimeError('Unsafe UI replacement; missing '+required)
 check=subprocess.run(['node','--check','-'],input=UI,text=True,capture_output=True,timeout=30)
 if check.returncode:raise RuntimeError('New UI syntax error: '+check.stderr)
 html=html[:a]+UI+html[b:]
 if 'document.documentElement.style.zoom=' in html:raise RuntimeError('Global zoom still in game')
 if '.v375-open' in html or 'v375Open()' in html or 'v375-overlay' in html:raise RuntimeError('Duplicate settings navigation still in game')
 path.write_text(html,encoding='utf-8')
 report={'ok':True,'version':'18.376.0','fontOnlyNoGlobalZoom':True,'oneExistingSettingsPage':True,
 'noAdditionalSidebarButton':True,'modeWindowAndFullscreenInExistingSettings':True,
 'legacyFontPreferenceReused':True,'other18375SupportFixesPreserved':True,'saveAndWorldNotTouched':True,
 'sha256':hashlib.sha256(html.encode('utf-8')).hexdigest()}
 (root/'font-settings-18376-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
