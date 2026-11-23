"""Test actual 18.384 grouped player honors JS and responsive CSS in Chromium."""
from pathlib import Path
import json,hashlib,subprocess,re,sys
from playwright.sync_api import sync_playwright

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_player_honors_18384.py <prepared-root>')
 root=Path(sys.argv[1]);src=(root/'src/index.html').read_text(encoding='utf-8')
 a=src.index('/* FUTBR_PLAYER_TROPHIES_GROUPED_18384')
 b=src.index('window.GestorFC.render=render;',a)
 code=src[a:b]
 m=re.search(r'<style id="futbr-player-honors-grouped-18384">([\s\S]*?)</style>',src)
 if not m:raise RuntimeError('Missing player grouped honors stylesheet')
 css=m.group(1)
 fixture=r"""
const assert=require('node:assert/strict');
global.window={GestorFC:{}};
const state={teams:[{id:'hof',name:'TSG Hoffenheim',country:'ger'},
 {id:'bay',name:'Bayern München',country:'ger'}]};
const E={team:(s,id)=>s.teams.find(x=>x.id===id)||null};
const esc=v=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
const badge=t=>'<span class="shield" data-club="'+esc(t.id)+'"></span>';
const countryName=c=>c==='ger'?'Alemanha':'';
const v123HonorsRows=id=>players[id]?.honors538||[];
const v123Honors=p=>'ORIGINAL_EMPTY';
const rows=[
 {kind:'club',key:'league:ger:1',name:'Alemanha · 1ª divisão',year:2036,teamId:'hof',teamName:'TSG Hoffenheim'},
 {kind:'club',key:'league:ger:1',name:'Alemanha · 1ª divisão',year:2033,teamId:'hof',teamName:'TSG Hoffenheim'},
 {kind:'club',key:'league:ger:1',name:'Alemanha · 1ª divisão',year:2033,teamId:'hof',teamName:'TSG Hoffenheim'},
 {kind:'scorer',key:'scorer:league:ger:1',name:'Artilheiro · Alemanha · 1ª divisão',year:2033,teamId:'hof',goals:24},
 {kind:'scorer',key:'scorer:league:ger:1',name:'Artilheiro · Alemanha · 1ª divisão',year:2026,teamId:'hof',goals:25},
 {kind:'scorer',key:'scorer:cup:ger',name:'Artilheiro · DFB-Pokal',year:2029,teamId:'hof',goals:6},
 {kind:'scorer',key:'scorer:cup:ger',name:'Artilheiro · DFB-Pokal',year:2028,teamId:'hof',goals:7},
 {kind:'club',key:'cup:ger',name:'DFB-Pokal',year:2029,teamId:'hof'},
 {kind:'club',key:'cup:ger',name:'DFB-Pokal',year:2028,teamId:'hof'},
 {kind:'club',key:'cup:ger',name:'DFB-Pokal',year:2026,teamId:'hof'},
 {kind:'club',key:'cup:ger',name:'DFB-Pokal',year:2034,teamId:'bay'}
];
const players={p:{id:'p',honors538:rows},empty:{id:'empty',honors538:[]}};
const saved=JSON.stringify(players);
"""
 checks=r"""
const grouped=v18384PlayerHonorGroups(rows);
assert.equal(grouped.length,5,'4 titles + separate scorer groups must create five groups');
const cup=grouped.find(x=>x.kind==='club'&&x.name==='DFB-Pokal'&&x.teamId==='hof');
assert.deepEqual(cup.years.map(x=>x.year),[2029,2028,2026]);
const scorerCup=grouped.find(x=>x.kind==='scorer'&&x.name==='Artilheiro · DFB-Pokal');
assert.equal(scorerCup.count,2);
assert.deepEqual(scorerCup.years.map(x=>x.goals),[6,7]);
assert.equal(scorerCup.goals,13);
const league=grouped.find(x=>x.kind==='club'&&x.name==='Alemanha · 1ª divisão');
assert.equal(league.count,2,'duplicate award row in same year deduplicated');
assert(grouped.some(x=>x.teamId==='bay'&&x.count===1),'Different clubs kept separate');
const html=v123Honors(players.p);
assert.equal((html.match(/data-v18384-group="1"/g)||[]).length,5);
assert(html.includes('3 títulos')&&html.includes('2 artilharias'));
assert(html.includes('2036')&&html.includes('2026')&&html.includes('7 gols'));
assert(html.includes('data-club="hof"')&&html.includes('data-club="bay"'));
assert.equal(v123Honors(players.empty),'ORIGINAL_EMPTY');
assert.equal(JSON.stringify(players),saved,'No career or source award mutated');
console.log(JSON.stringify({ok:true,version:'18.384.0',actualRendererWrapped:true,
 repeatedChampionshipsGrouped:true,scorerAwardsSeparate:true,scorerGoalsPerYear:true,
 distinctClubHonorsDistinct:true,duplicatesDedupeViewOnly:true,
 legacyEmptyStatePreserved:true,savedHonorsUnchanged:true,
 titleCards:grouped.length,html}));
"""
 f=root/'player-honors-18384-fixture.cjs'
 f.write_text(fixture+'\n'+code+'\n'+checks,encoding='utf-8')
 result=subprocess.run(['node',str(f)],text=True,capture_output=True,timeout=40)
 try:f.unlink()
 except OSError:pass
 if result.returncode:raise RuntimeError(result.stderr[-3500:])
 report=json.loads(result.stdout.strip().splitlines()[-1]);html=report.pop('html')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1580,'height':900})
  page.set_content('<html><head><style>'+css+'</style></head><body><div id="modal-root"><div class="v123-panel">'+html+'</div></div></body></html>')
  cols=page.locator('.v18384-player-honors').evaluate('(el)=>getComputedStyle(el).gridTemplateColumns')
  assert len(cols.split())==3,cols
  page.set_viewport_size({'width':850,'height':800})
  cols2=page.locator('.v18384-player-honors').evaluate('(el)=>getComputedStyle(el).gridTemplateColumns')
  assert len(cols2.split())==2,cols2
  page.set_viewport_size({'width':520,'height':850})
  cols3=page.locator('.v18384-player-honors').evaluate('(el)=>getComputedStyle(el).gridTemplateColumns')
  assert len(cols3.split())==1,cols3
  assert page.locator('.v123-honor').count()==5
  report.update({'actualBrowserResponsiveGrid':True,'gridColumns':'3/2/1',
  'originalHonorPaginationSelectorPreserved':True})
  browser.close()
 report['sourceSha256']=hashlib.sha256(src.encode()).hexdigest()
 (root/'player-honors-18384-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
