"""Regression of the original named-save router with isolated storage fixtures.

TEST_HOOK can be injected immediately before G.namedSaves125 for real-browser
tests. It refuses an existing career/index and is never shipped in the game.
"""
from pathlib import Path
import json
import re
import subprocess
import sys


TEST_HOOK = r'''
/* TEST_ONLY_NATIVE_CONFIRMATIONS_18372 */
window.__nativeConfirm18372Test={keys:[],audit:{indexWrites:0,deleteBatches:[]},
 async seed(){
  await ready;
  if(state||busy||slots.entries.length)throw Error('Use an empty isolated browser context for this fixture.');
  const prefix='test-only-native-18372:',active='fixture-active',archived='fixture-archive',keep='fixture-keep';
  const manifest=(id,key)=>({format:FORMAT,year:2026,day:12,
   root:{futbrSaveId:id,v1903CareerId:'fixture-career-'+id},collections:{players:{keys:[key],count:1}}});
  const values={
   [BASE]:manifest(active,prefix+'active'),[BASE+':meta']:{year:2026,day:12},
   [BASE+':previous']:manifest(active,prefix+'previous'),
   [prefix+'active']:[{id:'fixture-player',name:'Active fixture'}],
   [prefix+'previous']:[{id:'fixture-player',name:'Previous fixture'}],
   [ARCHIVE+archived]:manifest(archived,prefix+'archived'),
   [prefix+'archived']:[{id:'fixture-archived-player',name:'Archived fixture'}],
   [ARCHIVE+keep]:manifest(keep,prefix+'keep'),
   [prefix+'keep']:[{id:'fixture-keep-player',name:'Preserved fixture'}],
   [prefix+'unrelated']:{preserve:true}
  };
  for(const [key,value]of Object.entries(values))await put(key,value);
  slots={version:1,activeId:active,entries:[
   {id:active,name:'Carreira ativa de teste',archived:false,updatedAt:3,year:2026,day:12},
   {id:archived,name:'Carreira arquivada de teste',archived:true,updatedAt:2,year:2026,day:8},
   {id:keep,name:'Outra carreira preservada',archived:true,updatedAt:1,year:2026,day:4}
  ]};
  await writeIndex();this.keys=[INDEX,...Object.keys(values)];
  this.audit={indexWrites:0,deleteBatches:[]};listDialog();
  return {active,archived,keep,base:BASE,index:INDEX,archive:ARCHIVE,prefix};
 },
 async snapshot(){
  await writingIndex;
  const disk={};for(const key of this.keys)disk[key]=(await get(key))??null;
  return {disk,slots:JSON.parse(JSON.stringify(slots)),busy,modalKind,
   audit:JSON.parse(JSON.stringify(this.audit)),
   pending:typeof v18372DeleteRequest==='undefined'?null:v18372DeleteRequest?
    {id:v18372DeleteRequest.id,phase:v18372DeleteRequest.phase,token:v18372DeleteRequest.token}:null,
   focus:{action:document.activeElement?.dataset?.action||'',saveId:document.activeElement?.dataset?.saveId||''}};
 }
};
const v18372FixtureDeleteMany=delMany,v18372FixtureWriteIndex=writeIndex;
delMany=async function(keys){window.__nativeConfirm18372Test.audit.deleteBatches.push([...keys]);
 return v18372FixtureDeleteMany(keys);};
writeIndex=async function(...args){window.__nativeConfirm18372Test.audit.indexWrites++;
 return v18372FixtureWriteIndex.apply(this,args);};
'''


