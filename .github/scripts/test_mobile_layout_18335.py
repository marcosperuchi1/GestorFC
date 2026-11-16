#!/usr/bin/env python3
"""Mobile layout regression: actual CSS, touch controls and short viewport.

Uses Playwright Chromium with mobile touch and multiple aspect ratios.
Run after apply_mobile_responsive_18335.py, before Android packaging.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def main(project:Path):
    project=project.resolve()
    src=(project/'src'/'index.html').read_text(encoding='utf-8')
    marker='futbr-mobile-responsive-18335'
    match=re.search(r'<style id="'+marker+r'">([\s\S]*?)</style>',src)
    assert match,'mobile style missing'
    css=match.group(1)
    matchjs=re.search(r'<script id="futbr-mobile-touch-navigation-18335">([\s\S]*?)</script>',src)
    assert matchjs,'mobile touch navigation missing'
    js=matchjs.group(1)
    assert 'FUTBR_UNEMPLOYED_RESUME_18334_BEGIN' in src,'18.334 missing'
    assert "const waiting=v18334ShouldWait()" in src,'18.334 button guard missing'
    assert 'FUTBR_SCOUT_RESPONSIVE_18331' in src,'18.331 scout missing'
    report=[]
    auth='''<main class="v548-auth" style="height:100vh;overflow:hidden">
        <div class="v548-auth-shell" style="min-width:1100px;height:100vh;max-height:100vh;display:grid">
          <section class="v548-auth-brand">Descrição do jogo</section>
          <section class="v548-auth-card" style="overflow:hidden;min-width:550px;height:650px">
            <div class="v548-auth-tabs"><button>Entrar</button><button>Criar conta</button></div>
            <h2>Bem-vindo de volta</h2>
            <form class="v548-auth-form">''' + ''.join(
              '<div class="field"><label>Email</label><input type="text" placeholder="E-mail"></div>'
              for _ in range(8)) + '''<button class="btn">Entrar</button></form>
          </section></div></main>'''
    welcome='''<main class="welcome v570-career-start" style="height:100vh;overflow:hidden">
       <div class="welcome-top"><div class="brand"><span class="brandname">FutBR Manager</span></div></div>
       <div class="welcome-main" style="display:grid;grid-template-columns:minmax(300px,.8fr) minmax(470px,1.2fr)">
         <section class="welcome-copy"><h1>Treine sua equipe</h1></section>
         <section class="setup-card v648-stable-card" style="height:640px;min-height:640px;overflow:hidden">
           <div class="flex between"><h2>Nova carreira</h2></div>
           <div class="country-filters"><div class="field"><label>País</label><select><option>Brasil</option></select></div><div class="field"><label>Divisão</label><select><option>Primeira</option></select></div></div>''' + ''.join(
             '<div class="field" style="margin-top:24px"><label>Escolha</label><input type="text"></div>'
              for _ in range(7)) + '''
           <div class="mt24"><button class="btn" data-action="new-career">INICIAR CARREIRA</button></div>
         </section></div></main>'''
    game='''<aside class="sidebar" style="width:290px;min-width:290px">
       <nav><button data-action="nav">Visão geral</button></nav>
       </aside><div class="main-wrap" style="width:1100px">
       <header class="topbar"><div class="club-top">Palmeiras</div><div class="top-actions"><button>Avançar Jornada</button></div></header>
       <main class="main" id="main-content" style="height:780px;overflow:hidden">
          <div id="v555-page"><h2>Minha carreira</h2>
           <div style="height:900px">Conteúdo da carreira</div></div>
       </main></div>'''
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        try:
            for width,height in ((844,390),(740,360),(390,844)):
                context=browser.new_context(viewport={'width':width,'height':height},
                    is_mobile=True,has_touch=True,device_scale_factor=1)
                page=context.new_page()
                head='<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>'+css+'</style>'
                for name,fixture in (('auth',auth),('welcome',welcome),('career',game)):
                    base='<html class="futbr-android-alpha"><head>'+head+'</head><body><div id="app">'+fixture+'</div><div id="modal-root"></div>'
                    script='<script>'+js+'</script>'
                    page.set_content(base+script+'</body></html>',wait_until='domcontentloaded')
                    selector={'auth':'.v548-auth','welcome':'.welcome','career':'.main-wrap'}[name]
                    measurement=page.locator(selector).evaluate("""el=>{
                      const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                      return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,
                        clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,
                        clientWidth:el.clientWidth,scrollWidth:el.scrollWidth,
                        overflowY:s.overflowY,display:s.display};
                    }""")
                    assert measurement['right']<=width+3, (name,width,measurement)
                    assert measurement['left']>=-3, (name,width,measurement)
                    if name=='auth':
                        assert page.locator('.v548-auth-brand').evaluate('(e)=>getComputedStyle(e).display')=='none'
                        assert measurement['overflowY']=='auto',(name,width,measurement)
                        card=page.locator('.v548-auth-card').bounding_box()
                        assert card['width']<=width+1 and card['x']>=-1,(width,card)
                    elif name=='welcome':
                        assert measurement['overflowY']=='auto',(name,width,measurement)
                        assert measurement['scrollHeight']>measurement['clientHeight'],(name,width,measurement)
                        page.locator('.welcome').evaluate('(el)=>el.scrollTop=el.scrollHeight')
                        btn=page.locator('[data-action="new-career"]').bounding_box()
                        assert btn and btn['y']+btn['height']<=height+8,(name,width,btn)
                    else:
                        assert page.locator('#futbr-mobile-nav-button').is_visible(),(width,height)
                        page.locator('#futbr-mobile-nav-button').click()
                        assert 'futbr-mobile-nav-open' in page.locator('html').get_attribute('class')
                        page.locator('.sidebar [data-action="nav"]').click()
                        assert 'futbr-mobile-nav-open' not in page.locator('html').get_attribute('class')
                        assert page.locator('#main-content').evaluate(
                            '(e)=>getComputedStyle(e).overflowY')=='auto'
                    report.append({'viewport':[width,height],'screen':name,
                                   'fit':True,'scroll':measurement['overflowY']})
                context.close()
        finally:
            browser.close()
    out={'ok':True,'pc_base':'18.334','android_layout':'18.335',
         'checks':report,'total':len(report)}
    (project/'mobile-responsive-18335-tests.json').write_text(
        json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: test_mobile_layout_18335.py <project>')
    main(Path(sys.argv[1]))
