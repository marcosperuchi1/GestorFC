# FutBR Manager 18.339 — atualizações automáticas do Windows

A versão 18.339 introduz o atualizador **assinado do Tauri 2**. Quem já instalou 18.338 ou anterior deverá instalar 18.339 manualmente uma única vez; os próximos instaladores poderão ser entregues pelo atualizador incorporado.

## 1. Gerar e proteger a chave de assinatura (uma vez)

O plugin Tauri updater **recusa atualizações sem assinatura válida**. A chave privada nunca deve entrar no GitHub como arquivo, aparecer nos logs, nem ser enviada pelo chat. Guarde uma cópia offline segura: perder essa chave impossibilita atualizar instalações já distribuídas com sua chave pública correspondente.

Em um projeto Tauri 2 com Node e a CLI instalada, execute em PowerShell:

    New-Item -ItemType Directory -Force "$env:USERPROFILE\.tauri"
    npm run tauri signer generate -- --write-keys "$env:USERPROFILE\.tauri\futbr-manager.key"

Use uma senha forte quando a CLI solicitar. O comando cria um arquivo privado .key e um arquivo público .key.pub.

No repositório GestorFC: **Settings → Secrets and variables → Actions**:

- Em **Repository secrets**, crie TAURI_SIGNING_PRIVATE_KEY com o conteúdo integral do arquivo .key.
- Em **Repository secrets**, crie TAURI_SIGNING_PRIVATE_KEY_PASSWORD com a senha escolhida (se configurou senha).
- Em **Repository variables**, crie FUTBR_UPDATER_PUBLIC_KEY com o conteúdo integral do arquivo .key.pub (incluindo a linha de comentário).
- Opcional: defina FUTBR_UPDATE_FEED_URL com a URL HTTPS pública de latest.json e FUTBR_UPDATE_ASSET_BASE_URL com a pasta pública em que ficarão os instaladores.

**Atenção:** Tauri não usa certificados Windows ou Supabase como substitutos da chave de assinatura do updater.

## 2. Configurar o Cloudflare R2 (opcional para gerar o .exe; obrigatório para o auto-update funcionar)

Este fluxo envia um instalador NSIS assinado e latest.json para a pasta updates/ do bucket R2. Configure as seguintes Repository variables e secrets:

| Tipo | Nome |
| ---- | ---- |
| Variable | R2_ACCOUNT_ID |
| Variable | R2_BUCKET |
| Secret | R2_ACCESS_KEY_ID |
| Secret | R2_SECRET_ACCESS_KEY |
| Variable (opcional) | FUTBR_UPDATE_FEED_URL |
| Variable (opcional) | FUTBR_UPDATE_ASSET_BASE_URL |

O endpoint compilado padrão é https://futbrmanager.com.br/updates/latest.json e a URL padrão dos pacotes é https://futbrmanager.com.br/updates/. É necessário que essas URLs realmente sirvam os objetos públicos do bucket, por uma rota Cloudflare Worker/Pages ou domínio personalizado R2.

Uma alternativa é usar um domínio público de R2 e declarar:
- FUTBR_UPDATE_FEED_URL = https://updates.futbrmanager.com.br/updates/latest.json
- FUTBR_UPDATE_ASSET_BASE_URL = https://updates.futbrmanager.com.br/updates

Confirme que GET do JSON retorna HTTP 200 e JSON válido. O arquivo publicado deve conter a assinatura literal da .sig e a URL HTTPS do EXE assinado.

## 3. Rodar a única compilação de 18.339

Abra **Actions → FutBR Windows 18.339 - atualizador assinado → Run workflow**, selecione a branch feature/desktop-18339-auto-updates.

O workflow executa primeiro testes isolados sem usar credenciais. Sem as chaves, **não compila nem oferece um instalador falsamente atualizável**. Com as chaves corretas, recompõe a base Windows validada 18.338, aplica a navegação contextual do histórico de campeões, mantém os testes de saves longos, instala o updater e compila NSIS assinado. O resultado aparece no artifact:

    FutBR-Manager-18.339-Windows-Signed-Update

O artifact contém EXE, .sig, latest.json e relatórios. Nenhuma chave privada é incluída.

Se as variáveis R2 também estiverem configuradas, o workflow faz upload do executável e assinatura primeiro e publica latest.json por último, impedindo que o jogo receba um manifesto apontando para um instalador ainda não disponível.

## 4. Segurança e teste com carreira antiga

1. Faça uma cópia de segurança do save existente antes do primeiro teste de atualização.
2. Instale a versão 18.339 por cima da anterior, sem remover os dados do aplicativo.
3. Abra uma carreira antiga, valide o histórico específico da competição e salve/saia.
4. No próximo release (por exemplo 18.340.0), o jogo verificará a URL pública automaticamente ao iniciar. Quando houver versão maior, mostrará **Salvar e atualizar** ou **Depois**.
5. Se houver carreira ativa, o jogo valida e confirma o checkpoint atômico de 18.338 antes de chamar o instalador. A atualização é cancelada caso o save falhe ou haja partida, férias ou sincronização em andamento.
6. O Tauri valida a assinatura Ed25519 da atualização recebida antes de iniciar o instalador; em Windows a instalação fecha o aplicativo.

As atualizações são oferecidas a contas gratuitas e Premium, sem substituir o sistema de login/licenciamento. O novo instalador preserva o mesmo identificador de aplicativo e a mesma pasta de dados.

## 5. Publicação de 18.340+

Uma vez distribuída a primeira versão com chave pública embutida, **não altere o par de chaves** nas próximas compilações. Incremente a versão SemVer do Tauri, gere e assine o NSIS com TAURI_SIGNING_PRIVATE_KEY, publique o novo EXE em URL HTTPS própria e publique latest.json por último. Um release que altere a chave privada sem procedimento de rotação que preserve a confiança da chave antiga não atualizará as instalações existentes.

Não considere a distribuição automática validada até testar em duas instalações reais: uma na versão 18.339 e outra já atualizada para 18.340.
