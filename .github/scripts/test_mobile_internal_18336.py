#!/usr/bin/env python3
"""18.336 mobile regression: squad, market, standings, tactics, menu and modal.

Synthetic fixtures use the real generated CSS/JS and reproduce the desktop
height traps that made the roster inaccessible on Android 18.335.
"""
from __future__ import annotations
import json,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def extract(src,name,tag):
    p=r'<'+tag+r' id="'+re.escape(name)+r'">([\s\S]*?)</'+tag+r'>'
    m=re.search(p,src)
    if not m:raise AssertionError(name+' missing from source')
    return m.group(1)

def make_table(prefix,columns,count,classes=''):
    head=''.join('<th>'+s+'</th>' for s in columns)
    rows=[]
    for n in range(count):
        cells=[]
        for i,h in enumerate(columns):
            if h.lower() in ('atleta','nome','jogador','clube','seleção','equipe'):
                value=f'<button class="table-button player-name" data-action="player" data-player="{prefix}-{n}">{prefix} jogador longo {n}</button>'
            elif h in ('Força','POT','PTS','Nota'):
                value=f'<span class="rating">{80+(n%10)}</span>'
            else:
                value=str(n+1+i)
            cls=' class="col-wage"' if h=='Salário' else ' class="col-contract"' if h=='Contrato' else ''
            cells.append('<td'+cls+'>'+value+'</td>')
        rows.append('<tr>'+''.join(cells)+'</tr>')
    return '<div class="table-scroll"><table class="'+classes+'"><thead><tr>'+head+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'

def page_fixture(kind):
    if kind=='squad':
        cols=['Atleta','Pos.','Idade','Força','POT','Físico','Moral','Situação','Contrato','Salário','Valor']
        rows=make_table('Atleta',cols,28,'v57-squad-table v58-squad-table')
        page='<div class="v57-squad-page v553-squad-page"><section class="panel v57-squad-panel">'
        page+='<div class="panel-head v553-squad-head"><div class="v57-squad-toolbar">'
        page+='<div class="v57-squad-summary"><span class="pill">28 ATLETAS</span></div>'
        page+='<div class="v57-squad-filters"><div class="field compact"><label>Posição</label><select><option>Todas</option></select></div><div class="field compact"><label>Ordenar</label><select><option>Força</option></select></div></div>'
        page+='</div><button class="btn" data-action="auto-lineup">Escalar melhor</button></div>'
        page+='<div id="squad-results">'+rows+'</div></section></div>'
        return page
    if kind=='league':
        cols=['#','Clube','PTS','J','V','E','D','GP','GC','SG']
        return '<section class="panel"><div class="panel-head"><h2>Classificação</h2></div>'+make_table('Clube',cols,20)+'</section>'
    if kind=='market':
        cols=['Atleta','Pos.','Clube','Força','Idade','Valor','Salário','Contrato','Situação']
        return '<div class="tabs"><button class="tab">Comprar</button><button class="tab">Vender</button><button class="tab">Empréstimos</button></div>'+make_table('Mercado',cols,16)
    if kind=='tactics':
        return '<div class="v5-workbench"><section class="panel"><div class="panel-head">Prancheta</div><div class="panel-body"><div class="v5-board" style="width:580px;min-width:580px;height:440px;border:1px solid green">Campo tático</div></div></section><div class="stack"><section class="panel"><div class="panel-head">Instruções</div><div class="v5-control-grid" style="display:grid;grid-template-columns:repeat(3,1fr)">'+''.join('<div class="field"><label>Instrução</label><select><option>Neutro</option></select></div>' for _ in range(8))+'</div></section></div></div>'
    if kind=='scout':
        cols=['Atleta','Clube','País','Idade','Força','Pos.','Potencial','Valor','Situação']
        return '<section class="panel"><h3>Olheiro</h3>'+make_table('Scout',cols,12)+'</section>'
    if kind=='dashboard':
        return '<div class="main-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">'+''.join('<section class="panel" style="min-width:400px"><h2>Indicador '+str(i)+'</h2><p>Resultado da rodada</p></section>' for i in range(3))+'</div>'
    raise ValueError(kind)

def mock_document(css,js,kind):
    style='''<style>
html,body{width:100%;height:100%;margin:0;background:#08120d;color:#eefcef;font-family:Arial,sans-serif}
*{box-sizing:border-box}.sidebar{background:#132619}.main-wrap{background:#0e1b13}
.panel{background:#13231a;border:1px solid #315d3e;border-radius:8px}
.table-scroll{overflow-x:auto}.table-scroll table{border-collapse:collapse;min-width:1180px}
th,td{border-bottom:1px solid #345348;padding:6px}
body.v614-squad-view .v553-squad-page{height:100%!important;overflow:hidden!important;display:flex!important}
body.v614-squad-view .v57-squad-panel{height:100%!important;overflow:hidden!important;display:flex!important;flex-direction:column!important}
body.v614-squad-view #squad-results{flex:1 1 0!important;height:auto!important;min-height:0!important;overflow:hidden!important}
body.v614-squad-view #squad-results>.table-scroll{height:100%!important;overflow-x:auto!important;overflow-y:auto!important}
.v5-workbench{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.main-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
</style>'''
    body='<div id="app"><aside class="sidebar"><div class="brand">FutBR Manager</div><nav class="nav">'
    body+='<div class="v556-nav-group open"><button class="v556-nav-parent" type="button">Elenco</button><div class="v556-nav-sub"><button data-action="nav" data-view="squad">Elenco</button><button data-action="nav" data-view="tactics">Táticas</button></div></div>'
    body+='<button data-action="nav" data-view="competitions">Competições</button></nav></aside>'
    body+='<div class="main-wrap"><header class="topbar"><div class="club-top">Meu clube</div><div class="top-actions"><button>Avançar Jornada</button></div></header>'
    body+='<main class="main" id="main-content"><div id="v555-page">'+page_fixture(kind)+'</div></main></div></div>'
    body+='<div id="modal-root"></div>'
    return '<!doctype html><html class="futbr-android-alpha"><head><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'+style+'<style>'+css+'</style></head><body class="v614-squad-view">'+body+'<script>'+js+'</script></body></html>'

