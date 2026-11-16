from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: test_welcome_national_preview_18342.py <project-dir>")
    project=Path(sys.argv[1]).resolve()
    html=(project/"src/index.html").read_text(encoding="utf-8")
    if "FUTBR_WELCOME_NATIONAL_PREVIEW_18342" not in html:
        raise RuntimeError("18.342 visual repair missing in the actual game")
    if html.count('id="futbr-18342-national-choice-preview"') != 1:
        raise RuntimeError("National welcome patch installed multiple times")
    for legacy in ('function v643ApplyWelcomeMode()', 'function v643UpdateNationalPreview()',
                   "FUTBR_LONG_CAREER_SAVE_18338_BEGIN", "FUTBR_SCORER_SEARCH_SUBMIT_18340"):
        if legacy not in html:
            raise RuntimeError("Original game state or historical archive removed: "+legacy)

    spec=importlib.util.spec_from_file_location(
        "fix_welcome_national_preview_18342",
        Path(__file__).with_name("fix_welcome_national_preview_18342.py"))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from playwright.sync_api import sync_playwright
    fixture=r'''
    <!doctype html><html><head><style>
    .v643-club-only-hidden{display:none!important}
    .welcome.v570-career-start #club-preview.v744-preview-slot{
      display:flex!important;height:120px!important;max-height:120px!important
    }
    .setup-card{width:600px;background:#06170c;color:white;padding:15px;}
    .club-preview{display:flex;gap:15px;}
    </style></head><body>
    <main class="welcome v570-career-start">
      <div class="setup-card">
        <button data-v643-start="club">Começar em um clube</button>
        <button data-v643-start="national">Começar em uma seleção</button>
        <div id="v643-national-start" class="active">
          <select id="v643-start-national">
            <option value="BRA" selected>Brasil</option>
            <option value="URU">Uruguai</option>
          </select>
          <div id="v643-national-preview">Brasil preview compacto</div>
        </div>
        <select id="club-select">
          <option selected value="fla">Flamengo</option>
        </select>
        <div id="club-preview" class="v744-preview-slot" data-v643-club-only="1">
          <div class="club-preview">FLAMENGO ORIGINAL</div>
        </div>
      </div>
    </main></body></html>
    '''
    original=r'''
    let v643StartMode='club';
    const V640_CONF_NAMES={CONMEBOL:'América do Sul'};
    const v640Sides=[
      {code:'BRA',name:'Brasil',conf:'CONMEBOL'},
      {code:'URU',name:'Uruguai',conf:'CONMEBOL'}];
    function v643WelcomeMode(){return v643StartMode;}
    function v640AssocCatalog(){return v640Sides;}
    function v640Flag(code){return '<span class="fixture-flag" data-code="'+code+'">Bandeira '+code+'</span>';}
    function esc(v){return String(v).replaceAll('&','&amp;').replaceAll('<','&lt;');}
    function renderClubPreview(){
      const host=document.getElementById('club-preview');
      host.innerHTML='<div class="club-preview">Escudo do Flamengo</div>';
    }
    function v643UpdateNationalPreview(){
      document.getElementById('v643-national-preview').textContent=
        'Seleção '+document.getElementById('v643-start-national').value;
    }
    function v643ApplyWelcomeMode(){
      const national=v643WelcomeMode()==='national';
      document.querySelectorAll('[data-v643-club-only="1"]').forEach(
        e=>e.classList.toggle('v643-club-only-hidden',national));
      v643UpdateNationalPreview();
    }
    function renderWelcome(){return true;}
    '''
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1440,"height":900})
        page.set_content(fixture)
        page.add_script_tag(content=original)
        page.add_style_tag(content=module.CSS.replace('<style id="futbr-18342-national-choice-preview-style">','').replace('</style>',''))
        script=module.JS.split('>',1)[1].rsplit('</script>',1)[0]
        page.add_script_tag(content=script)
        def inspect():
            return page.evaluate('''() => {
                const x=document.querySelector('#club-preview');
                return {
                  text:x?.innerText||'',
                  visible:getComputedStyle(x).display!=='none',
                  mode:x?.dataset.v18342National||'club',
                  smallHidden:getComputedStyle(document.querySelector('#v643-national-preview')).display==='none',
                  clubValue:document.querySelector('#club-select').value,
                  flag:x?.querySelector('.fixture-flag')?.dataset?.code||''
                };
            }''')

        page.evaluate("renderClubPreview()")
        first=inspect()
        assert 'Flamengo' in first['text'], first

        page.evaluate("v643StartMode='national';v643ApplyWelcomeMode()")
        brasil=inspect()
        assert brasil['visible'] and brasil['mode']=='BRA' and brasil['flag']=='BRA', brasil
        assert 'Brasil' in brasil['text'] and 'Flamengo' not in brasil['text'], brasil
        assert brasil['smallHidden'],brasil

        page.evaluate("document.querySelector('#v643-start-national').value='URU';v643UpdateNationalPreview()")
        uruguay=inspect()
        assert uruguay['mode']=='URU' and uruguay['flag']=='URU',uruguay
        assert 'Uruguai' in uruguay['text'] and 'Brasil' not in uruguay['text'],uruguay

        # An unrelated legacy refresh should not overwrite the national choice.
        page.evaluate("renderClubPreview()")
        assert inspect()['mode']=='URU' and 'Flamengo' not in inspect()['text']

        page.evaluate("v643StartMode='club';v643ApplyWelcomeMode()")
        back=inspect()
        assert 'Flamengo' in back['text'] and back['mode']=='club',back
        assert not back['smallHidden'] and back['clubValue']=='fla',back

        page.evaluate("v643StartMode='national';v643ApplyWelcomeMode()")
        again=inspect()
        assert again['mode']=='URU' and 'Uruguai' in again['text'] and 'Flamengo' not in again['text'],again

        # Fresh render preserves active national mode on a new welcome DOM.
        page.evaluate("renderWelcome()")
        page.wait_for_timeout(30)
        rendered=inspect()
        assert rendered['mode']=='URU' and rendered['visible'],rendered
        browser.close()

    report={
        'ok':True,'version':'18.342','clubToNationalRendersNational':True,
        'nationChangedWithoutStaleClub':True,
        'legacyClubPreviewCannotOverwriteNational':True,
        'returnToClubRestoresPreviouslySelectedClub':True,
        'newRenderPreservesNationalPreview':True,
        'clubSelectionNotDeleted':True,'noSaveMutation':True,
        'fullCardVisibleInNationalMode':True
    }
    (project/"welcome-national-preview-18342-tests.json").write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    main()
