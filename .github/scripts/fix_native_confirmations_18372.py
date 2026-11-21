"""Use the game's own confirmation dialog for named-career deletion."""
from pathlib import Path
import json
import sys


MARKER = 'FUTBR_NATIVE_CONFIRMATIONS_18372_BEGIN'
BLOCK = r'''/* FUTBR_NATIVE_CONFIRMATIONS_18372_BEGIN
   Requesting deletion never touches storage. Only the current dialog's explicit
   affirmative action may enter the original named-save deletion transaction. */
const v18372DeleteKind='futbr18372-delete-confirm';
let v18372DeleteRequest=null,v18372DeleteSequence=0;
function v18372DeletePanel(){return document.querySelector('#modal-root .modal');}
function v18372RestoreDeleteList(request,deleted=false){
 if(v18372DeleteRequest===request)v18372DeleteRequest=null;
 listDialog();
 setTimeout(()=>{
  if(modalKind!=='futbr125-list')return;
  const action=deleted?'futbr125-load':'futbr125-delete';
  const buttons=[...document.querySelectorAll('#modal-root [data-action="'+action+'"]')];
  const target=deleted?buttons[Math.min(request.index,buttons.length-1)]:
   buttons.find(button=>button.dataset.saveId===request.id);
  (target||document.querySelector('#modal-root [data-action="close"]'))?.focus({preventScroll:true});
 },0);
}
function v18372CancelDelete(){
 const request=v18372DeleteRequest;
 if(!request||request.phase!=='confirm')return false;
 v18372RestoreDeleteList(request);return true;
}
function deleteSlot(id){
 if(busy)return false;
 // A different dialog may have replaced this one. Its old token must expire.
 if(v18372DeleteRequest&&modalKind!==v18372DeleteKind)v18372DeleteRequest=null;
 if(v18372DeleteRequest)return false;
 const entry=findSlot(id);if(!entry||!belongsToAccount(entry))return false;
 const request={id,entry,name:entry.name,account:signedAccount(),activeId:slots.activeId,
  archived:!!entry.archived,index:Math.max(0,sorted().findIndex(item=>item.id===id)),
  token:++v18372DeleteSequence,phase:'confirm'};
 v18372DeleteRequest=request;
 modal(modalHead('Excluir carreira','Confirme a exclusão do save selecionado.')+
  `<div class="modal-body"><p id="futbr18372-delete-description">Excluir definitivamente <strong>${esc(entry.name)}</strong> deste dispositivo? Esta ação não pode ser desfeita.</p><p class="futbr125-data-warning mt16">Os outros saves e os backups JSON já exportados serão mantidos.</p></div>`+
  `<div class="modal-footer">${button('futbr18372-delete-cancel','Cancelar','secondary')}${button('futbr18372-delete-confirm','Excluir definitivamente','danger',`data-save-id="${esc(id)}" data-delete-token="${request.token}"`)}</div>`,v18372DeleteKind);
 const panel=v18372DeletePanel();panel?.classList.add('futbr125-dialog');
 panel?.setAttribute('aria-describedby','futbr18372-delete-description');
 setTimeout(()=>{
  if(v18372DeleteRequest===request&&request.phase==='confirm'&&modalKind===v18372DeleteKind)
   document.querySelector('#modal-root [data-action="futbr18372-delete-cancel"]')?.focus({preventScroll:true});
 },0);
 return true;
}
async function v18372ConfirmDelete(id,token){
 const request=v18372DeleteRequest;
 if(!request||request.phase!=='confirm'||busy||modalKind!==v18372DeleteKind||
    request.id!==id||String(request.token)!==String(token))return false;
 const entry=findSlot(id);
 if(entry!==request.entry||entry.name!==request.name||!belongsToAccount(entry)||
    signedAccount()!==request.account||slots.activeId!==request.activeId||
    !!entry.archived!==request.archived){
  v18372RestoreDeleteList(request);
  toast('A lista de carreiras mudou. Confira o save e abra a confirmação novamente.','warn');
  return false;
 }
 // Lock synchronously, before the first await, including repeated DOM clicks.
 request.phase='deleting';busy=true;
 const panel=v18372DeletePanel();panel?.setAttribute('aria-busy','true');
 panel?.querySelectorAll('button').forEach(button=>{button.disabled=true;});
 block('Excluindo '+entry.name+'...');
 let deleted=false;
 try{
  if(id===slots.activeId){
   await v52FlushSave();if(v52SavePromise)await v52SavePromise;
   const main=await get(BASE).catch(()=>null),previous=await get(BASE+':previous').catch(()=>null);
   await delMany([BASE,BASE+':meta',BASE+':previous']);
   slots.activeId=null;v260SavedMeta=null;saved=null;
   const chunks=[...new Set([...manifestKeys(main),...manifestKeys(previous)])];
   if(chunks.length)await delMany(chunks);
  }
  const manifest=await get(ARCHIVE+id).catch(()=>null);
  await delMany([ARCHIVE+id]);
  if(manifest?.format===FORMAT)await delMany(manifestKeys(manifest));
  slots.entries=slots.entries.filter(item=>item.id!==id);await writeIndex();deleted=true;
  toast('Save excluído.','success');
 }catch(error){toast('Erro ao excluir: '+(error?.message||String(error)),'error');}
 finally{busy=false;unblock();v18372RestoreDeleteList(request,deleted);}
 return deleted;
}
const v18372DeleteBaseCloseModal=closeModal;
closeModal=function(...args){
 if(modalKind===v18372DeleteKind&&v18372DeleteRequest){v18372CancelDelete();return;}
 return v18372DeleteBaseCloseModal.apply(this,args);
};
// The legacy document capture listener deliberately blocks Escape for other
// game dialogs. Handle only this confirmation before that listener runs.
window.addEventListener('keydown',event=>{
 if(modalKind!==v18372DeleteKind||!v18372DeleteRequest)return;
 if(event.key==='Escape'){
  event.preventDefault();event.stopImmediatePropagation();v18372CancelDelete();return;
 }
 if(event.key!=='Tab')return;
 const panel=v18372DeletePanel(),buttons=[...(panel?.querySelectorAll('button:not(:disabled)')||[])];
 event.stopImmediatePropagation();
 if(!buttons.length){event.preventDefault();return;}
 const first=buttons[0],last=buttons.at(-1),current=document.activeElement;
 if(!buttons.includes(current)){event.preventDefault();(event.shiftKey?last:first).focus();}
 else if(event.shiftKey&&current===first){event.preventDefault();last.focus();}
 else if(!event.shiftKey&&current===last){event.preventDefault();first.focus();}
},true);
/* FUTBR_NATIVE_CONFIRMATIONS_18372_END */
'''


