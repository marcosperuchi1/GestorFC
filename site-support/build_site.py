#!/usr/bin/env python3
"""Rebuild original live Direct Upload assets plus FutBR support/legal edits.
Keeps all production original files; never deletes assets. Output zip is ready for manual
Cloudflare Pages Direct Upload after review. Source site remains unmodified by this script.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import zipfile
from pathlib import Path

BASE = 'https://futbrmanager.com.br'
OUT = Path('site-support/dist')
ORIGINAL = OUT / 'original'
DEPLOY = OUT / 'deploy'
FILES = (
  'index.html',
  'app.js',
  'config.js',
  'styles.css',
  'homologacao.html',
  'homologacao.js',
  'assets/futbr-logo.png',
)
TERMS_HTML = "<div class=\"legal-document\"><p class=\"legal-meta\">Última atualização: 17 de novembro de 2026</p><h3>1. Sobre o FutBR Manager</h3><p>O FutBR Manager é um jogo de gerenciamento de futebol, disponível para uso gratuito com funcionalidades adicionais no plano Premium. Ao criar uma conta, acessar o site ou utilizar o jogo, você concorda com estes termos e com a legislação aplicável.</p><h3>2. Conta e acesso</h3><p>O cadastro é pessoal. Use informações corretas, mantenha a senha em segurança e não compartilhe indevidamente sua conta. O mesmo e-mail cadastrado permite identificar sua licença no site e no jogo.</p><h3>3. Plano gratuito e licença Premium</h3><p>O plano gratuito permite experimentar os recursos disponíveis sem pagamento. O Premium é oferecido por compra única, sem mensalidade ou renovação automática, e fica vinculado à conta utilizada no pagamento. O preço final e os meios de pagamento são informados antes da conclusão da compra.</p><p>O processamento é realizado pelo Mercado Pago. A ativação do Premium depende da confirmação do pagamento pela operadora; o simples retorno à página não significa aprovação da compra. A licença Premium atualmente permite até dois dispositivos autorizados por conta.</p><h3>4. Arrependimento, cancelamento e reembolso</h3><p>Compras realizadas pela internet estão sujeitas ao direito de arrependimento previsto no artigo 49 do Código de Defesa do Consumidor, no prazo legal de sete dias. Para solicitar orientação ou reembolso, abra um chamado de “Pagamento / Premium” em <a href=\"/suporte.html\">nossa Central de Suporte</a> ou escreva para <a href=\"mailto:marcosperuchi1@gmail.com\">marcosperuchi1@gmail.com</a>. Cada solicitação será analisada conforme a legislação aplicável e as condições da compra.</p><h3>5. Atualizações, funcionamento e salvamentos</h3><p>O jogo recebe melhorias, correções e atualizações de versão. Algumas funcionalidades podem mudar ao longo do desenvolvimento. Os arquivos de carreira (saves) são mantidos localmente no dispositivo ou na instalação utilizada, e não são hospedados automaticamente na nuvem. Recomendamos manter cópias de segurança de seus saves.</p><h3>6. Uso responsável e propriedade intelectual</h3><p>O usuário deve utilizar o serviço de maneira lícita, sem tentar fraudar pagamentos, contornar licenças, comprometer a segurança ou redistribuir indevidamente o software e seus componentes. Marcas e conteúdos de terceiros pertencem aos respectivos titulares.</p><h3>7. Suporte e alterações destes termos</h3><p>Problemas técnicos, dúvidas e sugestões podem ser enviados pela <a href=\"/suporte.html\">Central de Suporte</a>. Estes termos poderão ser atualizados para refletir mudanças no serviço ou na legislação, respeitando os direitos já assegurados ao consumidor. Consulte a data indicada no início deste documento.</p></div>"
PRIVACY_HTML = "<div class=\"legal-document\"><p class=\"legal-meta\">Última atualização: 17 de novembro de 2026</p><h3>1. Responsável e contato</h3><p>O FutBR Manager trata os dados necessários para oferecer o site, o jogo, o acesso à conta e as licenças. Para esclarecimentos ou para exercer direitos relacionados aos seus dados pessoais, utilize a <a href=\"/suporte.html\">Central de Suporte</a> ou entre em contato pelo e-mail <a href=\"mailto:marcosperuchi1@gmail.com\">marcosperuchi1@gmail.com</a>.</p><h3>2. Dados utilizados</h3><p>Podemos tratar o e-mail cadastrado, o identificador da conta, informações técnicas de autenticação e dispositivos autorizados, dados da licença, histórico e estado de pedidos, informações fornecidas nos chamados de suporte e registros técnicos necessários à segurança e ao funcionamento do serviço.</p><p>A senha é gerenciada pelo serviço de autenticação. Dados completos de cartão não são armazenados pelo FutBR Manager; o pagamento é realizado no ambiente do provedor de pagamentos.</p><h3>3. Para que usamos esses dados</h3><p>Os dados são usados para cadastrar e autenticar contas, disponibilizar recursos gratuitos e Premium, confirmar compras, prevenir fraudes, atender solicitações, corrigir problemas e cumprir obrigações legais. O tratamento observa as bases legais aplicáveis, incluindo execução de contrato, cumprimento de obrigação legal e interesses legítimos compatíveis com os direitos dos titulares.</p><h3>4. Prestadores de serviços</h3><p>Utilizamos o Supabase para autenticação e controle de acesso, o Mercado Pago para pagamentos e o Cloudflare para hospedagem e entrega do site. Esses prestadores podem tratar dados técnicos e operacionais necessários à prestação dos respectivos serviços, conforme seus próprios avisos de privacidade e contratos.</p><h3>5. Sessões, segurança e armazenamento</h3><p>O site e o jogo podem guardar identificadores e dados técnicos de sessão no dispositivo para manter o acesso autenticado. Aplicamos controles de acesso e restrições para que usuários comuns não visualizem os chamados de outras pessoas. Nenhum serviço conectado à internet é totalmente isento de riscos.</p><p>Os saves das carreiras permanecem no dispositivo ou instalação do usuário; não são enviados automaticamente ao Supabase como backup de partidas.</p><h3>6. Conservação dos dados</h3><p>As informações são mantidas enquanto forem necessárias ao funcionamento da conta e às finalidades descritas, ou pelo prazo exigido por obrigações legais, prevenção de fraude e resolução de disputas. Após isso, poderão ser eliminadas ou anonimizadas quando permitido pela legislação.</p><h3>7. Seus direitos</h3><p>Nos termos da Lei Geral de Proteção de Dados (LGPD), você pode solicitar confirmação de tratamento, acesso, correção, informações sobre compartilhamento, eliminação ou anonimização quando cabível e outros direitos aplicáveis. A solicitação pode ser feita pela <a href=\"/suporte.html\">Central de Suporte</a> ou pelo e-mail informado acima. Poderemos solicitar a verificação da identidade para proteger a conta.</p><h3>8. Atualizações desta política</h3><p>Esta política poderá mudar para refletir melhorias do serviço, novos recursos ou exigências legais. A versão mais recente estará disponível no site com a data da atualização.</p></div>"

def fetch_asset(path: str) -> bytes:
    req = urllib.request.Request(BASE + '/' + path, headers={'User-Agent': 'Mozilla/5.0 (compatible; FutBR-Release-Builder/1.0)', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=45) as resp:
        assert resp.status == 200, (path, resp.status)
        content = resp.read()
        ctype = resp.headers.get('Content-Type', '').lower()
        if path.endswith('.html'):
            assert b'<!doctype html' in content[:500].lower(), (path,'Not an HTML page')
        if path.endswith('.js'):
            assert 'javascript' in ctype or path == 'config.js' and content.startswith(b'//'), (path,ctype)
        if path.endswith('.css'):
            assert b'--forest' in content or b':root' in content, (path,'invalid stylesheet')
        if path.endswith('.png'):
            assert content[:8] == b'\x89PNG\r\n\x1a\n', (path,'invalid PNG')
        return content

def patch_site():
    ORIGINAL.mkdir(parents=True,exist_ok=True)
    DEPLOY.mkdir(parents=True,exist_ok=True)
    originals={}
    for path in FILES:
        body=fetch_asset(path)
        originals[path]=hashlib.sha256(body).hexdigest()
        target=ORIGINAL / path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(body)
        t=DEPLOY / path
        t.parent.mkdir(parents=True,exist_ok=True)
        t.write_bytes(body)

    app=(DEPLOY/'app.js').read_text(encoding='utf-8')
    assert 'store-create-checkout' in app and 'store-reconcile' in app
    # Only the explicitly identified legal modal and footer contact functions are replaced.
    start=app.index('  function info(kind){')
    end=app.index('  function wire(){',start)
    assert 'Documento preliminar' in app[start:end]
    modal=(
      '  function info(kind){\n'
      "    const terms=kind==='terms';\n"
      "    $('info-title').textContent=terms?'Termos de Uso':'Privacidade e Dados';\n"
      "    $('info-content').innerHTML=terms?"+json.dumps(TERMS_HTML,ensure_ascii=False)+':'+json.dumps(PRIVACY_HTML,ensure_ascii=False)+';\n'
      "    show('info-backdrop');\n"
      "  }\n"
    )
    app=app[:start]+modal+app[end:]
    start=app.index('  function setSupport(){')
    end=app.index('  function configureDownload(){',start)
    app=app[:start]+(
      '  function setSupport(){\n'
      "    const link=$('support-link');\n"
      "    link.href='/suporte.html';\n"
      "    link.textContent='Suporte e Feedback';\n"
      "    link.removeAttribute('aria-disabled');\n"
      '  }\n'
    )+app[end:]
    assert app.count('function info(kind)')==1
    assert app.count('function setSupport()')==1
    assert 'Documento preliminar' not in app
    assert 'store-create-checkout' in app and 'store-reconcile' in app
    (DEPLOY/'app.js').write_text(app,encoding='utf-8')

    index=(DEPLOY/'index.html').read_text(encoding='utf-8')
    assert 'id="info-content"' in index and 'id="support-link"' in index, 'Site structure changed; abort'
    if 'href="/suporte.html"' not in index:
        # Append one link to desktop header nav; footer support link handled in app.js.
        nav=re.search(r'(<nav\b[^>]*class="[^"]*desktop-nav[^"]*"[^>]*>)(.*?)(</nav>)', index, flags=re.I|re.S)
        if nav:
            index=index[:nav.end(2)]+ '  <a href="/suporte.html">Suporte</a>\n' +index[nav.start(3):]
        else:
            raise RuntimeError('desktop nav changed; refusing unverified modification')
    (DEPLOY/'index.html').write_text(index,encoding='utf-8')

    css=(DEPLOY/'styles.css').read_text(encoding='utf-8')
    css+="""

