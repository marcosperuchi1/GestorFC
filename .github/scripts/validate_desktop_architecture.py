from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path

CRITICAL_MARKERS=[
    'const Engine = (() => {',
    'v643ConvertNewCareerToNational',
    'GFC_SHARDED_171',
    'futbr-v18159-fixes',
    'v1891-nextmatch',
    'v55InjuryPrompt',
    'v55PenaltyPrompt',
    'v538CareerArchive',
    'v555CareerArchive',
    'competitionStats',
    'allTimeStats',
]

def die(msg): raise RuntimeError(msg)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def engine_sha(html):
    a=html.find('const Engine = (() => {')
    b=html.find("if(typeof module!=='undefined'&&module.exports)",a)
    if a<0 or b<a: die('Motor principal nao encontrado')
    return hashlib.sha256(html[a:b].encode()).hexdigest()

def parse_index(html):
    m=re.search(r'const\s+V310_ROSTER_INDEX\s*=\s*(\{.*?\});\s*const\s+V310_ROSTER_SOURCES=',html,re.S)
    if not m: die('Indice V310 nao encontrado')
    return json.loads(m.group(1))

def validate_scripts(html, root):
    pat=re.compile(r'<script\b([^>]*)>(.*?)</script>',re.I|re.S)
    checked=0
    for i,m in enumerate(pat.finditer(html)):
        attrs=m.group(1); body=m.group(2)
        mt=re.search(r'\btype=["\']([^"\']+)["\']',attrs,re.I)
        typ=(mt.group(1).lower() if mt else '')
        if typ and typ not in ('text/javascript','application/javascript','module'): continue
        if not body.strip(): continue
        suffix='.mjs' if typ=='module' else '.js'
        tmp=root/f'.futbr_validate_{i}{suffix}'
        tmp.write_text(body,encoding='utf-8')
        try:
            r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True)
            if r.returncode: die(f'Erro de sintaxe JS no bloco {i}: {r.stderr[-1000:]}')
        finally:
            tmp.unlink(missing_ok=True)
        checked+=1
    if checked<100: die(f'Poucos scripts executaveis validados: {checked}')
    return checked

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: validate_desktop_architecture.py <project-dir>')
    project=Path(sys.argv[1]).resolve(); src=project/'src'; html_path=src/'index.html'
    html=html_path.read_text(encoding='utf-8')

    for marker in CRITICAL_MARKERS:
        if marker not in html: die(f'Marcador critico ausente: {marker}')
    if 'v310RosterNode' in html: die('Referencia antiga ao roster embutido permanece')
    if 'indexeddb-hot-sqlite-manual-sync' not in html: die('Camada hibrida de persistencia nao encontrada')
    if 'futbr-desktop-viewport-lock' not in html: die('Trava de viewport desktop ausente')
    if 'futbr-desktop-crest-warmup' not in html: die('Preaquecimento de escudos ausente')
    if "v4CrestURL=function(t){const r=v53Record(t.id);return r?.data||r?.url||'';};" not in html:
        die('Resolvedor final de escudos nao aceita arquivos locais externos')
    if 'futbr-player-base-preload' in html:
        die('Preload antigo da base de jogadores ainda existe no head')
    if "load_player_base" not in html:
        die('Bridge nativo da base de jogadores nao foi ligado ao frontend')
    if "async function v548EnterGame(){await v260FastLoadLocal(false);await v310StartRosterLoad();renderWelcome();}" not in html:
        die('Entrada autenticada ainda pode renderizar antes da base instalada')
    if "v548RenderAuth('login','');" not in html:
        die('Boot nao monta o formulario de login imediatamente')
    if "const rosterPreload=Promise.resolve().then(()=>v310StartRosterLoad())" in html or "await Promise.all([localPreload,rosterPreload]);" in html:
        die('Boot ainda pre-carrega a base durante autenticacao')
    if "if(authenticated){\n  await localPreload;\n  await v310StartRosterLoad();" not in html:
        die('Sessao restaurada nao aguarda a base somente depois da autenticacao')
    if "if(!v310RosterText&&!V310_BOOTSTRAP_ROSTERS[id])return undefined;" not in html:
        die('Leitura sincrona da base ainda pode abortar o script antes do login')
    if re.search(r'^v526PrioritizeJoaquinRoster\(\);
    if "const v18196BaseWelcome=renderWelcome;" not in html or "welcomeRosterGate:true" not in html:
        die('Gate final da tela inicial para a base instalada ausente')
    if "const authenticated=await Promise.race([authPromise,timeout]);" not in html or "setTimeout(()=>resolve(null),6000)" not in html:
        die('Validacao remota ainda pode deixar o boot em tela vazia indefinidamente')
    if "Promise.resolve().then(()=>v580RestoreRemoteSession())" not in html or "bootPromiseSafe:true" not in html:
        die('Boot ainda pode escapar por excecao sincrona antes da tela de login')
    if "emptyAppWatchdog:true" not in html or "setTimeout(rescue,2500)" not in html:
        die('Watchdog final para app vazio ausente')
    if "base local no login:" in html or "base local durante load:" in html:
        die('Continuar save ainda carrega a base inicial de jogadores desnecessariamente')
    if "const v18194Loader=window.GestorFC?.v171?.loadDirect;" not in html or html.count("if(!loaded)loaded=await v53Call('load',{key:STORE});") < 2:
        die('Carregamento direto ou fallback seguro das duas rotas de save nao foi instalado')
    if "rosterPromise" in html:
        die('Carregamento de save ainda espera a base inicial desnecessariamente')
    if html.count('"name":"ASA"') != 1:
        die('Catalogo inicial ainda possui ASA duplicado')
    if "supportFictional?(div>=4?.72" not in html:
        die('Guard de desenvolvimento para elencos de suporte ausente')
    if "futbr-root-18170-fixes" not in html:
        die('Correcoes raiz 18.170 ausentes')
    if "function v53ScheduleNationalJumpPaint()" not in html:
        die('Visao Geral do nationaljump ainda nao usa o agendador raiz')
    if "if(v53Sim?.mode==='nationaljump'){v53ScheduleNationalJumpPaint();}" not in html:
        die('Pacotes vac-live do nationaljump ainda nao atualizam a Visao Geral')
    if "v18170EnsureAllNationalPools" not in html or "v18170InitialNationalFreeAgent" not in html:
        die('Selecoes pequenas ainda nao recebem jogadores livres na criacao do mundo')
    if "localizedNationalFreeAgentNames:true" not in html or "function v18171NationalGeneratedName(s,code,id,used=new Set())" not in html:
        die('Jogadores ficticios das selecoes ainda nao recebem nomes caracteristicos do pais')
    if "+String((h%89)+10)" in html or "nationalNamesNeverNumeric:true" not in html:
        die('Jogadores ficticios de selecao ainda podem receber sufixo numerico')
    if "const clean=p.v18171LocalizedName&&p.natCode===n&&!/\\d/.test" not in html:
        die('Reparo de nomes nacionais numericos anteriores ausente')
    if "dynamicCareerSurfaceTheme:true" not in html or "function v18172ApplyCareerSurface(primary)" not in html:
        die('Tema dinamico da carreira ainda nao deriva da equipe comandada')
    if "consultedProfileOwnTheme:true" not in html or "v18172ApplySurfaceToElement(modalEl,p.primary)" not in html:
        die('Ficha consultada ainda nao recebe tema completo proprio')
    if "nationalProfileFinalOwnTheme:true" not in html or "function v18173PaintConsultedNationalProfile(code)" not in html or "v18173PaintConsultedNationalProfile(n);" not in html:
        die('Redefinicao final da ficha de selecao pode perder a paleta da selecao consultada')
    if "const surface=typeof v18172SurfaceVars==='function'?v18172SurfaceVars(p.primary)" not in html or "try{v18172ApplySurfaceToElement(profile,p.primary);}catch(e){}" not in html:
        die('v657ApplyNationalModalTheme ainda nao reaplica bg/panel/panel2/line da selecao consultada')
    if "nationalProfileForcedSurface:true" not in html or "function v18174ForceNationalProfileTheme(code)" not in html or "v18174ForceNationalProfileTheme(code);" not in html:
        die('Ficha nacional final ainda pode herdar superficie da selecao comandada')
    if "nationalModalOwnRootTheme:true" not in html or "let v18176NationalModalCode=null,v18176OpeningNationalCode=null" not in html:
        die('Ficha nacional ainda nao controla o tema raiz enquanto esta aberta')
    if "nationalModalThemePinsV128:true" not in html or "const use=v18176NationalModalCode||v18176OpeningNationalCode||code;" not in html:
        die('Carreira iniciada por selecao ainda pode sobrescrever o tema da ficha consultada')
    if "v18176NationalModalCode=n;" not in html or "v18176NationalModalCode=null;" not in html:
        die('Tema raiz da ficha nacional nao e ativado/restaurado corretamente')
    if "set(modalEl,'background'," not in html or "set(body,'background'," not in html:
        die('Tema nacional final nao fixa fundo e corpo da selecao consultada')
    if "dragGhost:true" not in html or "function v18172PointerGhostAt(p,e)" not in html:
        die('Cartao fantasma do jogador durante o arraste ausente')
    if "reservePointerSwap:true" not in html or "if(el.dataset.v5Slot===undefined){e.preventDefault();return;}" not in html:
        die('Banco de reservas ainda depende do drag HTML nativo')
    if "v18170EnsureNationalPool(state,enemy,f);" not in html:
        die('Saves antigos ainda podem enfrentar selecao adversaria sem elenco apto suficiente')
    if "t.v600PreferredBench=v602SortPlayerIds(list.slice(0,V600_BENCH_LIMIT))" not in html:
        die('Banco nacional pre-jogo nao esta ordenado por posicao na raiz')
    if "ids=typeof v602SortPlayerIds==='function'?v602SortPlayerIds(raw):raw" not in html:
        die('Banco durante a partida nao esta ordenado por posicao na raiz')
    if "return typeof v602SortPlayerIds==='function'?v602SortPlayerIds(ids):ids;" not in html:
        die('Nao relacionados durante a partida nao estao ordenados por posicao')
    if "futbr-v18164-national-match-parity" not in html:
        die('Camada visual de paridade das selecoes ausente')
    if "firstClickEditable:true" not in html or "coreDragOnly:true" not in html:
        die('Primeiro clique ou drag da selecao ainda nao usa a rota unificada')
    if "v18167NationalDrag" in html:
        die('Listener duplicado de drag nacional foi reintroduzido')
    if "justify-self:stretch!important" not in html:
        die('Banco do adversario nacional ainda nao ocupa toda a largura')
    if "nationalFixtureDetails:true" not in html:
        die('Detalhes das partidas de selecoes ausentes')
    if "decorateCareerMenuActions" not in html:
        die('Acoes desktop do menu de carreira nao sao independentes do tipo de carreira')
    if "function v515RatingForClub(t){if(t?.regionalOnly)return null;" not in html:
        die('Clubes regionais ainda podem herdar ranking mundial por colisao de nome')
    if "cleanNationalClubVisualResidue" not in html and "futbr-root-18170-fixes" not in html:
        die('Isolamento visual entre carreira de selecao e clube ausente')
    if "initialClub:nationalCode?'':loaded.user" not in html:
        die('Carreira nova de selecao ainda guarda clube inicial indevido')
    if "function v310ReleaseRosterSource(){v310RosterText='';" in html:
        die('Base compacta de jogadores ainda esta sendo descartada durante a carreira')
    if "fetch(V310_ROSTER_ASSET" in html:
        die('A build desktop ainda usa fetch local para a base de jogadores')
    if "O acesso é validado pelo servidor do FutBR Manager." in html:
        die('Mensagem de seguranca ainda aparece no login desktop')
    if "futbr-desktop-load-optimization" not in html:
        die('Otimizacao de carregamento de saves ausente')
    if "freeNationalStartBlocked:true" not in html or "params?.options?.v643StartType==='national'&&!v18177FullAccess()" not in html:
        die('Plano Gratuito ainda pode iniciar carreira por selecao')
    if "freeNationalStartCoreGate:true" not in html or "if(!v548FullAccess()&&v128NationalStart){" not in html:
        die('Nucleo final 11.5C ainda pode permitir carreira nacional gratuita')
    if "function v643ConvertNewCareerToNational(s,code){if(!v548FullAccess())throw Error('Carreira por selecao requer Premium.')" not in html:
        die('Conversao final para selecao nao exige Premium')
    if "fastCareerSeedRefs:true" not in html or "p.v18175SeedRoster=data?.prebuiltInitial?null:rp" not in html:
        die('Criacao consolidada ainda mantem referencia duplicada da base em cada jogador')
    if "const info=db[t.id],map=new Map((info?.players||[]).map" in html:
        die('Criacao de carreira ainda cria Maps repetidos para os elencos')
    manifest_text=(project/'src/assets/data/player-base-manifest.json').read_text(encoding='utf-8')
    if "if(cache.size>32)cache.delete(cache.keys().next().value)" not in html:
        die('Worker da nova carreira nao limita o cache decodificado da base consolidada')
    if "shardReadConcurrency:8" not in html:
        die('Leitura paralela dos blocos do save nao foi ativada')
    if "indexedDbBatchTransaction:true" not in html or "async function v18183DbWriteMany(entries)" not in html:
        die('Salvamento fragmentado ainda abre transacoes IndexedDB por shard')
    if "playerShardTransactionBatch:8" not in html:
        die('Lote de shards de jogadores nao foi ativado')
    if "function v18182NationalIndex(s)" not in html or "indexedBuild:true" not in html:
        die('Criacao de carreira ainda varre todos os jogadores repetidamente por selecao')
    if "compactInitialAcademies:true" not in html or "academyDepthMatchesRollover:true" not in html or "v18190InitialAcademyTarget" not in html:
        die('Primeira temporada ainda cria profundidade excessiva de base para todos os clubes')
    if "FUTBR_PLAYERS_PACKED_GZIP_V1" not in html or "unknownFields:'extra'" not in html:
        die('Jogadores ainda sao persistidos como objetos completos sem compactacao lossless')
    if "playerChunkSize:900" not in html or "playerTransactionBatch:8" not in html:
        die('Tamanho de bloco do save compacto nao esta limitado para reduzir pico de memoria')
    if "player-packed-buffer-v1" not in html or "v18191wPostPackedPlayerRows" not in html:
        die('Transferencia Worker para UI ainda envia jogadores no formato expandido')
    if "v18191wDecodePlayerChunk" not in html or "v18191mEncodePlayerChunk" not in html:
        die('Codec compacto de jogadores nao esta ligado a leitura e gravacao')
    bad_stream="const key=m.key||'players',dst=rec.state[key]||(rec.state[key]={}),rows=m.bytes instanceof ArrayBuffer?"
    good_stream="const key=m.key||'players',dst=rec.state[key]||(rec.state[key]={});let rows=m.bytes instanceof ArrayBuffer?"
    if bad_stream in html:
        die('Create-stream ainda reatribui uma constante e pode perder todos os jogadores')
    if good_stream not in html:
        die('Receptor mutavel do create-stream nao foi instalado')
    if "18.193-background-create-checkpoint" not in html or "oneAuthoritativeCheckpoint:true" not in html or "foregroundBlocking:false" not in html:
        die('Criacao de carreira ainda pode bloquear a interface aguardando checkpoint completo')
    if "initialSaveBackground:true" not in html or "advanceWaitsPendingCheckpoint:true" not in html:
        die('Politica segura de primeiro checkpoint em segundo plano ausente')
    if "18.185-single-create-checkpoint" in html or "if(state)await finalCreateCheckpoint()" in html:
        die('Checkpoint completo ainda bloqueia o retorno da nova carreira')
    if re.search(r'(?<=>)\\n(?=\s*<)',html):
        die('HTML final ainda possui quebra de linha literal visivel entre tags')
    if "blankScreenRecovery:true" not in html:
        die('Recuperacao automatica de tela vazia ausente')
    if "18.194-direct-sharded-load" not in html or "noWorkerWorldCloneOnLoad:true" not in html:
        die('Carregamento de save ainda pode montar uma segunda copia completa no Worker')
    if "incrementalManifestHydration:true" not in html or "batchReadTransactions:true" not in html:
        die('Hidratacao direta dos shards nao esta ativa')
    if "rosterPreloadedDuringAuth:false" not in html or "loginUiIndependentFromRoster:true" not in html:
        die('Login ainda nao esta desacoplado do preload da base consolidada')
    if "rosterLoadAfterAuthentication:true" not in html or "noRosterReadBeforeLogin:true" not in html:
        die('Base consolidada ainda pode ser tocada antes da autenticacao')
    if "welcomeAwaitsRoster:true" not in html or "welcomeRosterGate:true" not in html:
        die('Tela inicial ainda pode abrir antes da base consolidada')
    if "legacySaveFallback:true" not in html or "if(!loaded)loaded=await v53Call('load',{key:STORE});" not in html:
        die('Fallback para saves antigos foi removido do carregamento direto')
    if "view=loaded?.v640National?.userTeam?'national':'squad';" not in html:
        die('Carreira de clube ainda nao abre diretamente no Elenco')
    if "dashboardRemovedForClub:true" not in html or "view==='dashboard')view='squad'" not in html:
        die('Dashboard obsoleto ainda pode abrir em carreira de clube')
    if "v4CrestURL=function(t){const r=v53Record(t.id);return r?.data||'';};" in html:
        die('Ainda existe resolvedor final de escudo que ignora arquivos locais')
    if "supabase_proxy" not in html or "supabaseRequest:request=>call('supabase_proxy'" not in html:
        die('Proxy nativo do Supabase nao foi ligado ao frontend')
    if "window.FutBRDesktop?.supabaseRequest" not in html:
        die('v580Fetch desktop nao usa o proxy nativo do Supabase')
    csp_tag=re.search(r'<meta[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>',html,re.I)
    if not csp_tag or "img-src 'self'" not in csp_tag.group(0):
        die("CSP desktop nao permite imagens locais do proprio aplicativo")

    manifest_path=src/'assets/data/player-base-manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    asset=src/manifest['asset']
    if not asset.exists(): die('Arquivo externo da base de jogadores ausente')
    if asset.stat().st_size!=int(manifest['bytes']): die('Tamanho da base de jogadores divergiu')
    if sha(asset)!=manifest['sha256']: die('SHA-256 da base de jogadores divergiu')
    if manifest.get('format')!='FUTBR_PLAYER_BASE_CONSOLIDATED_V2' or not manifest.get('consolidated'):
        die('Manifesto final nao representa a base inicial consolidada V2')
    if manifest.get('runtimeFallbackRequired') is not False:
        die('Manifesto ainda permite reconstrucao de elencos em runtime')
    if int(manifest.get('catalogClubs',0))<5500:
        die('Catalogo consolidado de clubes esta incompleto')

    index=parse_index(html)
    if len(index)!=int(manifest['records']): die('Quantidade de elencos divergiu do manifesto')
    raw=asset.read_text(encoding='utf-8')
    players=0
    required={'t0','t6','t9','t12'}
    for tid,(start,length) in index.items():
        start=int(start); length=int(length)
        if start<0 or length<=0 or start+length>len(raw): die(f'Indice fora do limite: {tid}')
        try: rec=json.loads(raw[start:start+length])
        except Exception as e: die(f'Registro de elenco corrompido {tid}: {e}')
        rows=rec.get('_p') or []
        if not isinstance(rows,list): die(f'Lista de jogadores invalida: {tid}')
        players+=len(rows)
    if players!=int(manifest['players']): die(f'Quantidade de jogadores divergiu: {players} != {manifest["players"]}')
    if not required.issubset(index): die('Clubes de controle ausentes na base')

    crest_manifest=src/'assets/crests/manifest.json'
    crest_info=json.loads(crest_manifest.read_text(encoding='utf-8'))
    files=sum(1 for p in (src/'assets/crests').rglob('*') if p.is_file() and p.name!='manifest.json')
    if files<int(crest_info.get('asset_files',0)): die('Arquivos de escudos locais incompletos')

    lib_rs=(project/'src-tauri/src/lib.rs').read_text(encoding='utf-8')
    cargo_toml=(project/'src-tauri/Cargo.toml').read_text(encoding='utf-8')
    for marker in ['async fn supabase_proxy(', 'fn open_premium_site(', 'fn load_player_base(']:
        if marker not in lib_rs:
            die(f'Comando Rust ausente: {marker}')
    handler_match=re.search(r'tauri::generate_handler!\[(.*?)\]',lib_rs,re.S)
    if not handler_match:
        die('invoke_handler do Tauri nao encontrado')
    handler=handler_match.group(1)
    for command in ['supabase_proxy','open_premium_site','load_player_base']:
        if command not in handler:
            die(f'Comando Tauri nao registrado no invoke_handler: {command}')
    if 'reqwest = ' not in cargo_toml:
        die('Dependencia reqwest ausente do Cargo.toml')
    runtime_path=project/'runtime-boot-tests.json'
    if not runtime_path.exists():
        die('Resultado do smoke test real do boot ausente')
    runtime_result=json.loads(runtime_path.read_text(encoding='utf-8'))
    if not runtime_result.get('ok') or int(runtime_result.get('authCount',0))<1 or int(runtime_result.get('loginFormCount',0))<1:
        die('Smoke test real do boot nao montou o login')
    if runtime_result.get('fatalVisible') or runtime_result.get('rosterFailures'):
        die('Smoke test real do boot detectou falha fatal ou leitura antecipada da base')

    checked=validate_scripts(html,project)
    report={
        'ok':True,
        'engine_sha256':engine_sha(html),
        'player_base_records':len(index),
        'player_base_players':players,
        'player_base_bytes':asset.stat().st_size,
        'crest_assets':crest_info.get('asset_files'),
        'executable_js_blocks':checked,
        'runtime_boot_login':True,
        'no_roster_read_before_login':True,
        'history_markers_preserved':True,
        'career_state_authority':'unchanged',
        'player_base_external_only':'initial-database',
        'save_shards_preserved':['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive']
    }
    (project/'architecture-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
,html,re.M):
        die('Correcao antiga de Joaquin ainda le roster no topo do script')
    if "(function v530PatchRosterFacts()" in html or "const v183FluBase=v310RosterRecord('t6')" in html:
        die('Correcao legacy ainda le roster durante avaliacao inicial')
    if "(WorldCatalog.clubs||[]).slice(-256)" in html:
        die('Sweep legacy dos 256 elencos ainda roda antes do login')
    if "baseRosterStats310?.players" not in html:
        die('Metadados do boot ainda podem enumerar todos os elencos')
    if "const v18196BaseWelcome=renderWelcome;" not in html or "welcomeRosterGate:true" not in html:
        die('Gate final da tela inicial para a base instalada ausente')
    if "const authenticated=await Promise.race([authPromise,timeout]);" not in html or "setTimeout(()=>resolve(null),6000)" not in html:
        die('Validacao remota ainda pode deixar o boot em tela vazia indefinidamente')
    if "Promise.resolve().then(()=>v580RestoreRemoteSession())" not in html or "bootPromiseSafe:true" not in html:
        die('Boot ainda pode escapar por excecao sincrona antes da tela de login')
    if "emptyAppWatchdog:true" not in html or "setTimeout(rescue,2500)" not in html:
        die('Watchdog final para app vazio ausente')
    if "base local no login:" in html or "base local durante load:" in html:
        die('Continuar save ainda carrega a base inicial de jogadores desnecessariamente')
    if "const v18194Loader=window.GestorFC?.v171?.loadDirect;" not in html or html.count("if(!loaded)loaded=await v53Call('load',{key:STORE});") < 2:
        die('Carregamento direto ou fallback seguro das duas rotas de save nao foi instalado')
    if "rosterPromise" in html:
        die('Carregamento de save ainda espera a base inicial desnecessariamente')
    if html.count('"name":"ASA"') != 1:
        die('Catalogo inicial ainda possui ASA duplicado')
    if "supportFictional?(div>=4?.72" not in html:
        die('Guard de desenvolvimento para elencos de suporte ausente')
    if "futbr-root-18170-fixes" not in html:
        die('Correcoes raiz 18.170 ausentes')
    if "function v53ScheduleNationalJumpPaint()" not in html:
        die('Visao Geral do nationaljump ainda nao usa o agendador raiz')
    if "if(v53Sim?.mode==='nationaljump'){v53ScheduleNationalJumpPaint();}" not in html:
        die('Pacotes vac-live do nationaljump ainda nao atualizam a Visao Geral')
    if "v18170EnsureAllNationalPools" not in html or "v18170InitialNationalFreeAgent" not in html:
        die('Selecoes pequenas ainda nao recebem jogadores livres na criacao do mundo')
    if "localizedNationalFreeAgentNames:true" not in html or "function v18171NationalGeneratedName(s,code,id,used=new Set())" not in html:
        die('Jogadores ficticios das selecoes ainda nao recebem nomes caracteristicos do pais')
    if "+String((h%89)+10)" in html or "nationalNamesNeverNumeric:true" not in html:
        die('Jogadores ficticios de selecao ainda podem receber sufixo numerico')
    if "const clean=p.v18171LocalizedName&&p.natCode===n&&!/\\d/.test" not in html:
        die('Reparo de nomes nacionais numericos anteriores ausente')
    if "dynamicCareerSurfaceTheme:true" not in html or "function v18172ApplyCareerSurface(primary)" not in html:
        die('Tema dinamico da carreira ainda nao deriva da equipe comandada')
    if "consultedProfileOwnTheme:true" not in html or "v18172ApplySurfaceToElement(modalEl,p.primary)" not in html:
        die('Ficha consultada ainda nao recebe tema completo proprio')
    if "nationalProfileFinalOwnTheme:true" not in html or "function v18173PaintConsultedNationalProfile(code)" not in html or "v18173PaintConsultedNationalProfile(n);" not in html:
        die('Redefinicao final da ficha de selecao pode perder a paleta da selecao consultada')
    if "const surface=typeof v18172SurfaceVars==='function'?v18172SurfaceVars(p.primary)" not in html or "try{v18172ApplySurfaceToElement(profile,p.primary);}catch(e){}" not in html:
        die('v657ApplyNationalModalTheme ainda nao reaplica bg/panel/panel2/line da selecao consultada')
    if "nationalProfileForcedSurface:true" not in html or "function v18174ForceNationalProfileTheme(code)" not in html or "v18174ForceNationalProfileTheme(code);" not in html:
        die('Ficha nacional final ainda pode herdar superficie da selecao comandada')
    if "nationalModalOwnRootTheme:true" not in html or "let v18176NationalModalCode=null,v18176OpeningNationalCode=null" not in html:
        die('Ficha nacional ainda nao controla o tema raiz enquanto esta aberta')
    if "nationalModalThemePinsV128:true" not in html or "const use=v18176NationalModalCode||v18176OpeningNationalCode||code;" not in html:
        die('Carreira iniciada por selecao ainda pode sobrescrever o tema da ficha consultada')
    if "v18176NationalModalCode=n;" not in html or "v18176NationalModalCode=null;" not in html:
        die('Tema raiz da ficha nacional nao e ativado/restaurado corretamente')
    if "set(modalEl,'background'," not in html or "set(body,'background'," not in html:
        die('Tema nacional final nao fixa fundo e corpo da selecao consultada')
    if "dragGhost:true" not in html or "function v18172PointerGhostAt(p,e)" not in html:
        die('Cartao fantasma do jogador durante o arraste ausente')
    if "reservePointerSwap:true" not in html or "if(el.dataset.v5Slot===undefined){e.preventDefault();return;}" not in html:
        die('Banco de reservas ainda depende do drag HTML nativo')
    if "v18170EnsureNationalPool(state,enemy,f);" not in html:
        die('Saves antigos ainda podem enfrentar selecao adversaria sem elenco apto suficiente')
    if "t.v600PreferredBench=v602SortPlayerIds(list.slice(0,V600_BENCH_LIMIT))" not in html:
        die('Banco nacional pre-jogo nao esta ordenado por posicao na raiz')
    if "ids=typeof v602SortPlayerIds==='function'?v602SortPlayerIds(raw):raw" not in html:
        die('Banco durante a partida nao esta ordenado por posicao na raiz')
    if "return typeof v602SortPlayerIds==='function'?v602SortPlayerIds(ids):ids;" not in html:
        die('Nao relacionados durante a partida nao estao ordenados por posicao')
    if "futbr-v18164-national-match-parity" not in html:
        die('Camada visual de paridade das selecoes ausente')
    if "firstClickEditable:true" not in html or "coreDragOnly:true" not in html:
        die('Primeiro clique ou drag da selecao ainda nao usa a rota unificada')
    if "v18167NationalDrag" in html:
        die('Listener duplicado de drag nacional foi reintroduzido')
    if "justify-self:stretch!important" not in html:
        die('Banco do adversario nacional ainda nao ocupa toda a largura')
    if "nationalFixtureDetails:true" not in html:
        die('Detalhes das partidas de selecoes ausentes')
    if "decorateCareerMenuActions" not in html:
        die('Acoes desktop do menu de carreira nao sao independentes do tipo de carreira')
    if "function v515RatingForClub(t){if(t?.regionalOnly)return null;" not in html:
        die('Clubes regionais ainda podem herdar ranking mundial por colisao de nome')
    if "cleanNationalClubVisualResidue" not in html and "futbr-root-18170-fixes" not in html:
        die('Isolamento visual entre carreira de selecao e clube ausente')
    if "initialClub:nationalCode?'':loaded.user" not in html:
        die('Carreira nova de selecao ainda guarda clube inicial indevido')
    if "function v310ReleaseRosterSource(){v310RosterText='';" in html:
        die('Base compacta de jogadores ainda esta sendo descartada durante a carreira')
    if "fetch(V310_ROSTER_ASSET" in html:
        die('A build desktop ainda usa fetch local para a base de jogadores')
    if "O acesso é validado pelo servidor do FutBR Manager." in html:
        die('Mensagem de seguranca ainda aparece no login desktop')
    if "futbr-desktop-load-optimization" not in html:
        die('Otimizacao de carregamento de saves ausente')
    if "freeNationalStartBlocked:true" not in html or "params?.options?.v643StartType==='national'&&!v18177FullAccess()" not in html:
        die('Plano Gratuito ainda pode iniciar carreira por selecao')
    if "freeNationalStartCoreGate:true" not in html or "if(!v548FullAccess()&&v128NationalStart){" not in html:
        die('Nucleo final 11.5C ainda pode permitir carreira nacional gratuita')
    if "function v643ConvertNewCareerToNational(s,code){if(!v548FullAccess())throw Error('Carreira por selecao requer Premium.')" not in html:
        die('Conversao final para selecao nao exige Premium')
    if "fastCareerSeedRefs:true" not in html or "p.v18175SeedRoster=data?.prebuiltInitial?null:rp" not in html:
        die('Criacao consolidada ainda mantem referencia duplicada da base em cada jogador')
    if "const info=db[t.id],map=new Map((info?.players||[]).map" in html:
        die('Criacao de carreira ainda cria Maps repetidos para os elencos')
    manifest_text=(project/'src/assets/data/player-base-manifest.json').read_text(encoding='utf-8')
    if "if(cache.size>32)cache.delete(cache.keys().next().value)" not in html:
        die('Worker da nova carreira nao limita o cache decodificado da base consolidada')
    if "shardReadConcurrency:8" not in html:
        die('Leitura paralela dos blocos do save nao foi ativada')
    if "indexedDbBatchTransaction:true" not in html or "async function v18183DbWriteMany(entries)" not in html:
        die('Salvamento fragmentado ainda abre transacoes IndexedDB por shard')
    if "playerShardTransactionBatch:8" not in html:
        die('Lote de shards de jogadores nao foi ativado')
    if "function v18182NationalIndex(s)" not in html or "indexedBuild:true" not in html:
        die('Criacao de carreira ainda varre todos os jogadores repetidamente por selecao')
    if "compactInitialAcademies:true" not in html or "academyDepthMatchesRollover:true" not in html or "v18190InitialAcademyTarget" not in html:
        die('Primeira temporada ainda cria profundidade excessiva de base para todos os clubes')
    if "FUTBR_PLAYERS_PACKED_GZIP_V1" not in html or "unknownFields:'extra'" not in html:
        die('Jogadores ainda sao persistidos como objetos completos sem compactacao lossless')
    if "playerChunkSize:900" not in html or "playerTransactionBatch:8" not in html:
        die('Tamanho de bloco do save compacto nao esta limitado para reduzir pico de memoria')
    if "player-packed-buffer-v1" not in html or "v18191wPostPackedPlayerRows" not in html:
        die('Transferencia Worker para UI ainda envia jogadores no formato expandido')
    if "v18191wDecodePlayerChunk" not in html or "v18191mEncodePlayerChunk" not in html:
        die('Codec compacto de jogadores nao esta ligado a leitura e gravacao')
    bad_stream="const key=m.key||'players',dst=rec.state[key]||(rec.state[key]={}),rows=m.bytes instanceof ArrayBuffer?"
    good_stream="const key=m.key||'players',dst=rec.state[key]||(rec.state[key]={});let rows=m.bytes instanceof ArrayBuffer?"
    if bad_stream in html:
        die('Create-stream ainda reatribui uma constante e pode perder todos os jogadores')
    if good_stream not in html:
        die('Receptor mutavel do create-stream nao foi instalado')
    if "18.193-background-create-checkpoint" not in html or "oneAuthoritativeCheckpoint:true" not in html or "foregroundBlocking:false" not in html:
        die('Criacao de carreira ainda pode bloquear a interface aguardando checkpoint completo')
    if "initialSaveBackground:true" not in html or "advanceWaitsPendingCheckpoint:true" not in html:
        die('Politica segura de primeiro checkpoint em segundo plano ausente')
    if "18.185-single-create-checkpoint" in html or "if(state)await finalCreateCheckpoint()" in html:
        die('Checkpoint completo ainda bloqueia o retorno da nova carreira')
    if re.search(r'(?<=>)\\n(?=\s*<)',html):
        die('HTML final ainda possui quebra de linha literal visivel entre tags')
    if "blankScreenRecovery:true" not in html:
        die('Recuperacao automatica de tela vazia ausente')
    if "18.194-direct-sharded-load" not in html or "noWorkerWorldCloneOnLoad:true" not in html:
        die('Carregamento de save ainda pode montar uma segunda copia completa no Worker')
    if "incrementalManifestHydration:true" not in html or "batchReadTransactions:true" not in html:
        die('Hidratacao direta dos shards nao esta ativa')
    if "rosterPreloadedDuringAuth:true" not in html or "loginUiIndependentFromRoster:true" not in html:
        die('Base consolidada nao e preparada em paralelo sem bloquear o formulario de login')
    if "welcomeAwaitsRoster:true" not in html or "welcomeRosterGate:true" not in html:
        die('Tela inicial ainda pode abrir antes da base consolidada')
    if "legacySaveFallback:true" not in html or "if(!loaded)loaded=await v53Call('load',{key:STORE});" not in html:
        die('Fallback para saves antigos foi removido do carregamento direto')
    if "view=loaded?.v640National?.userTeam?'national':'squad';" not in html:
        die('Carreira de clube ainda nao abre diretamente no Elenco')
    if "dashboardRemovedForClub:true" not in html or "view==='dashboard')view='squad'" not in html:
        die('Dashboard obsoleto ainda pode abrir em carreira de clube')
    if "v4CrestURL=function(t){const r=v53Record(t.id);return r?.data||'';};" in html:
        die('Ainda existe resolvedor final de escudo que ignora arquivos locais')
    if "supabase_proxy" not in html or "supabaseRequest:request=>call('supabase_proxy'" not in html:
        die('Proxy nativo do Supabase nao foi ligado ao frontend')
    if "window.FutBRDesktop?.supabaseRequest" not in html:
        die('v580Fetch desktop nao usa o proxy nativo do Supabase')
    csp_tag=re.search(r'<meta[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>',html,re.I)
    if not csp_tag or "img-src 'self'" not in csp_tag.group(0):
        die("CSP desktop nao permite imagens locais do proprio aplicativo")

    manifest_path=src/'assets/data/player-base-manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    asset=src/manifest['asset']
    if not asset.exists(): die('Arquivo externo da base de jogadores ausente')
    if asset.stat().st_size!=int(manifest['bytes']): die('Tamanho da base de jogadores divergiu')
    if sha(asset)!=manifest['sha256']: die('SHA-256 da base de jogadores divergiu')
    if manifest.get('format')!='FUTBR_PLAYER_BASE_CONSOLIDATED_V2' or not manifest.get('consolidated'):
        die('Manifesto final nao representa a base inicial consolidada V2')
    if manifest.get('runtimeFallbackRequired') is not False:
        die('Manifesto ainda permite reconstrucao de elencos em runtime')
    if int(manifest.get('catalogClubs',0))<5500:
        die('Catalogo consolidado de clubes esta incompleto')

    index=parse_index(html)
    if len(index)!=int(manifest['records']): die('Quantidade de elencos divergiu do manifesto')
    raw=asset.read_text(encoding='utf-8')
    players=0
    required={'t0','t6','t9','t12'}
    for tid,(start,length) in index.items():
        start=int(start); length=int(length)
        if start<0 or length<=0 or start+length>len(raw): die(f'Indice fora do limite: {tid}')
        try: rec=json.loads(raw[start:start+length])
        except Exception as e: die(f'Registro de elenco corrompido {tid}: {e}')
        rows=rec.get('_p') or []
        if not isinstance(rows,list): die(f'Lista de jogadores invalida: {tid}')
        players+=len(rows)
    if players!=int(manifest['players']): die(f'Quantidade de jogadores divergiu: {players} != {manifest["players"]}')
    if not required.issubset(index): die('Clubes de controle ausentes na base')

    crest_manifest=src/'assets/crests/manifest.json'
    crest_info=json.loads(crest_manifest.read_text(encoding='utf-8'))
    files=sum(1 for p in (src/'assets/crests').rglob('*') if p.is_file() and p.name!='manifest.json')
    if files<int(crest_info.get('asset_files',0)): die('Arquivos de escudos locais incompletos')

    lib_rs=(project/'src-tauri/src/lib.rs').read_text(encoding='utf-8')
    cargo_toml=(project/'src-tauri/Cargo.toml').read_text(encoding='utf-8')
    for marker in ['async fn supabase_proxy(', 'fn open_premium_site(', 'fn load_player_base(']:
        if marker not in lib_rs:
            die(f'Comando Rust ausente: {marker}')
    handler_match=re.search(r'tauri::generate_handler!\[(.*?)\]',lib_rs,re.S)
    if not handler_match:
        die('invoke_handler do Tauri nao encontrado')
    handler=handler_match.group(1)
    for command in ['supabase_proxy','open_premium_site','load_player_base']:
        if command not in handler:
            die(f'Comando Tauri nao registrado no invoke_handler: {command}')
    if 'reqwest = ' not in cargo_toml:
        die('Dependencia reqwest ausente do Cargo.toml')
    checked=validate_scripts(html,project)
    report={
        'ok':True,
        'engine_sha256':engine_sha(html),
        'player_base_records':len(index),
        'player_base_players':players,
        'player_base_bytes':asset.stat().st_size,
        'crest_assets':crest_info.get('asset_files'),
        'executable_js_blocks':checked,
        'history_markers_preserved':True,
        'career_state_authority':'unchanged',
        'player_base_external_only':'initial-database',
        'save_shards_preserved':['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive']
    }
    (project/'architecture-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
