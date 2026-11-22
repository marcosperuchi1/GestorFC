"""Regression: one championship selector option per name, all historical years preserved."""
from pathlib import Path
import hashlib,json,subprocess,sys
from playwright.sync_api import sync_playwright

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_national_history_competition_filter_18381.py <game-root>')
 root=Path(sys.argv[1]).resolve()
 source=(root/'src/index.html').read_text(encoding='utf-8')
 a=source.index('/* FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381 */')
 b=source.index('function v18322NationalScorers(',a)
 code=source[a:b]
 if code.count('function v18381CompetitionOptions(')!=1:raise RuntimeError('Unique grouping implementation not present')
 runner=r"""
const assert=require('node:assert/strict');
function v18322N(x){return Number(x)||0;}
function v18322Esc(x){return String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');}
function v18322Option(value,label,current){
 return '<option value="'+v18322Esc(value)+'"'+(String(value)===String(current)?' selected':'')+'>'+v18322Esc(label)+'</option>';
}
function v640Flag(x){return '['+x+']';}
function v18322ScorerCell(){return 'goals';}
function v18322NationalScorers(){return [];}
let lastRows=[];
function v18322Table(rows){lastRows=rows;return '<div id="edition-count" data-count="'+rows.length+'">Exibindo '+rows.length+' edições</div>';}
const v18322NationalFilters={conf:'all',nation:'all',competition:'all'};
const history=[
 {id:'caf-2037',name:'Copa Africana de Nações',year:2037,champion:'cod',runnerUp:'nig'},
 {id:'caf-2035',name:'Copa Africana de Nacoes',year:2035,champion:'nig',runnerUp:'cod'},
 {id:'caf-2033',name:' Copa Africana  de Nações ',year:2033,champion:'cod',runnerUp:'nig'},
 {id:'asia-2036',name:'Copa da Ásia',year:2036,champion:'jpn',runnerUp:'kor'},
 {id:'asia-2035',name:'Copa da Asia',year:2035,champion:'kor',runnerUp:'jpn'},
 {id:'world-2038',name:'Copa do Mundo FIFA',year:2038,champion:'jpn',runnerUp:'cod'},
 {id:'world-2034',name:'Copa do Mundo FIFA',year:2034,champion:'nig',runnerUp:'kor'},
 {id:'concacaf-2037',name:'Copa Ouro da Concacaf',year:2037,champion:'usa',runnerUp:'jpn'}
];
const state={v640National:{
 history,
 competitions:{
 'caf-2037':{name:'Copa Africana de Nações',conf:'CAF'},
 'caf-2035':{name:'Copa Africana de Nações',conf:'CAF'},
 'caf-2033':{name:'Copa Africana de Nações',conf:'CAF'},
 'asia-2036':{name:'Copa da Ásia',conf:'AFC'},
 'asia-2035':{name:'Copa da Ásia',conf:'AFC'},
 'world-2038':{name:'Copa do Mundo FIFA',conf:'FIFA'},
 'world-2034':{name:'Copa do Mundo FIFA',conf:'FIFA'},
 'concacaf-2037':{name:'Copa Ouro da Concacaf',conf:'CONCACAF'}
 },
 teams:{
 cod:{name:'RD Congo',conf:'CAF'},nig:{name:'Nigéria',conf:'CAF'},
 jpn:{name:'Japão',conf:'AFC'},kor:{name:'Coreia do Sul',conf:'AFC'},
 usa:{name:'Estados Unidos',conf:'CONCACAF'}
 }
}};
const unchanged=JSON.stringify(state);
const opts=v18381CompetitionOptions(state.v640National,history);
assert.equal(opts.length,4,'Different edition IDs must yield four distinct championship choices');
const first=v18322HistoryPage('national');
assert.equal(lastRows.length,8,'All editions shown when filter=all');
assert.equal((first.match(/Copa Africana de Nações<\/option>/g)||[]).length,1);
assert.equal((first.match(/Copa da Ásia<\/option>/g)||[]).length,1);
assert.equal((first.match(/Copa do Mundo FIFA<\/option>/g)||[]).length,1);
const chosen='title:copa africana de nacoes';
v18322NationalFilters.competition=chosen;
const african=v18322HistoryPage('national');
assert.equal(lastRows.length,3,'Choosing grouped competition must show every year');
assert.deepEqual(lastRows.map(r=>r.year),[2037,2035,2033]);
assert(african.includes('value="'+chosen+'" selected'));
v18322NationalFilters.competition='caf-2035'; // older in-memory saved dropdown selection
v18322HistoryPage('national');
assert.equal(lastRows.length,3,'Legacy per-edition selection must match all editions');
v18322NationalFilters.competition='title:copa da asia';
v18322HistoryPage('national');
assert.equal(lastRows.length,2,'Unicode accents must not split one tournament');
v18322NationalFilters.competition='title:copa do mundo fifa';
v18322HistoryPage('national');
assert.equal(lastRows.length,2,'Repeated World Cup editions grouped');
v18322NationalFilters.conf='CAF';
v18322NationalFilters.competition='all';
v18322HistoryPage('national');
assert.equal(lastRows.length,3,'Confederation filter still works');
v18322NationalFilters.conf='all';
v18322NationalFilters.nation='jpn';
v18322HistoryPage('national');
assert.equal(lastRows.length,4,'National team filter still works');
assert.equal(JSON.stringify(state),unchanged,'No competition history records mutated');
console.log(JSON.stringify({ok:true,version:'18.381.0',uniqueOptionsPerDisplayName:true,
 normalizedAccentAndWhitespace:true,multipleEditionIdsSameOption:true,
 selectsEveryYearOfTournament:true,formerSelectedIdCompatible:true,
 confederationAndNationFiltersPreserved:true,gameStateUntouched:true,
 allEightHistoryRowsPreserved:true,initialHTML:first}));
"""
 temp=root/'national-filter-18381-fixture.cjs'
 temp.write_text(runner[:runner.index('const unchanged=')]+code+'\n'+runner[runner.index('const unchanged='):],encoding='utf-8')
 out=subprocess.run(['node',str(temp)],text=True,capture_output=True,timeout=60)
 try:temp.unlink()
 except OSError:pass
 if out.returncode:raise RuntimeError('18.381 production national filter test: '+out.stderr[-3500:])
 report=json.loads(out.stdout.strip().splitlines()[-1])
 html=report.pop('initialHTML')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=browser.new_page()
  page.set_content('<!doctype html><html><body>'+html+'</body></html>')
  choices=page.locator('select[data-v18322="n-competition"] option')
  labels=choices.all_text_contents()
  assert len(labels)==5 and len(set(labels))==5,labels
  assert labels[0]=='Todos',labels
  assert set(labels[1:])=={'Copa Africana de Nações','Copa da Ásia','Copa do Mundo FIFA','Copa Ouro da Concacaf'},labels
  assert page.locator('select[data-v18322="n-conf"]').count()==1
  assert page.locator('select[data-v18322="n-nation"]').count()==1
  page.locator('select[data-v18322="n-competition"]').select_option('title:copa africana de nacoes')
  assert page.locator('select[data-v18322="n-competition"]').input_value()=='title:copa africana de nacoes'
  report['actualBrowserOneOptionPerCompetition']=True
  report['nativeSelectValueFunctional']=True
  browser.close()
 report['sourceSha256']=hashlib.sha256(source.encode('utf-8')).hexdigest()
 (root/'national-history-filter-18381-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
