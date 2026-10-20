from __future__ import annotations
import json, re, sys
from pathlib import Path


def die(msg):
    raise RuntimeError(msg)


def function_block(src, name):
    m = re.search(r'(?:async\s+)?function\s+' + re.escape(name) + r'\s*\(', src)
    if not m:
        die(name + ' ausente')
    b = src.find('{', m.end())
    depth = 0
    quote = None
    esc = False
    for i in range(b, len(src)):
        ch = src[i]
        if quote:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"', chr(96)):
            quote = ch
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return src[m.start():i + 1]
    die(name + ' nao fechada')


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_login_boot.py <project-dir>')
    root = Path(sys.argv[1]).resolve()
    html = (root / 'src' / 'index.html').read_text(encoding='utf-8')
    enter = function_block(html, 'v548EnterGame')
    boot = function_block(html, 'v548Boot')
    meta = function_block(html, 'v691RefreshMeta')
    record = function_block(html, 'v310RosterRecord')

    # Entrada autenticada: so aqui a base de jogadores deve ser aguardada.
    if 'await loadLocal()' in enter or 'await loadLocal(false)' in enter:
        die('v548EnterGame ainda chama loadLocal pesado')
    if 'await v260FastLoadLocal(false)' not in enter:
        die('v548EnterGame nao usa carregamento rapido de metadados')
    if 'await v310StartRosterLoad();' not in enter:
        die('v548EnterGame nao aguarda a base depois da autenticacao')
    if enter.find('await v310StartRosterLoad();') > enter.find('renderWelcome();'):
        die('renderWelcome ocorre antes da base na entrada autenticada')

    # Boot real: formulario primeiro, roster somente se a sessao for valida.
    auth_call = "v548RenderAuth('login','');"
    if auth_call not in boot:
        die('boot nao monta o formulario de login imediatamente')
    if 'rosterPreload=' in boot:
        die('boot ainda inicia preload de roster durante autenticacao')
    roster_pos = boot.find('await v310StartRosterLoad();')
    auth_pos = boot.find(auth_call)
    authenticated_pos = boot.find('if(authenticated){')
    if roster_pos < 0:
        die('boot nao carrega roster para sessao restaurada valida')
    if not (auth_pos >= 0 and authenticated_pos >= 0 and auth_pos < authenticated_pos < roster_pos):
        die('boot pode tocar na base antes de montar login e validar sessao')
    if "await localPreload;\n v548RenderAuth" in boot:
        die('login ainda espera leitura local antes de aparecer')
    if 'Promise.resolve().then(()=>v310StartRosterLoad())' in boot:
        die('roster ainda e iniciado em paralelo com autenticacao')

    # Submit de login nao deve tocar diretamente no asset; v548EnterGame faz isso apos auth valida.
    submit_marker = "document.addEventListener('submit',async e=>"
    si = html.find(submit_marker)
    if si < 0:
        die('submit de login ausente')
    se = html.find("document.addEventListener('click'", si)
    block = html[si:se if se > si else si + 5000]
    if 'v310StartRosterLoad' in block or 'v310EnsureRosterTextSync' in block or 'v310RosterSlice' in block:
        die('submit de login toca diretamente na base inicial')

    # Leitura sincrona deve ser inofensiva enquanto o asset ainda nao foi carregado.
    if "if(!v310RosterText&&!V310_BOOTSTRAP_ROSTERS[id])return undefined;" not in record:
        die('v310RosterRecord ainda pode abortar o script antes do login')

    # Metadados do boot usam a contagem precomputada em vez de enumerar 5.628 rosters.
    if 'baseRosterStats310?.players' not in meta:
        die('v691RefreshMeta nao usa estatistica precomputada')
    if "else if(typeof v310RosterText==='string'&&v310RosterText)" not in meta:
        die('v691RefreshMeta pode enumerar rosters antes de a base estar pronta')

    # Correcoes antigas precisam estar apenas no asset consolidado, nao no boot.
    forbidden = [
        '(function v530PatchRosterFacts()',
        "const v183FluBase=v310RosterRecord('t6')",
        '(WorldCatalog.clubs||[]).slice(-256)',
    ]
    for marker in forbidden:
        if marker in html:
            die('rotina legacy ainda toca roster no boot: ' + marker)
    if re.search(r'^v526PrioritizeJoaquinRoster\(\);$', html, re.M):
        die('priorizacao Joaquin ainda roda no topo do script')

    # Gate da tela de nova carreira continua protegendo renderWelcome.
    if 'const v18196BaseWelcome=renderWelcome;' not in html:
        die('gate final de renderWelcome ausente')
    if "if(typeof v310RosterText==='string'&&v310RosterText)return v18196BaseWelcome" not in html:
        die('renderWelcome nao verifica se a base esta pronta')

    markers = [
        'rosterPreloadedDuringAuth:false',
        'loginUiIndependentFromRoster:true',
        'rosterLoadAfterAuthentication:true',
        'noRosterReadBeforeLogin:true',
        'welcomeRosterGate:true',
    ]
    for marker in markers:
        if marker not in html:
            die('marcador de boot ausente: ' + marker)

    result = {
        'ok': True,
        'loginUiImmediate': True,
        'loginSubmitRosterIndependent': True,
        'noRosterReadBeforeLogin': True,
        'rosterLoadAfterAuthentication': True,
        'authenticatedEntryAwaitsRoster': True,
        'restoredSessionAwaitsRoster': True,
        'precomputedRosterStatsBeforeLogin': True,
        'legacyBootRosterSweepsRemoved': True,
        'welcomeRosterGate': True,
    }
    (root / 'login-boot-tests.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