/* FutBR legal information - readable dialogs (17 November 2026) */
.info-panel{max-height:calc(100vh - 36px);overflow-y:auto;overscroll-behavior:contain}
.info-panel #info-content{margin-top:16px}
.info-panel #info-content h3{font-family:var(--body);font-size:15px;line-height:1.4;font-weight:800;color:#f0fff2;margin:20px 0 7px;letter-spacing:0}
.info-panel #info-content p{font-size:14px;line-height:1.7;color:#cfddcf;margin:0 0 12px}
.info-panel #info-content .legal-meta{font-size:12px;color:#91cfa9;font-weight:700;margin-bottom:18px}
.info-panel #info-content a{color:#a4e9bd;text-decoration:underline;text-underline-offset:3px}
.info-panel #info-content a:hover{color:#fff}
@media(max-width:600px){.info-panel{padding:23px 18px;max-height:calc(100dvh - 28px)}.info-panel #info-content p{font-size:13px;line-height:1.65}.info-panel #info-content h3{font-size:14px}}
"""
    (DEPLOY/'styles.css').write_text(css,encoding='utf-8')

    support=(Path('site-support')/'suporte.html').read_text(encoding='utf-8')
    assert 'support_tickets' in support and 'support_messages' in support
    # Reuse official logo already present in the parent website.
    support=support.replace(
       '<span aria-hidden="true">F</span>FutBR Manager',
       '<img src="/assets/futbr-logo.png" width="36" height="36" alt="" style="width:36px;height:36px;object-fit:contain;vertical-align:middle;margin-right:10px">FutBR Manager',
       1
    )
    assert '<img src="/assets/futbr-logo.png"' in support
    (DEPLOY/'suporte.html').write_text(support,encoding='utf-8')

    files=FILES+('suporte.html',)
    package=OUT/'FutBR_Manager_SITE_Com_Suporte_Termos_Privacidade.zip'
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in files: z.write(DEPLOY/path,arcname=path)
    assert package.stat().st_size>0
    (OUT/'manifest.json').write_text(json.dumps({
      'base_url':BASE,'source_original_sha256':originals,
      'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
      'changed':['index.html','app.js','styles.css'],
      'added':['suporte.html'],
      'preserved_unchanged':['config.js','homologacao.html','homologacao.js','assets/futbr-logo.png']
    },ensure_ascii=False,indent=2),encoding='utf-8')
    print('SUCCESS: preserved 7 existing files; added support page; updated only legal modal, contact and menu.')
    print('Package',package,'bytes',package.stat().st_size)

if __name__=='__main__':
    patch_site()
