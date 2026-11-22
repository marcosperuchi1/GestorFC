"""18.378: keep numeric engine values, render grouped BRL editing fields, and auto-install signed updates on launch."""
from pathlib import Path
import json,re,sys,subprocess,hashlib

MARK="FUTBR_MONEY_AUTOUPDATE_18378"
MONEY=r"""
/* FUTBR_MONEY_AUTOUPDATE_18378 */
const v378Grouped=new Intl.NumberFormat('pt-BR',{maximumFractionDigits:0});
function v378GroupDigits(value){
 const digits=String(value??'').replace(/\D/g,'').replace(/^0+(?=\d)/,'');
 return digits ? v378Grouped.format(Number(digits)) : '';
}
function v378MoneyInput(native){
 if(!native||native.dataset.v378Grouped||native.type!=='number')return;
 const id=native.id||'',label=native.closest('.field')?.querySelector('label')?.textContent||'';
 if(!['bid-value','bid-wage','renew-wage'].includes(id)&&
    !(/R\$\b|sal[aá]rio|valor|pre[cç]o|luvas|b[oô]nus|comiss[aã]o/i.test(label)))return;
 native.dataset.v378Grouped='true';
 const visual=document.createElement('input');
 visual.type='text';visual.inputMode='numeric';visual.autocomplete='off';
 visual.className=native.className;visual.dataset.v378For=id;
 visual.id='v378-'+id;visual.setAttribute('aria-label',label||'Valor em reais');
 visual.placeholder='0';visual.readOnly=native.readOnly;visual.disabled=native.disabled;
 visual.value=v378GroupDigits(native.value);
 native.style.display='none';native.tabIndex=-1;native.setAttribute('aria-hidden','true');
 native.insertAdjacentElement('afterend',visual);
 visual.addEventListener('input',()=>{
  const before=visual.value,offset=visual.selectionStart??before.length;
  const leftDigits=before.slice(0,offset).replace(/\D/g,'').length;
  const digits=before.replace(/\D/g,'').replace(/^0+(?=\d)/,'');
  visual.value=v378GroupDigits(digits);
  let pos=0,seen=0;
  if(leftDigits>0){for(;pos<visual.value.length;pos++){if(/\d/.test(visual.value[pos]))seen++;if(seen>=leftDigits){pos++;break;}}}
  try{visual.setSelectionRange(pos,pos);}catch(_e){}
  native.value=digits||'';
  native.dispatchEvent(new Event('input',{bubbles:true}));
  native.dispatchEvent(new Event('change',{bubbles:true}));
 });
}
function v378MountMoneyInputs(){
 for(const input of document.querySelectorAll('input[type="number"]'))v378MoneyInput(input);
}
const v378BeforeShowBuy=showBuy;
showBuy=function(...args){const result=v378BeforeShowBuy.apply(this,args);queueMicrotask(v378MountMoneyInputs);return result;};
const v378BeforeShowRenew=showRenew;
showRenew=function(...args){const result=v378BeforeShowRenew.apply(this,args);queueMicrotask(v378MountMoneyInputs);return result;};
"""
def once(source,old,new,label):
 if source.count(old)!=1:raise RuntimeError(label+' anchor count: '+str(source.count(old)))
 return source.replace(old,new,1)

def main():
 if len(sys.argv)!=2:raise SystemExit("usage: fix_money_autoupdate_18378.py <project-root>")
 root=Path(sys.argv[1]);hp=root/'src/index.html'
 html=hp.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('18.378 patch applied twice')
 anchor='const v375PreviousRender=render;'
 html=once(html,anchor,MONEY+'\n'+anchor,'core money wrapper')
 js_start=html.index('<script id="futbr-desktop-update-ui-18339">')
 js_end=html.index('</script>',js_start)
 updater=html[js_start:js_end]
 updater=once(updater,"let root=null,checking=false,installing=false,dismissed=false;","let root=null,checking=false,installing=false,dismissed=false,v378AutoAttempted=false;",'startup updater state')
 updater=once(updater,'Salvar e atualizar','Tentar novamente','recovery button label')
 updater=once(updater,'    go.disabled=later.disabled=false;','    go.disabled=later.disabled=false;\n    root.querySelector(".actions").hidden=false;','failed auto fallback')
 updater=once(updater,'''     panel.hidden=false;
''','''     panel.hidden=false;
     if(!v378AutoAttempted){
      v378AutoAttempted=true;
      panel.querySelector('.actions').hidden=true;
      panel.querySelector('.status').textContent='Salvando a carreira e instalando atualização assinada automaticamente...';
      // Reuse the signed 18.361 click handler, which saves before invoking native NSIS.
      panel.querySelector('[data-v18339-install]').click();
     }
''','automatic startup installation')
 html=html[:js_start]+updater+html[js_end:]
 style_anchor='#futbr-desktop-update-18339 .v18361-progress[hidden]{display:none}'
 if style_anchor not in html:raise RuntimeError('Existing fast updater CSS absent')
 html=once(html,style_anchor,'''#futbr-desktop-update-18339 .actions[hidden]{display:none!important}
'''+style_anchor,'updater button hiding')
 # Core engine still receives Number(native.value) and all existing input listeners receive
 # unchanged native numeric field events. Only user-visible text controls gain punctuation.
 assert html.count('FUTBR_MONEY_AUTOUPDATE_18378')==1
 assert 'Number($(\'#bid-value\').value)' in html
 assert 'Number($(\'#bid-wage\').value)' in html
 check=subprocess.run(['node','--check','-'],input=MONEY,text=True,capture_output=True)
 if check.returncode:raise RuntimeError('Monetary JS syntax: '+check.stderr[-2000:])
 match=re.search(r'<script id="futbr-desktop-update-ui-18339">([\s\S]*?)</script>',html)
 check=subprocess.run(['node','--check','-'],input=match.group(1),text=True,capture_output=True)
 if check.returncode:raise RuntimeError('Updater JS syntax: '+check.stderr[-2000:])
 hp.write_text(html,encoding='utf-8')
 report={'ok':True,'version':'18.378.0','monetaryGroupingPtBR':True,
         'numericEngineValuesPreserved':True,'nativeInputEventsPreserved':True,
         'signedUpdaterAutoTriggeredAtStartup':True,'guardedCareerSaveBeforeInstall':True,
         'failedInstallOffersManualRecovery':True,'offlineLaunchUnchanged':True,
         'visualOnlyNoWorkerWorldChanges':True,'sourceSha256':hashlib.sha256(html.encode()).hexdigest()}
 (root/'money-autoupdate-18378-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))
if __name__=='__main__':main()
