#!/usr/bin/env python3
"""Smoke-test FutBR Support responsive pages and ticket workflow with a fake API."""
from pathlib import Path
from playwright.sync_api import sync_playwright

FAKE_JS = r"""
(function(){
 let account=null,seq=100;
 const tickets=[{id:'seed',ticket_no:89,user_id:'player',contact_email:'jogador@exemplo.com',
   category:'bug',platform:'windows',game_version:'18.342',
   subject:'Falha na classificacao da liga',description:'Jogo apresentou uma tabela errada no fim.',
   status:'open',priority:'normal',created_at:'2026-11-17T15:00:00Z',last_activity_at:'2026-11-17T15:00:00Z'}], messages=[];
 function table(name){
  const f={};
  return {
   select(){return this},eq(k,v){f[k]=v;return this},order(){return this},
   limit(){
     if(name==='support_tickets')return Promise.resolve({data:tickets.filter(x=>account&&(account.id==='admin'||x.user_id===account.id)),error:null});
     if(name==='support_messages')return Promise.resolve({data:messages.filter(x=>x.ticket_id===f.ticket_id),error:null});
     return Promise.resolve({data:[],error:null});
   },
   maybeSingle(){return Promise.resolve({data:name==='support_staff'&&account&&account.id==='admin'?{role:'admin'}:null,error:null});},
   insert(data){
     if(name==='support_tickets'){
       seq++;
       const t=Object.assign({id:'ticket-'+seq,ticket_no:seq,contact_email:account.email,status:'open',priority:'normal',
         created_at:new Date().toISOString(),last_activity_at:new Date().toISOString()},data);
       tickets.unshift(t);
       return {select(){return {single(){return Promise.resolve({data:{id:t.id},error:null})}}}};
     }
     if(name==='support_messages'){messages.push(Object.assign({id:'m'+messages.length,is_staff:account.id==='admin',
       created_at:new Date().toISOString()},data));return Promise.resolve({error:null});}
     throw new Error('bad table');
   },
   update(data){return {eq(k,v){return {select(){
      const t=tickets.find(x=>x[k]===v);if(t)Object.assign(t,data);
      return Promise.resolve({data:t?[{id:t.id}]:[],error:null});
   }}}};}
  };
 }
 window.supabase={createClient(){return {
  from:table,
  auth:{
   getUser(){return Promise.resolve({data:{user:account}})},
   signInWithPassword(p){account={email:p.email,id:p.email.indexOf('marcos')===0?'admin':'player'};return Promise.resolve({data:{user:account},error:null})},
   signOut(){account=null;return Promise.resolve({error:null})},
   onAuthStateChange(){return {data:{subscription:{unsubscribe(){}}}}}
  }
 }}};
})();
"""

def main():
    html=Path(__file__).resolve().parents[2]/"site-support"/"suporte.html"
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        for width,height in [(390,844),(844,390),(1280,800)]:
            page=browser.new_page(viewport={"width":width,"height":height})
            page.route("**/supabase.min.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body=FAKE_JS))
            page.goto(html.resolve().as_uri(),wait_until="load")
            page.locator("#email").fill("jogador@exemplo.com")
            page.locator("#password").fill("senha-falsa")
            page.locator("#loginBtn").click()
            page.locator("#app").wait_for(state="visible",timeout=5000)
            page.locator("#newBtn").click()
            page.locator("#subject").fill("Erro ao iniciar as férias")
            page.locator("#description").fill("O jogo travou ao salvar o calendário na terceira temporada.")
            page.locator("#createBtn").click()
            page.locator("#modal").wait_for(state="hidden",timeout=5000)
            page.locator("#details h2").wait_for(state="visible",timeout=5000)
            assert page.locator("#details h2").inner_text()=="Erro ao iniciar as férias"
            assert page.locator("#staffForm").count()==0
            page.locator("#replyText").fill("Consegui reproduzir ao abrir o save novamente.")
            page.locator("#replyForm button[type=submit]").click()
            page.locator(".message").first.wait_for(state="visible",timeout=5000)
            assert page.locator(".message").count()==1
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"),width
            page.close()
        admin=browser.new_page(viewport={"width":1280,"height":800})
        admin.route("**/supabase.min.js",lambda route:route.fulfill(status=200,content_type="application/javascript",body=FAKE_JS))
        admin.goto(html.resolve().as_uri(),wait_until="load")
        admin.locator("#email").fill("marcosperuchi1@gmail.com")
        admin.locator("#password").fill("senha-falsa")
        admin.locator("#loginBtn").click()
        admin.locator("#app").wait_for(state="visible",timeout=5000)
        admin.locator("[data-ticket='seed']").click()
        admin.locator("#adminStatus").wait_for(state="visible",timeout=5000)
        admin.locator("#adminStatus").select_option("resolved")
        admin.locator("#staffForm button[type=submit]").click()
        admin.wait_for_timeout(140)
        assert admin.locator(".detail-top .badge").get_attribute("data-status")=="resolved"
        browser.close()
    print("PASS: mobile/tablet/desktop login, ticket creation, reply, staff status update")

if __name__=="__main__":
    main()