def run_browser_ui(page, artifacts_dir):
    """Exercise real named-save controls on the root's isolated Playwright page.

    The caller owns page/browser lifecycle and native-dialog dismissal. Only
    test fixtures seeded by TEST_HOOK are read or deleted here.
    """
    from copy import deepcopy

    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    screenshot = artifacts_dir / 'delete-confirmation-18372.png'
    native_dialogs = []

    def observe_native(dialog):
        native_dialogs.append({'type': dialog.type, 'message': dialog.message})

    def snapshot():
        return page.evaluate('() => window.__nativeConfirm18372Test.snapshot()')

    def control(action, save_id=None, header=False):
        selector = '#modal-root ' + ('.modal-header ' if header else '')
        selector += f'[data-action="{action}"]'
        if save_id is not None:
            selector += f'[data-save-id="{save_id}"]'
        return page.locator(selector)

    def wait_focus(action, save_id=None):
        page.wait_for_function('''({action,id}) => {
          const d=document.activeElement?.dataset;
          return d?.action===action&&(id===null||d.saveId===id);
        }''', arg={'action': action, 'id': save_id}, timeout=10000)

    def wait_list():
        page.wait_for_function('''async () => {
          const s=await window.__nativeConfirm18372Test.snapshot();
          return s.modalKind==='futbr125-list'&&!s.busy&&!s.pending;
        }''', timeout=20000)

    def open_delete(save_id):
        control('futbr125-delete', save_id).click()
        control('futbr18372-delete-cancel').wait_for(state='visible')
        wait_focus('futbr18372-delete-cancel')
        current = snapshot()
        assert current['modalKind'] == 'futbr18372-delete-confirm'
        assert current['pending']['id'] == save_id
        assert current['pending']['phase'] == 'confirm'
        assert not current['busy']
        return current

    def unchanged(before, after):
        assert after['disk'] == before['disk'], 'Cancel changed stored save data'
        assert after['slots'] == before['slots'], 'Cancel changed the career index'
        assert after['audit'] == before['audit'], 'Cancel performed a write or delete'
        assert not after['busy'] and not after['pending']

    def expected_deletion(before, after, save_id, fixture):
        expected = deepcopy(before['disk'])
        index = deepcopy(before['slots'])
        removed = []

        def remove_manifest(key):
            manifest = expected.get(key)
            if manifest and manifest.get('format') == 'GFC_SHARDED_171':
                for spec in manifest.get('collections', {}).values():
                    for chunk in spec.get('keys', []):
                        expected[chunk] = None
                        removed.append(chunk)
            if key in expected:
                expected[key] = None
            removed.append(key)

        if index['activeId'] == save_id:
            remove_manifest(fixture['base'])
            remove_manifest(fixture['base'] + ':previous')
            expected[fixture['base'] + ':meta'] = None
            removed.append(fixture['base'] + ':meta')
            index['activeId'] = None
        remove_manifest(fixture['archive'] + save_id)
        index['entries'] = [entry for entry in index['entries'] if entry['id'] != save_id]
        expected[fixture['index']] = index
        assert after['disk'] == expected, 'Deletion changed data outside the selected save'
        assert after['slots'] == index, 'Memory index differs from the committed index'
        assert after['audit']['indexWrites'] == before['audit']['indexWrites'] + 1, 'Deletion committed twice'
        new_batches = after['audit']['deleteBatches'][len(before['audit']['deleteBatches']):]
        actual_removed = [key for batch in new_batches for key in batch]
        assert sorted(actual_removed) == sorted(removed), 'Unexpected or repeated save-key deletion'
        return {'id': save_id, 'deletedKeys': actual_removed,
                'indexWrites': after['audit']['indexWrites'],
                'remaining': [entry['id'] for entry in index['entries']]}

    page.on('dialog', observe_native)
    try:
        page.wait_for_function('() => !!window.__nativeConfirm18372Test', timeout=90000)
        fixture = page.evaluate('() => window.__nativeConfirm18372Test.seed()')
        wait_list()
        original = snapshot()
        opened = open_delete(fixture['archived'])
        assert opened['disk'] == original['disk'] and opened['slots'] == original['slots']
        assert opened['audit'] == original['audit'], 'Opening the dialog touched storage'
        panel = page.locator('#modal-root .modal')
        assert panel.count() == 1
        assert panel.get_attribute('role') == 'dialog'
        assert panel.get_attribute('aria-modal') == 'true'
        assert panel.get_attribute('aria-describedby') == 'futbr18372-delete-description'
        viewport = page.evaluate('() => ({width:innerWidth,height:innerHeight})')
        bounds = panel.bounding_box()
        assert bounds and bounds['width'] > 0 and bounds['height'] > 0
        assert bounds['x'] >= -1 and bounds['y'] >= -1, 'Dialog starts outside the viewport'
        assert bounds['x'] + bounds['width'] <= viewport['width'] + 1
        assert bounds['y'] + bounds['height'] <= viewport['height'] + 1
        page.screenshot(path=str(screenshot), full_page=False, animations='disabled')

        # Use real keyboard navigation to test the modal focus boundaries.
        control('close', header=True).focus()
        page.keyboard.press('Shift+Tab')
        wait_focus('futbr18372-delete-confirm', fixture['archived'])
        page.keyboard.press('Tab')
        wait_focus('close')
        control('futbr18372-delete-cancel').click()
        wait_list()
        wait_focus('futbr125-delete', fixture['archived'])
        unchanged(original, snapshot())

        open_delete(fixture['archived'])
        page.keyboard.press('Escape')
        wait_list()
        wait_focus('futbr125-delete', fixture['archived'])
        unchanged(original, snapshot())

        open_delete(fixture['archived'])
        control('close', header=True).click()
        wait_list()
        wait_focus('futbr125-delete', fixture['archived'])
        unchanged(original, snapshot())

        open_delete(fixture['archived'])
        # Deliberately replay the same DOM button immediately. This goes through
        # the game's document router; no deletion helper is called by the test.
        double_click = page.evaluate('''() => {
          const b=document.querySelector('#modal-root [data-action="futbr18372-delete-confirm"]');
          if(!b||b.disabled)throw Error('Confirmation button was not ready');
          b.click();const disabledAfterFirst=b.disabled;b.click();
          return {attempts:2,disabledAfterFirst};
        }''')
        assert double_click['disabledAfterFirst'], 'Affirmative click did not lock synchronously'
        wait_list()
        after_archived = snapshot()
        archived_result = expected_deletion(original, after_archived, fixture['archived'], fixture)
        assert after_archived['slots']['activeId'] == fixture['active']

        open_delete(fixture['active'])
        control('futbr18372-delete-confirm').click()
        wait_list()
        after_active = snapshot()
        active_result = expected_deletion(after_archived, after_active, fixture['active'], fixture)
        assert after_active['slots']['activeId'] is None
        assert [entry['id'] for entry in after_active['slots']['entries']] == [fixture['keep']]
        assert after_active['disk'][fixture['archive'] + fixture['keep']] == original['disk'][fixture['archive'] + fixture['keep']]
        assert after_active['disk'][fixture['prefix'] + 'keep'] == original['disk'][fixture['prefix'] + 'keep']

        control('close', header=True).click()
        page.locator('#modal-root .modal').wait_for(state='detached')
        final = snapshot()
        assert final['modalKind'] is None and not final['busy'] and not final['pending']
        assert final['disk'] == after_active['disk'] and final['slots'] == after_active['slots']
        assert not native_dialogs, 'A native browser dialog was opened'
        return {'ok': True, 'version': '18.372', 'realNamedSaveControls': True,
                'inGameDeleteConfirmation': True, 'noNativeConfirm': True,
                'cancelPreservesStorage': True, 'escapePreservesStorage': True,
                'closePreservesStorage': True, 'focusInitiallyCancel': True,
                'focusRestoredAfterCancel': True, 'focusTrapWorks': True,
                'dialogWithinViewport': True, 'singleCommitOnDoubleClick': True,
                'explicitConfirmDeletesOnlySelected': True,
                'activeDeletionPreservesOtherCareers': True,
                'indexMatchesCommittedStorage': True, 'listClosedAtEnd': True,
                'isolatedFixturesOnly': True, 'testHookNotShipped': True,
                'nativeDialogs': native_dialogs, 'screenshot': str(screenshot),
                'bounds': bounds, 'viewport': viewport, 'doubleDOMClick': double_click,
                'archivedDeletion': archived_result, 'activeDeletion': active_result,
                'preservedCareer': fixture['keep'], 'finalIndex': final['slots']}
    finally:
        page.remove_listener('dialog', observe_native)


