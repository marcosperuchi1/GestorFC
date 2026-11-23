"""Inspect FutBR login critical path from final compiled JavaScript, without secrets."""
from pathlib import Path
import re,sys
src=(Path(sys.argv[1])/'src/index.html').read_text(encoding='utf-8')
def clean(s):
 s=re.sub(r'(?i)(sb_secret_|service_role)[a-zA-Z0-9_.-]+',r'[REDACTED]',s)
 s=re.sub(r'(?i)(apikey|Authorization|password|token|secret)\s*[:=]\s*["\x27][A-Za-z0-9\-_.]{16,}["\x27]',r'\1: "[REDACTED]"',s)
 s=re.sub(r'https://[a-z0-9]{15,}\.supabase\.co',r'https://[PROJECT].supabase.co',s)
 return s
print('FILE LENGTH',len(src))
for pattern in [
 r'function\s+(v548[A-Za-z0-9_]+)\s*\(',r'function\s+(v580[A-Za-z0-9_]+)\s*\(',
 r'function\s+(v691[A-Za-z0-9_]+)\s*\(',r'function\s+(v310[A-Za-z0-9_]+)\s*\(',
 r'function\s+([\w$]*(?:Auth|Login|Session|License|Premium|EnterGame|Boot|RosterLoad|Splash)[\w$]*)\s*\(',
]:
 matches=list(re.finditer(pattern,src,re.I))
 print('NAMES',pattern,sorted(set(x.group(1) for x in matches))[:135])
targets=['v548Boot','v548EnterGame','v548RenderAuth','v548SetSession',
         'v548Login','v548SignIn','v548Auth','v548Submit','v548Restore',
         'v548ValidateSession','v548RefreshAccess','v548Fetch',
         'v691RefreshMeta','v310StartRosterLoad','v260FastLoadLocal']
for name in targets:
 matches=list(re.finditer(r'(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',src))
 print('\n==== FUNC',name,'COUNT',len(matches))
 for m in matches[-1:]:
  a=m.start();print('POS',a,'CODE',repr(clean(src[a:a+(6600 if name in ['v548Boot','v548EnterGame'] else 4500)])))
for term in [
 "document.addEventListener('submit',async e=>",
 'signInWithPassword','getSession()','getUser()','onAuthStateChange',
 'validate-license','v548EnterGame(', 'v548Boot()', 'rosterLoad',
 'fetchWithTimeout','setTimeout(resolve','v310StartRosterLoad(',
 'authorizations','device-session','v548Session=', 'v548RenderAuth(',
]:
 hits=list(re.finditer(re.escape(term),src))
 print('\n==== CALL',term,'COUNT',len(hits))
 for m in hits[-5:]:
  a=m.start()
  print('POS',a,'CODE',repr(clean(src[max(0,a-700):a+1800])))
