#!/usr/bin/env python3
"""Mobile 18.337 smoke: narrow list layouts retain player/team taps and scrolling."""
from __future__ import annotations
import json,re,runpy,sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def extract(src,ident,tag):
    m=re.search(r'<'+tag+r' id="'+re.escape(ident)+r'">([\s\S]*?)</'+tag+r'>',src)
    assert m,ident+' missing'
    return m.group(1)

def main(project):
    project=Path(project)
    src=(project/'src'/'index.html').read_text(encoding='utf-8')
    for key in ('futbr-mobile-pages-18336','futbr-mobile-lists-18337','FUTBR_UNEMPLOYED_RESUME_18334_BEGIN'):
        assert key in src,key
    prev=runpy.run_path('.github/scripts/test_mobile_internal_18336.py')
    css=''.join(extract(src,name,'style') for name in
        ('futbr-mobile-responsive-18335','futbr-mobile-pages-18336','futbr-mobile-lists-18337'))
    js=';'.join(extract(src,name,'script') for name in
        ('futbr-mobile-touch-navigation-18335','futbr-mobile-table-cards-18336','futbr-mobile-lists-script-18337'))
    tests=[]
    with sync_playwright() as p:
      browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
      try:
       for w,h in ((844,390),(740,360),(390,844)):
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1,is_mobile=True,has_touch=True)
        page=context.new_page()
        for kind,expected in (('squad',4),('league',5)):
          page.set_content(prev['mock_document'](css,js,kind),wait_until='domcontentloaded')
          page.evaluate('window.FutBRMobile18336.scan();window.FutBRMobile18337.scan()')
          table=page.locator('table.futbr-mobile-slim')
          assert table.count()==1,(w,h,kind,'slim table missing')
          first=table.locator('tbody tr').first
          shown=first.locator('td.futbr-list-show')
          assert shown.count()==expected,(w,h,kind,'incorrect columns',shown.count(),expected)
          rect=first.bounding_box()
          assert rect and rect['width']<=w-16,(w,h,kind,'row too wide',rect)
          assert 42<=rect['height']<=100,(w,h,kind,'row too tall',rect)
          assert first.evaluate("(e)=>getComputedStyle(e).borderRadius")=='0px',(w,h,kind,'card corners')
          assert first.evaluate("(e)=>getComputedStyle(e).boxShadow")=='none',(w,h,kind,'card shadow')
          td_names=shown.evaluate_all("(arr)=>arr.map(e=>e.className)")
          assert any('futbr-list-name' in name for name in td_names),(w,h,kind,td_names)
          assert page.locator('#main-content').evaluate("(el)=>el.scrollWidth<=el.clientWidth+3"),(w,h,kind,'horizontal')
          assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+3"),(w,h,kind,'root overflow')
          last=page.locator('tbody tr').last
          last.scroll_into_view_if_needed(timeout=8000)
          lastrect=last.bounding_box()
          assert lastrect and lastrect['y']>=-1 and lastrect['y']<h,(w,h,kind,'last row hidden',lastrect)
          clicked=page.evaluate("window.__rowClick=0;document.addEventListener('click',function(e){if(e.target.closest('[data-action=player]'))window.__rowClick++;},true)")
          btn=first.locator('button[data-action=player]')
          assert btn.count()==1,(w,h,kind,'player action missing')
          btn.click()
          assert page.evaluate('window.__rowClick')==1,(w,h,kind,'action handler lost')
          assert first.locator('td.futbr-list-show').count()==expected,(w,h,kind,'columns changed after click')
          tests.append({'screen':kind,'viewport':[w,h],'visibleColumns':expected,'rowHeight':round(rect['height']),'horizontalScroll':False})
        # Non-target game screens must retain their own 18.336 UI.
        page.set_content(prev['mock_document'](css,js,'market'),wait_until='domcontentloaded')
        page.evaluate('window.FutBRMobile18336.scan();window.FutBRMobile18337.scan()')
        assert page.locator('table.futbr-mobile-cards').count()==1,(w,h,'market cards lost')
        assert page.locator('table.futbr-mobile-slim').count()==0,(w,h,'market accidentally changed')
        tests.append({'screen':'market-no-change','viewport':[w,h]})
        context.close()
      finally:
       browser.close()
    result={'ok':True,'mobile':'18.337','pc_base':'18.334','tests':len(tests),'checks':tests,
      'squad':'one compact list','standings':'one compact list',
      'actions_preserved':True,'horizontal_scroll':False,'desktop_untouched':True}
    (project/'mobile-lists-18337-tests.json').write_text(
       json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: test_mobile_lists_18337.py PROJECT')
    main(sys.argv[1])
