"""Install a DOM-only accessibility and display panel on the FutBR 18.374 UI."""
from pathlib import Path
import sys, json, hashlib, subprocess, re
MARK='FUTBR_SUPPORT_UI_18375'
UI=r"""
/* FUTBR_SUPPORT_UI_18375 */
const v375StorageKey='futbr-display-18375';
function v375Preferences(){try{const d=JSON.parse(localStorage.getItem(v375StorageKey)||'{}');return {scale:[90,100,110,120,125].includes(Number(d.scale))?Number(d.scale):100};}catch(e){return {scale:100};}}
let v375Pref=v375Preferences(),v375Dialog=null,v375Pending=false;
function v375Zoom(){document.documentElement.style.zoom=v375Pref.scale+'%';}
v375Zoom();
const v375Style=document.createElement('style');v375Style.id='futbr-support-ui-style';
v375Style.textContent=`
.v375-open{border:1px solid var(--line,#53646d);border-radius:9px;background:var(--panel,#22313a);color:inherit;cursor:pointer;padding:10px;margin:8px 10px;display:block;width:calc(100% - 20px)}
.v375-overlay{position:fixed;inset:0;z-index:2147483000;background:#000b;display:grid;place-items:center;padding:16px}
.v375-dialog{max-width:480px;width:100%;padding:22px;background:var(--panel,#22313a);color:var(--text,#fff);border:1px solid var(--line,#53646d);border-radius:14px;box-shadow:0 20px 70px #0009}
.v375-dialog h2{margin:0 0 10px}.v375-dialog p{line-height:1.5}
.v375-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:14px 0}
.v375-row button,.v375-dialog select,.v375-close{background:var(--panel-soft,#334953);border:1px solid var(--line,#53646d);color:inherit;border-radius:8px;padding:8px;cursor:pointer}
.v375-help{display:inline-flex;align-items:center;justify-content:center;font-size:12px;min-width:18px;height:18px;border:1px solid currentColor;background:transparent;color:inherit;border-radius:50%;margin-left:6px;cursor:help}
`;document.head.appendChild(v375Style);
function v375RemoveStrayText(){for(const n of [...document.body.childNodes])if(n.nodeType===Node.TEXT_NODE&&/^\\s*(?:(?:\\\\n|\\/n)\\s*)+$/.test(n.nodeValue||''))n.remove();}
async function v375Fullscreen(set){const w=window.__TAURI__?.window?.getCurrentWindow?.();if(w?.setFullscreen)return w.setFullscreen(set);if(set&&document.documentElement.requestFullscreen)return document.documentElement.requestFullscreen();if(!set&&document.fullscreenElement&&document.exitFullscreen)return document.exitFullscreen();throw Error('Modo janela indisponível neste ambiente.');}
function v375Close(){if(v375Dialog)v375Dialog.remove();v375Dialog=null;}
function v375Open(){
 if(v375Dialog)return;
 const overlay=document.createElement('div');overlay.id='v375-settings';overlay.className='v375-overlay';
 overlay.innerHTML=`<section role="dialog" aria-modal="true" aria-labelledby="v375-title" class="v375-dialog"><h2 id="v375-title">Configurações gerais</h2><p>Ajuste a interface sem alterar sua carreira.</p>
 <div class="v375-row"><label for="v375-scale">Tamanho dos textos e controles</label><select id="v375-scale"><option value="90">Pequeno (90%)</option><option value="100">Normal (100%)</option><option value="110">Grande (110%)</option><option value="120">Muito grande (120%)</option><option value="125">Máximo (125%)</option></select></div>
 <div class="v375-row"><span>Modo de exibição</span><span><button data-v375-full="1">Tela cheia</button> <button data-v375-full="0">Modo janela</button></span></div>
 <p>Para alterar o idioma, use o seletor existente no menu lateral.</p><button type="button" data-v375-close class="v375-close">Fechar</button></section>`;
 document.body.appendChild(overlay);v375Dialog=overlay;
 const scale=overlay.querySelector('#v375-scale');scale.value=String(v375Pref.scale);
 scale.addEventListener('change',()=>{v375Pref.scale=Number(scale.value);try{localStorage.setItem(v375StorageKey,JSON.stringify(v375Pref));}catch(e){}v375Zoom();});
 overlay.querySelectorAll('[data-v375-full]').forEach(b=>b.addEventListener('click',async()=>{b.disabled=true;try{await v375Fullscreen(b.dataset.v375Full==='1');}catch(e){if(typeof toast==='function')toast(e.message||String(e),'warn');}finally{b.disabled=false;}}));
 overlay.addEventListener('click',e=>{if(e.target===overlay||e.target.closest('[data-v375-close]'))v375Close();});
 overlay.addEventListener('keydown',e=>{if(e.key==='Escape'){e.stopPropagation();e.preventDefault();v375Close();}});
 overlay.querySelector('[data-v375-close]').focus({preventScroll:true});
}
const v375Tooltips={
 'Modelo de desafio financeiro':'Altera custos operacionais e juros do clube ao longo da carreira. Compare as despesas no menu Clube & Finanças.',
 'Renovação de contratos':'Automática: diretoria negocia. Manual: você controla as renovações; a preferência acompanha a carreira.'
};
function v375Mount(){
 v375RemoveStrayText();
 const sidebar=document.querySelector('.sidebar');
 if(sidebar&&!sidebar.querySelector('.v375-open')){
  const btn=document.createElement('button');btn.className='v375-open';btn.type='button';btn.textContent='⚙ Configurações gerais';
  btn.addEventListener('click',v375Open);const nav=sidebar.querySelector('.nav');if(nav)nav.insertAdjacentElement('afterend',btn);else sidebar.appendChild(btn);
 }
 for(const label of document.querySelectorAll('label')){
  const key=Object.keys(v375Tooltips).find(k=>(label.textContent||'').includes(k));
  if(!key||label.querySelector('.v375-help'))continue;
  const b=document.createElement('button');b.className='v375-help';b.type='button';b.textContent='?';b.title=v375Tooltips[key];b.setAttribute('aria-label',v375Tooltips[key]);b.addEventListener('click',e=>{e.stopPropagation();e.preventDefault();if(typeof toast==='function')toast(v375Tooltips[key],'info');});label.appendChild(b);
 }
}
function v375Schedule(){if(v375Pending)return;v375Pending=true;queueMicrotask(()=>{v375Pending=false;v375Mount();});}
const v375PreviousRender=render;
render=function(...args){const value=v375PreviousRender.apply(this,args);v375Schedule();return value;};
window.GestorFC.render=render;v375Schedule();
"""
def main():
 root=Path(sys.argv[1]).resolve();p=root/'src/index.html';s=p.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('Already installed')
 match=re.search(r'window\\.GestorFC\\.render=render;\\s*\\}\\)\\(\\);\\s*</script>',s)
 if not match:raise RuntimeError('Could not locate the final active UI closure')
 s=s[:match.start()]+'window.GestorFC.render=render;\\n'+UI+'\\n})();\\n</script>'+s[match.end():]
 # Compile the inserted JS fragment before touching the source.
 check=subprocess.run(['node','--check','-'],input=UI,text=True,capture_output=True)
 if check.returncode:raise RuntimeError(check.stderr)
 p.write_text(s,encoding='utf-8')
 (root/'support-ui-18375-install.json').write_text(json.dumps({'ok':True,'feature':MARK,'sha256':hashlib.sha256(s.encode()).hexdigest()},indent=2),encoding='utf-8')
if __name__=='__main__':main()
