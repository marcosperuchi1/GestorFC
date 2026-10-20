from __future__ import annotations
import json,re,sys
from pathlib import Path

def die(msg): raise RuntimeError(msg)

def function_block(src,name):
    m=re.search(r'(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',src)
    if not m: die(name+' ausente')
    b=src.find('{',m.end());depth=0;quote=None;esc=False
    for i in range(b,len(src)):
        ch=src[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
            continue
        if ch in ("'",'"','`'): quote=ch; continue
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return src[m.start():i+1]
    die(name+' nao fechada')

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_login_boot.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src'/'index.html').read_text(encoding='utf-8')
    enter=function_block(html,'v548EnterGame')
    boot=function_block(html,'v548Boot')

    if 'await loadLocal()' in enter or 'await loadLocal(false)' in enter:
        die('v548EnterGame ainda chama loadLocal pesado')
    if 'await v260FastLoadLocal(false)' not in enter:
        die('v548EnterGame nao usa carregamento rapido de metadados')
    if 'await v310StartRosterLoad();' not in enter:
        die('v548EnterGame pode renderizar antes da base instalada')
    if enter.find('await v310StartRosterLoad();') > enter.find('renderWelcome();'):
        die('renderWelcome ocorre antes da base instalada')

    if 'Promise.resolve().then(()=>loadLocal(false))' in boot:
        die('boot ainda usa loadLocal pesado')
    if 'Promise.resolve().then(()=>v260FastLoadLocal(false))' not in boot:
        die('boot nao usa carregamento rapido')
    if 'const rosterPreload=Promise.resolve().then(()=>v310StartRosterLoad())' not in boot:
        die('boot nao inicia a base consolidada em paralelo')
    if 'await Promise.all([localPreload,rosterPreload]);' not in boot:
        die('sessao restaurada pode renderizar antes da base consolidada')

    submit_marker="document.addEventListener('submit',async e=>"
    si=html.find(submit_marker)
    if si<0: die('submit de login ausente')
    se=html.find("document.addEventListener('click'",si)
    block=html[si:se if se>si else si+5000]
    if 'v310StartRosterLoad' in block or 'v310EnsureRosterTextSync' in block or 'v310RosterSlice' in block:
        die('submit de login toca diretamente na base inicial e pode bloquear a UI')

    if 'const v18196BaseWelcome=renderWelcome;' not in html:
        die('gate final de renderWelcome ausente')
    if "if(typeof v310RosterText==='string'&&v310RosterText)return v18196BaseWelcome" not in html:
        die('renderWelcome nao verifica se a base esta pronta')
    if 'base local para nova carreira' in html or 'base local no login:' in html or 'base local durante load:' in html:
        die('fluxo antigo de base adiada ainda permanece')
    if 'welcomeRosterGate:true' not in html or 'rosterPreloadedDuringAuth:true' not in html:
        die('marcadores do boot consolidado ausentes')

    result={
      'ok':True,
      'loginUiImmediate':True,
      'loginSubmitRosterIndependent':True,
      'authenticatedEntryAwaitsRoster':True,
      'restoredSessionAwaitsRoster':True,
      'welcomeRosterGate':True,
      'rosterPreloadedDuringAuth':True
    }
    (root/'login-boot-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