def main(project):
    src=(Path(project)/'src'/'index.html').read_text(encoding='utf-8')
    assert 'FUTBR_UNEMPLOYED_RESUME_18334_BEGIN' in src
    css=extract(src,'futbr-mobile-responsive-18335','style')
    css+='\n'+extract(src,'futbr-mobile-pages-18336','style')
    js=extract(src,'futbr-mobile-touch-navigation-18335','script')
    js+='\n'+extract(src,'futbr-mobile-table-cards-18336','script')
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        try:
            for w,h in ((844,390),(740,360),(390,844)):
                context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1,is_mobile=True,has_touch=True)
                page=context.new_page()
                for kind in ('squad','league','market','tactics','scout','dashboard'):
                    page.set_content(mock_document(css,js,kind),wait_until='domcontentloaded')
                    page.evaluate('window.FutBRMobile18336.scan()')
                    main=page.locator('#main-content')
                    width=main.evaluate('(e)=>({client:e.clientWidth,scroll:e.scrollWidth})')
                    if width['scroll']>width['client']+3:raise AssertionError((w,h,kind,'horizontal main',width))
                    pagewidth=page.evaluate('document.documentElement.scrollWidth')
                    if pagewidth>w+4:raise AssertionError((w,h,kind,'horizontal root',pagewidth))
                    if kind in ('squad','league','market','scout'):
                        table=page.locator('table.futbr-mobile-cards')
                        assert table.count()==1,(w,h,kind,'cards absent')
                        container=page.locator('.table-scroll')
                        assert container.evaluate('(e)=>getComputedStyle(e).overflowX')!='auto',(w,h,kind,'horizontal scroll')
                        row=page.locator('tbody tr').first
                        rect=row.bounding_box()
                        assert rect and rect['width']<=w-14,(w,h,kind,rect)
                        assert page.locator('tbody tr:first-child td.futbr-mobile-primary').count()==1,(w,h,kind)
                        assert page.locator('tbody tr:first-child td[data-futbr-label]').count()>=5,(w,h,kind)
                        button=page.locator('tbody tr:first-child button[data-action="player"]')
                        assert button.count()>=1,(w,h,kind)
                        page.evaluate("window.__futbrClicks=0;document.addEventListener('click',function(ev){if(ev.target.closest('[data-action=player]'))window.__futbrClicks++;},true)")
                        button.first.click()
                        assert page.evaluate('window.__futbrClicks')==1,(w,h,kind,'player click')
                        if kind=='squad':
                            last=page.locator('tbody tr').last
                            last.scroll_into_view_if_needed(timeout=5000)
                            after=last.bounding_box()
                            assert after and after['y']>=0 and after['y']<=h+10,(w,h,'squad not reachable',after)
                            assert main.evaluate('(e)=>e.scrollHeight>e.clientHeight'),(w,h,'no vertical squad scroll')
                            assert page.locator('#squad-results').evaluate('(e)=>getComputedStyle(e).overflowY')=='visible'
                            assert page.locator('.v57-squad-filters select').first.evaluate('(e)=>e.getBoundingClientRect().height')>=38
                    if kind in ('tactics','dashboard'):
                        grid=page.locator('.v5-workbench' if kind=='tactics' else '.main-grid')
                        cols=grid.evaluate('(e)=>getComputedStyle(e).gridTemplateColumns')
                        assert len(cols.split(' '))<=1,(w,h,kind,'grid not stacked',cols)
                    if kind=='squad':
                        toggle=page.locator('#futbr-mobile-nav-button')
                        toggle.click()
                        assert 'futbr-mobile-nav-open' in page.locator('html').get_attribute('class')
                        nav=page.locator('.sidebar [data-action="nav"]').first
                        assert nav.evaluate('(e)=>e.getBoundingClientRect().height')>=38
                        nav.click()
                        assert 'futbr-mobile-nav-open' not in page.locator('html').get_attribute('class')
                    results.append({'viewport':[w,h],'screen':kind,'fits':True,'vertical':True})
                # modal is an independent update after first draw
                modal='<div class="overlay"><div class="modal"><div class="modal-body">'+make_table('Ficha',['Atleta','Idade','Posição','Força','Potencial','Clube','Jogos'],4)+'</div></div></div>'
                page.locator('#modal-root').evaluate('(e,html)=>e.innerHTML=html',modal)
                page.evaluate('window.FutBRMobile18336.scan()')
                assert page.locator('#modal-root table.futbr-mobile-cards').count()==1
                results.append({'viewport':[w,h],'screen':'player-modal','fits':True})
                context.close()
        finally:
            browser.close()
    report={'ok':True,'mobile':'18.336','pc_base':'18.334','tests':len(results),
            'resolutions':[[844,390],[740,360],[390,844]],'screens':results,
            'squad_card_tap':True,'vertical_scroll':True,'horizontal_scroll_removed':True,
            'unemployed_fix_present':True}
    (Path(project)/'mobile-internal-18336-tests.json').write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: test_mobile_internal_18336.py PROJECT')
    main(sys.argv[1])
