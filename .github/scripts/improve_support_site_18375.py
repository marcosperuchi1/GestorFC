"""Add secure screenshot/PDF attachments to existing FutBR support page."""
from pathlib import Path
import sys,re,json,hashlib,subprocess
MARK='FUTBR_SUPPORT_ATTACHMENTS_18375'
JS=r'''
 /* FUTBR_SUPPORT_ATTACHMENTS_18375 */
 const v375Mime={ 'image/png':'png','image/jpeg':'jpg','image/webp':'webp','application/pdf':'pdf' };
 const v375Bucket='futbr-support',v375MaxSize=5*1024*1024;
 function v375Input(id){
  const wrap=document.createElement('div');wrap.className='field v375-attachments-field';
  const label=document.createElement('label');label.htmlFor=id;label.textContent='Anexos (PNG, JPG, WebP ou PDF; até 5 MB cada, até 3 arquivos)';
  const input=document.createElement('input');input.type='file';input.id=id;input.multiple=true;input.accept='.png,.jpg,.jpeg,.webp,.pdf';
  wrap.append(label,input);return wrap;
 }
 async function v375Upload(ticketId,files){
  if(!db||!state.user)throw Error('Entre na conta antes de enviar arquivos.');
  const list=[...(files||[])];if(list.length>3)throw Error('Selecione até três arquivos por envio.');
  let uploaded=0;
  for(const file of list){
   const ext=v375Mime[file.type];
   if(!ext||!file.size||file.size>v375MaxSize)throw Error('Arquivo inválido (tipo ou limite de 5 MB): '+file.name);
   const path=state.user.id+'/'+ticketId+'/'+crypto.randomUUID()+'.'+ext;
   const up=await db.storage.from(v375Bucket).upload(path,file,{upsert:false,contentType:file.type});
   if(up.error)throw Error('Falha no envio de '+file.name+': '+error(up.error));
   const metadata={ticket_id:ticketId,uploaded_by:state.user.id,object_path:path,
    original_name:file.name.slice(0,180),mime_type:file.type,file_size:file.size};
   const save=await db.from('support_attachments').insert(metadata);
   if(save.error)throw Error('Arquivo enviado, mas não registrado no chamado: '+error(save.error));
   uploaded++;
  }
  return uploaded;
 }
 async function v375Read(ticketId){
  const root=document.getElementById('v375-attachment-list');if(!root)return;
  const result=await db.from('support_attachments')
   .select('id,object_path,original_name,file_size').eq('ticket_id',ticketId).order('created_at',{ascending:true}).limit(50);
  if(!state.selected||state.selected.id!==ticketId||!root.isConnected)return;
  root.replaceChildren();
  if(result.error){root.textContent='Não foi possível carregar os anexos.';return;}
  const list=result.data||[];if(!list.length){root.textContent='Nenhum arquivo enviado.';return;}
  for(const item of list){
   const button=document.createElement('button');button.type='button';button.className='btn btn-secondary';
   button.textContent=item.original_name+' ('+Math.ceil(item.file_size/1024)+' KB)';
   button.addEventListener('click',async()=>{button.disabled=true;
    try{const res=await db.storage.from(v375Bucket).createSignedUrl(item.object_path,120);
     if(res.error)throw res.error;
     window.open(res.data.signedUrl,'_blank','noopener,noreferrer');
    }catch(e){flash('Não foi possível abrir anexo: '+error(e));}finally{button.disabled=false;}
   });root.appendChild(button);
  }
 }
 function v375MountTicket(t){
  const host=el('details');if(!host||!t||host.querySelector('#v375-files'))return;
  const section=document.createElement('section');section.id='v375-files';section.className='card v375-files';
  const title=document.createElement('h3');title.textContent='Arquivos e capturas de tela';
  const list=document.createElement('div');list.id='v375-attachment-list';list.textContent='Carregando anexos...';
  section.append(title,list);
  if(t.status!=='closed'&&String(t.user_id)===String(state.user?.id)){
   const field=v375Input('v375-reply-attachments'),input=field.querySelector('input');
   const button=document.createElement('button');button.type='button';button.className='btn btn-primary';button.textContent='Enviar arquivos';
   button.addEventListener('click',async()=>{
    if(state.busy||!state.selected||state.selected.id!==t.id||!input.files.length)return;
    state.busy=true;button.disabled=true;
    try{const count=await v375Upload(t.id,input.files);input.value='';flash(count+' arquivo(s) anexado(s).');await v375Read(t.id);}
    catch(e){flash('Erro ao enviar anexo: '+(e.message||String(e)));}
    finally{state.busy=false;button.disabled=false;}
   });section.append(field,button);
  }
  host.appendChild(section);v375Read(t.id);
 }
 function v375PrepareNew(){
  const form=el('newForm');if(form&&!el('v375-new-attachments')){
   const field=v375Input('v375-new-attachments');
   form.insertBefore(field,form.querySelector('.buttons')||form.lastElementChild);
  }
 }
'''
def main():
 path=Path(sys.argv[1]).resolve();source=path.read_text(encoding='utf-8')
 if MARK in source:raise RuntimeError('Patch already applied')
 anchor='function bind(){'
 if source.count(anchor)!=1:raise RuntimeError('Support controller not found')
 source=source.replace(anchor,JS+'\n'+anchor+'v375PrepareNew();',1)
 detail="if(el('replyForm'))el('replyForm').addEventListener('submit',reply);"
 if source.count(detail)!=1:raise RuntimeError('Ticket detail binding not found')
 source=source.replace(detail,detail+'v375MountTicket(t);',1)
 createStart=source.index('async function createTicket(evt){')
 createEnd=source.index('function bind(){',createStart)
 fragment=source[createStart:createEnd]
 reply="if(r.error){el('newError').textContent=error(r.error);return;}"
 if fragment.count(reply)!=1:raise RuntimeError('Ticket create response not found')
 fragment=fragment.replace(reply,reply+
  "if(el('v375-new-attachments')?.files?.length){try{await v375Upload(r.data.id,el('v375-new-attachments').files);}catch(ex){flash('Chamado aberto, mas anexo falhou: '+(ex.message||String(ex)));}}",1)
 source=source[:createStart]+fragment+source[createEnd:]
 source=source.replace('</style>',".v375-files{padding:16px;margin-top:16px}.v375-files button{margin:6px 8px 6px 0}.v375-attachments-field{margin:15px 0}</style>",1)
 code=re.search(r'<script id="futbr-support-js">([\s\S]*?)</script>',source)
 if not code:raise RuntimeError('Support inline script not found')
 result=subprocess.run(['node','--check','-'],input=code.group(1),text=True,capture_output=True)
 if result.returncode:raise RuntimeError(result.stderr[-2000:])
 path.write_text(source,encoding='utf-8')
 print(json.dumps({'ok':True,'supportAttachments':True,'sha256':hashlib.sha256(source.encode()).hexdigest(),'bytes':len(source)}))
if __name__=='__main__':main()