def extract(source, first, last):
    a = source.index(first)
    return source[a:source.index(last, a)]


FIXTURE = r'''
const assert=require('node:assert/strict');
const BASE='fixture-base',INDEX=BASE+':futbr125:index',ARCHIVE=BASE+':futbr125:archive:',FORMAT='GFC_SHARDED_171';
let slots,state=null,saved=null,v260SavedMeta=null,account='owner',busy=false,v52SavePromise=null;
let storage=new Map(),writes=0,deletions=[],flushes=0,failDelete=false,gate=null,modalKind=null;
const notices=[],timers=[],modalCalls=[],listeners={window:{},document:{}};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const setTimeout=cb=>{timers.push(cb);return timers.length;};
function flushTimers(){while(timers.length)timers.shift()();}
function element(action,id,token){return {dataset:{action,...(id?{saveId:id}:{}),...(token?{deleteToken:token}:{})},disabled:false,
 focus(){document.activeElement=this;},closest(selector){return selector==='[data-action]'?this:null;}};}
let buttons=[],panel={classList:{add(){}},attributes:{},setAttribute(k,v){this.attributes[k]=v;},
 querySelectorAll(selector){return selector==='button:not(:disabled)'?buttons.filter(b=>!b.disabled):buttons;}};
const document={activeElement:null,
 addEventListener(type,cb,capture=false){(listeners.document[type]??=[]).push({cb,capture});},
 querySelector(selector){if(selector==='#modal-root .modal')return panel;
  const match=selector.match(/data-action="([^"]+)"/);return match?buttons.find(b=>b.dataset.action===match[1])||null:null;},
 querySelectorAll(selector){const match=selector.match(/data-action="([^"]+)"/);
  return match?buttons.filter(b=>b.dataset.action===match[1]):[];}};
const window={GestorFC:{},addEventListener(type,cb,capture=false){(listeners.window[type]??=[]).push({cb,capture});}};
const button=(action,label,kind='',attrs='')=>`<button type="button" class="btn ${kind}" data-action="${action}" ${attrs}>${label}</button>`;
const modalHead=(title,subtitle)=>`<header><h2 id="dialog-title">${title}</h2><p>${subtitle}</p>${button('close','Fechar')}</header>`;
function modal(html,kind){modalKind=kind;modalCalls.push({html,kind});buttons=[];panel.attributes={};
 for(const m of html.matchAll(/<button\b([^>]*)>/g)){
  const a=m[1],action=a.match(/data-action="([^"]+)"/)?.[1];if(!action)continue;
  buttons.push(element(action,a.match(/data-save-id="([^"]+)"/)?.[1],a.match(/data-delete-token="([^"]+)"/)?.[1]));
 }
 setTimeout(()=>buttons[0]?.focus());
}
let closeModal=()=>{modalKind=null;buttons=[];};
const findSlot=id=>slots.entries.find(e=>e.id===id),signedAccount=()=>account;
const belongsToAccount=entry=>!entry?.owner||entry.owner===account;
const sorted=()=>slots.entries.filter(belongsToAccount).slice().sort((a,b)=>b.updatedAt-a.updatedAt);
function listDialog(){modalKind='futbr125-list';buttons=[];
 for(const s of sorted())buttons.push(element('futbr125-load',s.id),element('futbr125-delete',s.id));
 buttons.push(element('close'));setTimeout(()=>buttons[0]?.focus());}
const get=async key=>{if(gate)await gate;return storage.get(key);};
const delMany=async keys=>{if(failDelete)throw Error('fixture storage failure');
 for(const key of keys){storage.delete(key);deletions.push(key);}};
const manifestKeys=m=>m?.format===FORMAT?Object.values(m.collections).flatMap(x=>x.keys):[];
const writeIndex=async()=>{writes++;storage.set(INDEX,JSON.parse(JSON.stringify(slots)));};
const v52FlushSave=async()=>{flushes++;};
const block=()=>{},unblock=()=>{},toast=(text,type)=>notices.push({text,type});
const confirm=()=>{throw Error('Native confirm must never be called');};
function seed(){
 account='owner';busy=false;modalKind=null;buttons=[];deletions=[];writes=0;flushes=0;notices.length=0;
 timers.length=0;modalCalls.length=0;failDelete=false;gate=null;state=null;saved={fixture:'saved'};v260SavedMeta={fixture:'meta'};
 slots={version:1,activeId:'active',entries:[
  {id:'active',name:'Carreira ativa',owner:'owner',archived:false,updatedAt:3},
  {id:'archive',name:'Carreira <img src=x onerror=alert(1)>',owner:'owner',archived:true,updatedAt:2},
  {id:'keep',name:'Outra carreira',owner:'owner',archived:true,updatedAt:1}]};
 const manifest=key=>({format:FORMAT,collections:{players:{keys:[key]}}});
 storage=new Map([[INDEX,JSON.parse(JSON.stringify(slots))],[BASE,manifest('active-chunk')],
  [BASE+':meta',{year:2026}],[BASE+':previous',manifest('previous-chunk')],
  ['active-chunk',{content:'active'}],['previous-chunk',{content:'previous'}],
  [ARCHIVE+'archive',manifest('archive-chunk')],['archive-chunk',{content:'archive'}],
  [ARCHIVE+'keep',manifest('keep-chunk')],['keep-chunk',{content:'keep'}],['unrelated',{keep:true}]]);
 listDialog();flushTimers();
}
function image(){return JSON.stringify({slots,saved,v260SavedMeta,disk:[...storage]});}
function event(type,target,key='',shiftKey=false){return{type,target,key,shiftKey,prevented:false,stopped:false,
 preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;},stopPropagation(){this.stopped=true;}};}
function dispatch(e){for(const [where,capture]of [['window',true],['document',true],['document',false],['window',false]]){
 for(const listener of listeners[where][e.type]||[]){if(listener.capture!==capture)continue;listener.cb(e);if(e.stopped)return e;}}
 return e;}
function click(action,id){const target=buttons.find(b=>b.dataset.action===action&&(!id||b.dataset.saveId===id));
 assert(target,'Missing button '+action);dispatch(event('click',target));return target;}
let baseCalls=0;let act=()=>{baseCalls++;};
const v125ReadGuard=()=>true,v125RouteStats={close:0};
let v152SuppressAction='',v152SuppressUntil=0;
async function settle(){for(let i=0;i<20;i++)await Promise.resolve();flushTimers();}
'''