def once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one source anchor, found {count}')
    return source.replace(old, new, 1)


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: fix_native_confirmations_18372.py <project>')
    root = Path(sys.argv[1])
    target = root / 'src' / 'index.html'
    source = target.read_text(encoding='utf-8')
    if MARKER not in source:
        start = source.index('async function deleteSlot(id){')
        end = source.index('// Ensure a newly created career gets its OWN identity', start)
        source = source[:start] + BLOCK + source[end:]
        source = once(source,
            " if(action==='futbr125-delete'){deleteSlot(el.dataset.saveId);return true;}",
            " if(action==='futbr125-delete'){deleteSlot(el.dataset.saveId);return true;}\n"
            " if(action==='futbr18372-delete-cancel'){v18372CancelDelete();return true;}\n"
            " if(action==='futbr18372-delete-confirm'){v18372ConfirmDelete(el.dataset.saveId,el.dataset.deleteToken);return true;}",
            'named-career affirmative/cancel routing')
        target.write_text(source, encoding='utf-8')
    report = {'ok': True, 'version': '18.372',
        'inGameDeleteConfirmation': MARKER in source,
        'noNativeConfirmInNamedSaves': 'confirm(' not in source[source.index('function listDialog(){'):source.index('// Ensure a newly created career gets its OWN identity')],
        'explicitAffirmativeBeforeStorage': 'request.phase=\'deleting\';busy=true;' in source,
        'cancelAndEscapePreserveSave': 'function v18372CancelDelete()' in source,
        'doubleClickAndStaleTokenGuard': 'String(request.token)!==String(token)' in source,
        'editionUnchangedByThisPatch': True}
    (root / 'native-confirmations-18372-install.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
