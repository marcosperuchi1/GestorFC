"""Inspect real FutBR post-auth startup and welcome dependency without credentials."""
from pathlib import Path
import sys,re
s=(Path(sys.argv[1])/'src/index.html').read_text(encoding='utf-8')
def display(name,part,n=5000):
 print('###',name,'length',len(part))
 print(part[:n].replace('access_token','[ACCESS_TOKEN_FIELD]').replace('refresh_token','[REFRESH_TOKEN_FIELD]'))
def fn(name):
 hits=list(re.finditer(r'(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',s))
 if not hits:
  display('MISSING '+name,'');return
 m=hits[-1];a=s.find('{',m.end());depth=0;string=None;escape=False;open_end=None
 for i in range(a,len(s)):
  ch=s[i]
  if string:
   if escape:escape=False
   elif ch=='\\':escape=True
   elif ch==string:string=None
   continue
  if ch in ("'",'"',chr(96)):string=ch;continue
  if ch=='{':depth+=1
  elif ch=='}':
   depth-=1
   if depth==0:open_end=i+1;break
 display('FUNCTION '+name,s[m.start():(open_end or a+7000)],8000)
for name in ['v548EnterGame','v548Boot','v310StartRosterLoad',
 'v310AcceptRosterText','v260FastLoadLocal','v18196PaintWelcomeGate',
 'renderWelcome','v260InsertLazyResume','v548AuthHTML',
 'v18385LocalOnce','v18373PrepareVacationBoot',
 'v18196BaseWelcome','v310DecodeCompactRoster']:
 fn(name)
for needle in [
 'const v18196BaseWelcome=renderWelcome;', 'if(typeof v310RosterText',
 'renderWelcome=function','function renderWelcome','function v310AcceptRosterText',
 'async function v310AcceptRosterText','function v548RenderAuth',
 'v18385RosterPending=v310StartRosterLoad()',
 'v310RosterLoadPromise=','await v310StartRosterLoad();',
 'v310StartRosterLoad().catch',
 'window.FutBRDesktop.loadPlayerBase','window.FutBRDesktop?.loadPlayerBase',
 'rosterPreloadedDuringAuth:false',
 'data-action="new-career"','data-action="v260-continue"',
 ]:
 hits=list(re.finditer(re.escape(needle),s))
 print('### NEEDLE',repr(needle),'count',len(hits))
 for m in hits[-4:]:display('OFFSET '+str(m.start()),s[max(0,m.start()-500):m.start()+1600],2100)