CASES = r'''
(async()=>{
 seed();const before=image();const baseBefore=baseCalls;
 click('futbr125-delete','archive');flushTimers();
 assert.equal(image(),before,'Opening confirmation mutated storage or index');
 assert.equal(modalKind,v18372DeleteKind);assert.equal(document.activeElement.dataset.action,'futbr18372-delete-cancel');
 assert.equal(panel.attributes['aria-describedby'],'futbr18372-delete-description');
 assert(modalCalls.at(-1).html.includes('Carreira &lt;img'));
 assert(!modalCalls.at(-1).html.includes('<img src=x'));
 assert.equal(baseCalls,baseBefore,'Original router must consume delete exactly once');
 const firstToken=v18372DeleteRequest.token,dialogs=modalCalls.length;
 deleteSlot('archive');deleteSlot('keep');
 assert.equal(modalCalls.length,dialogs,'Repeated request replaced current confirmation');
 click('futbr18372-delete-cancel');flushTimers();
 assert.equal(image(),before);assert.equal(writes,0);assert.equal(deletions.length,0);
 assert.equal(document.activeElement.dataset.saveId,'archive');assert.equal(document.activeElement.dataset.action,'futbr125-delete');
 assert.equal(notices.length,0,'Cancel showed a deletion success toast');

 click('futbr125-delete','archive');flushTimers();
 const escape=dispatch(event('keydown',document.activeElement,'Escape'));flushTimers();
 assert(escape.prevented&&escape.stopped);assert.equal(modalKind,'futbr125-list');assert.equal(image(),before);
 click('futbr125-delete','archive');click('close');flushTimers();
 assert.equal(modalKind,'futbr125-list');assert.equal(image(),before);

 click('futbr125-delete','archive');flushTimers();
 assert.notEqual(v18372DeleteRequest.token,firstToken);
 assert.equal(await v18372ConfirmDelete('archive',firstToken),false);
 assert.equal(await v18372ConfirmDelete('keep',v18372DeleteRequest.token),false);
 assert.equal(image(),before,'An obsolete token or other career changed storage');
 const replacedToken=v18372DeleteRequest.token;
 modal('<button data-action="close">Fechar</button>','unrelated-dialog');
 assert.equal(await v18372ConfirmDelete('archive',replacedToken),false);
 assert.equal(deleteSlot('archive'),true);flushTimers();
 assert.notEqual(v18372DeleteRequest.token,replacedToken);
 assert.equal(await v18372ConfirmDelete('archive',replacedToken),false);
 assert.equal(image(),before,'A replaced dialog retained an actionable old token');
 const last=buttons.at(-1);last.focus();dispatch(event('keydown',last,'Tab'));
 assert.equal(document.activeElement,buttons[0]);
 dispatch(event('keydown',buttons[0],'Tab',true));assert.equal(document.activeElement,last);
 click('futbr18372-delete-cancel');flushTimers();
 busy=true;assert.equal(deleteSlot('archive'),false);busy=false;
 account='other';assert.equal(deleteSlot('archive'),false);account='owner';
 click('futbr125-delete','archive');account='changed';
 assert.equal(await v18372ConfirmDelete('archive',v18372DeleteRequest.token),false);
 account='owner';assert.equal(image(),before);assert.equal(writes,0);

 seed();const initialKeep=JSON.stringify([...storage].filter(([k])=>k!==INDEX&&k!==ARCHIVE+'archive'&&k!=='archive-chunk'));
 click('futbr125-delete','archive');flushTimers();
 let release;gate=new Promise(resolve=>{release=resolve;});
 const confirmButton=click('futbr18372-delete-confirm');
 assert(busy);assert.equal(v18372DeleteRequest.phase,'deleting');assert(buttons.every(b=>b.disabled));
 const lockToken=v18372DeleteRequest.token;
 act(confirmButton);dispatch(event('click',confirmButton));
 assert.equal(await v18372ConfirmDelete('archive',lockToken),false);
 assert.equal(v18372CancelDelete(),false);closeModal();
 dispatch(event('keydown',confirmButton,'Escape'));assert(busy);
 release();gate=null;await settle();
 assert(!busy&&!v18372DeleteRequest);assert.equal(writes,1);assert.equal(flushes,0);
 assert.deepEqual(deletions,[ARCHIVE+'archive','archive-chunk']);
 assert.equal(JSON.stringify([...storage].filter(([k])=>k!==INDEX)),initialKeep);
 assert.deepEqual(slots.entries.map(s=>s.id),['active','keep']);assert.equal(slots.activeId,'active');
 assert.equal(notices.filter(n=>n.text==='Save excluído.').length,1);
 assert.equal(document.activeElement.dataset.action,'futbr125-load');

 const keepBefore=JSON.stringify([storage.get(ARCHIVE+'keep'),storage.get('keep-chunk'),storage.get('unrelated')]);
 click('futbr125-delete','active');flushTimers();click('futbr18372-delete-confirm');await settle();
 assert.equal(writes,2);assert.equal(flushes,1);assert.equal(slots.activeId,null);assert.equal(saved,null);assert.equal(v260SavedMeta,null);
 for(const key of [BASE,BASE+':meta',BASE+':previous','active-chunk','previous-chunk'])assert(!storage.has(key));
 assert.equal(JSON.stringify([storage.get(ARCHIVE+'keep'),storage.get('keep-chunk'),storage.get('unrelated')]),keepBefore);
 assert.deepEqual(slots.entries.map(s=>s.id),['keep']);
 click('futbr125-delete','keep');flushTimers();click('futbr18372-delete-confirm');await settle();
 assert.equal(slots.entries.length,0);assert.equal(document.activeElement.dataset.action,'close');
 assert.deepEqual(storage.get('unrelated'),{keep:true});

 seed();click('futbr125-delete','archive');flushTimers();failDelete=true;
 click('futbr18372-delete-confirm');await settle();
 assert(!busy&&!v18372DeleteRequest);assert.equal(modalKind,'futbr125-list');
 assert(storage.has(ARCHIVE+'archive'));assert.equal(notices.filter(n=>n.type==='success').length,0);
 assert(notices.some(n=>n.type==='error'));
 console.log(JSON.stringify({ok:true,version:'18.372',inGameDeleteConfirmation:true,noNativeConfirm:true,
  cancelPreservesStorage:true,escapePreservesStorage:true,closePreservesStorage:true,
  explicitConfirmDeletesOnlySelected:true,activeDeletionPreservesOtherCareers:true,
  singleCommitOnDoubleClick:true,staleConfirmationRejected:true,focusManaged:true,
  accountChangeRevalidated:true,storageErrorDoesNotClaimSuccess:true,originalRouterUsed:true,
  escapedCareerName:true,isolatedFixturesOnly:true,testHookNotShipped:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
'''


