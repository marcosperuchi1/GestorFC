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
    if "async function v548EnterGame(){try{v310StartRosterLoad?.().catch(e=>console.warn('[FutBR] base local em segundo plano:'" not in html:
        die('Boot desktop ainda bloqueia a entrada esperando a base inicial de jogadores')
    if "const authenticated=await Promise.race([authPromise,timeout]);" not in html or "setTimeout(()=>resolve(null),6000)" not in html:
        die('Validacao remota ainda pode deixar o boot em tela vazia indefinidamente')
    if "v310StartRosterLoad?.().catch(e=>console.warn('[FutBR] base local no login:'" not in html:
        die('Tela de login nao inicia preload silencioso da base de jogadores')
    if "const loaded=await v53Call('load',{key:STORE});" not in html or "rosterPromise" in html:
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
    if "roster_source_retained_for_sync_reads" not in (project/'src/assets/data/player-base-manifest.json').read_text(encoding='utf-8'):
        die('Manifesto nao confirma preservacao da base compacta durante a carreira')
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
    if "fastCareerSeedRefs:true" not in html or "p.v18175SeedRoster=rp" not in html or "p.real?(p.v18175SeedRoster||null):null" not in html:
        die('Criacao de carreira ainda reconstrui relacionamentos da base por nome')
    if "const info=db[t.id],map=new Map((info?.players||[]).map" in html:
        die('Criacao de carreira ainda cria Maps repetidos para os elencos')
    manifest_text=(project/'src/assets/data/player-base-manifest.json').read_text(encoding='utf-8')
    if "parse-once-transient-create-cache" not in manifest_text:
        die('Worker da nova carreira ainda nao usa cache transitorio parse-once')
    if "shardReadConcurrency:8" not in html:
        die('Leitura paralela dos blocos do save nao foi ativada')
    if "indexedDbBatchTransaction:true" not in html or "async function v18183DbWriteMany(entries)" not in html:
        die('Salvamento fragmentado ainda abre transacoes IndexedDB por shard')
    if "playerShardTransactionBatch:4" not in html:
        die('Lote de shards de jogadores nao foi ativado')
    if "function v18182NationalIndex(s)" not in html or "indexedBuild:true" not in html:
        die('Criacao de carreira ainda varre todos os jogadores repetidamente por selecao')
    if re.search(r'</(?:script|style)>\\\\n(?=\\s*<)',html,re.I):
        die('HTML final ainda possui quebra de linha literal visivel entre tags')
    if "blankScreenRecovery:true" not in html:
        die('Recuperacao automatica de tela vazia ausente')
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
    if engine_sha(html)!=manifest['engine_sha256']: die('Motor de simulacao foi alterado durante a otimizacao')

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
        'engine_sha256':manifest['engine_sha256'],
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
