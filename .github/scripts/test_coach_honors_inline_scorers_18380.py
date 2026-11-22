"""Test production 18.380 coach grouping and scorer row computed layout in Chromium."""
from pathlib import Path
import json
import hashlib
import re
import subprocess
import sys
from playwright.sync_api import sync_playwright

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_coach_honors_inline_scorers_18380.py <prepared-root>')
 root=Path(sys.argv[1]).resolve()
 s=(root/'src/index.html').read_text(encoding='utf-8')
 start=s.index('/* FUTBR_COACH_HONORS_INLINE_SCORERS_18380')
 end=s.index('window.GestorFC.render=render;',start)
 script=s[start:end]
 m=re.search(r'<style id="futbr-coach-honors-scorer-inline-18380">([\s\S]*?)</style>',s)
 if not m:raise RuntimeError('Real production CSS missing from 18.380 HTML')
 css=m.group(1)
 fixture=r"""
const assert=require('node:assert/strict');
global.window=global;window.GestorFC={};
const state={year:2038,teams:[
  {id:'fla',name:'Flamengo',short:'FLA',color:'#e22'},
  {id:'flu',name:'Fluminense',short:'FLU',color:'#173'}
]};
const E={team:(s,id)=>s.teams.find(t=>t.id===id)||null};
function esc(v){return String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');}
function badge(team){return '<span class="club-crest" data-crest="'+esc(team.id)+'"></span>';}
function v18379ClubNameKey(v){return String(v||'').trim().toLowerCase();}
function v126CoachTitles(c){return c.titles;}
function v126CoachHonors(c){return c.titles?.length?'OLD_UNGROUPED':'EMPTY_TITLES';}
"""
 checks=r"""
const trophies=[
 {key:'cup:bra',label:'Copa do Brasil',club:'fla',year:2037,points:100},
 {key:'cup:bra',label:'Copa do Brasil',club:'fla',year:2036,points:100},
 {key:'cup:bra',label:'Copa do Brasil',club:'fla',year:2035,points:100},
 {key:'cup:bra',label:'Copa do Brasil',club:'fla',year:2034,points:100},
 {key:'cup:bra',label:'Copa do Brasil',club:'fla',year:2035,points:100}, // duplicate event in old archive
 {key:'cup:bra',label:'Copa do Brasil',club:'flu',year:2036,points:100},
 {key:'supercup:bra',label:'Supercopa Rei',club:'fla',year:2037,points:150},
 {key:'continental:lib',label:'CONMEBOL Libertadores',club:'fla',year:2030,points:150},
 {key:'national:world',label:'Copa do Mundo',clubName:'Brasil',year:2035,points:220}
];
const coach={id:'leonardo',name:'Leonardo Jardim',titles:trophies};
const original=JSON.stringify(coach),world=JSON.stringify(state);
const groups=v18380CoachHonorGroups(coach);
assert.equal(groups.length,5,'Four Copa do Brasil from one club should form one card');
const repeated=groups.find(x=>x.label==='Copa do Brasil'&&x.clubId==='fla');
assert.deepEqual(repeated.years.map(y=>y.label),['2037','2036','2035','2034']);
assert.equal(repeated.count,4,'Duplicated historical event must not inflate title counts');
assert.equal(repeated.points,400,'Total bonus points from four real titles');
const other=groups.find(x=>x.label==='Copa do Brasil'&&x.clubId==='flu');
assert(other&&other.count===1,'Same trophy at another club needs its own group');
assert(groups.some(x=>x.national&&x.clubName==='Brasil'),'National title kept');
const out=v126CoachHonors(coach);
assert.equal((out.match(/data-v18380-group="1"/g)||[]).length,5,'One card per group');
assert(out.includes('4 títulos')&&out.includes('400 pontos de bônus no total'));
assert(out.includes('2034')&&out.includes('2037'),'All seasons displayed');
assert(out.includes('data-crest="fla"')&&out.includes('data-crest="flu"'));
assert.equal(JSON.stringify(coach),original,'Coach history must not be altered');
assert.equal(JSON.stringify(state),world,'Game world must not be altered');
assert.equal(v126CoachHonors({titles:[]}), 'EMPTY_TITLES', 'Original empty state preserved');
console.log(JSON.stringify({ok:true,version:'18.380.0',originalCoachRendererWrapped:true,
 duplicatedTitlesDeduplicatedInViewOnly:true,fourCupTitlesOneCard:true,
 differentClubsSeparate:true,nationalTrophiesPreserved:true,
 yearsSortedAndVisible:true,bonusPointsSummed:true,
 noCareerMutation:true,groupedCards:groups.length}));
"""
 runner=root/'coach-honors-18380-fixture.cjs'
 runner.write_text(fixture+'\n'+script+'\n'+checks,encoding='utf-8')
 result=subprocess.run(['node',str(runner)],capture_output=True,text=True,timeout=45)
 try:runner.unlink()
 except OSError:pass
 if result.returncode:raise RuntimeError('Real coach production JS: '+result.stderr[-3900:])
 report=json.loads(result.stdout.strip().splitlines()[-1])
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1520,'height':820})
  page.set_content('''<!doctype html><html><head><style>
   .v538-scorer-club,.v18379-club-entry {display:flex;flex-direction:column}
   .shield {display:block;width:30px;height:30px;background:grey}
   .club-history {width:450px}
   </style><style>'''+css+'''</style></head><body>
   <div class="v615-ranking-scroll"><table><tbody><tr>
    <td class="club-history"><div class="v538-scorer-club v18379-club-links">
      <span class="v18379-club-entry"><span id="badge" class="shield club-crest"></span>
        <button id="club" class="table-button" data-action="team" data-team="long">Hokkaido Consadole Sapporo</button>
      </span></div></td></tr></tbody></table></div>
   <div id="modal-root"><div class="v126-honors v18380-grouped-honors">
    <article class="v126-honor v18380-honor-group"><h4>Copa do Brasil</h4></article>
    <article class="v126-honor v18380-honor-group"><h4>Libertadores</h4></article>
    <article class="v126-honor v18380-honor-group"><h4>Supercopa Rei</h4></article>
   </div></div></body></html>''')
  style=page.locator('.v18379-club-entry').evaluate('(el)=>getComputedStyle(el).flexDirection')
  assert style=='row',f'Existing column CSS still won: {style}'
  badge=page.locator('#badge').bounding_box()
  button=page.locator('#club').bounding_box()
  assert badge and button and 0<=button['x']-(badge['x']+badge['width'])<20,(badge,button)
  assert abs((badge['y']+badge['height']/2)-(button['y']+button['height']/2))<12,(badge,button)
  columns=page.locator('.v18380-grouped-honors').evaluate('(el)=>getComputedStyle(el).gridTemplateColumns')
  assert len(columns.split())==3,columns
  page.set_viewport_size({'width':920,'height':820})
  columns2=page.locator('.v18380-grouped-honors').evaluate('(el)=>getComputedStyle(el).gridTemplateColumns')
  assert len(columns2.split())==2,columns2
  page.set_viewport_size({'width':590,'height':820})
  columns3=page.locator('.v18380-grouped-honors').evaluate('(el)=>getComputedStyle(el).gridTemplateColumns')
  assert len(columns3.split())==1,columns3
  report.update({'realCssComputedInChromium':True,'clubNameBesideCrest':True,
                 'existingTableActionPreserved':True,'responsiveColumns':'3/2/1'})
  browser.close()
 report['sourceSha256']=hashlib.sha256(s.encode()).hexdigest()
 (root/'coach-honors-inline-18380-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