def main():
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != '--baseline'):
        raise SystemExit('usage: test_native_confirmations_18372.py <project> [--baseline]')
    root = Path(sys.argv[1])
    source = (root / 'src' / 'index.html').read_text(encoding='utf-8')
    router = extract(source[source.index('// 18.146: named careers now execute'):],
                     'const baseAct=act;', "document.addEventListener('click',ev=>")
    assert router.count("action==='futbr125-delete'") == 1
    primary = extract(source, "document.addEventListener('click',event=>{\n const el=event.target.closest?.('[data-action]');",
                      "document.addEventListener('change',event=>{const el=event.target;try{")
    direct = extract(source, 'function v125DirectAction(el){', '/* A ficha do clube ja recebe')
    if len(sys.argv) == 3:
        baseline = extract(source, 'async function deleteSlot(id){',
                           '// Ensure a newly created career gets its OWN identity')
        fixture = FIXTURE.replace("const confirm=()=>{throw Error('Native confirm must never be called');};",
                                  'let nativeCalls=0;const confirm=()=>{nativeCalls++;return false;};')
        cases = r'''
(async()=>{seed();const before=image();click('futbr125-delete','archive');await settle();
 assert.equal(nativeCalls,1);assert.equal(image(),before);assert.equal(writes,0);assert.equal(deletions.length,0);
 assert.equal(notices.length,0);console.log(JSON.stringify({ok:true,baselineNativePromptReproduced:true,
 nativeCalls,cancelPreservesStorage:true,singleOriginalRouterDispatch:true,noDeletionToastOnCancel:true,
 isolatedFixturesOnly:true}));})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        result = subprocess.run(['node', '-e', fixture + direct + primary + baseline + router + cases],
                                check=True, capture_output=True, text=True, encoding='utf-8')
        report = json.loads(result.stdout.strip().splitlines()[-1])
        (root / 'native-confirmations-18371-baseline.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False))
        return
    block = extract(source, '/* FUTBR_NATIVE_CONFIRMATIONS_18372_BEGIN',
                    '/* FUTBR_NATIVE_CONFIRMATIONS_18372_END */')
    assert 'confirm(' not in block, 'Deletion still calls the native confirmation'
    assert 'TEST_ONLY_NATIVE_CONFIRMATIONS_18372' not in source, 'Fixture was shipped'
    named = extract(source, 'function listDialog(){', '// Ensure a newly created career gets its OWN identity')
    assert 'confirm(' not in named, 'Another native confirmation remains in named-save dialogs'
    legacy_escape = "document.addEventListener('keydown',event=>{if(modalKind&&event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();}},true);"
    result = subprocess.run(['node', '-e', FIXTURE + direct + primary + legacy_escape + block + router + CASES],
                            check=True, capture_output=True, text=True, encoding='utf-8')
    report = json.loads(result.stdout.strip().splitlines()[-1])
    (root / 'native-confirmations-18372-tests.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
