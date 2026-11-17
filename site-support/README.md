# FutBR Manager: Central de Suporte / Feedback

## Funcionalidade criada
O backend está no Supabase do jogo, projeto ticwckvvxswturovwlqu, com
a migração futbr_support_center_20261117.

As tabelas public.support_tickets, public.support_messages e public.support_staff
foram criadas com RLS: o jogador acessa somente seus chamados e a equipe
autorizada pode ler todos, responder e mudar status e prioridade.

Administradores: marcosperuchi@live.com e marcosperuchi1@gmail.com.
A autenticação usa o mesmo Supabase Auth do jogo e a página usa somente a chave
pública, sem chave service-role ou dados financeiros. Existe proteção contra
chamados sucessivos do mesmo usuário em menos de 60 segundos.

## Publicar no Cloudflare Pages atual (sem sobrescrever o site)
O site futbrmanager.com.br está no projeto Cloudflare Pages
futbrmanager-site, publicado via Direct Upload, não via GitHub.

1. Recupere o pacote completo do site atualmente em produção, com index.html,
   imagens, JavaScript e configuração original do Supabase/Mercado Pago.
2. Copie site-support/suporte.html para a mesma raiz do index.html.
3. Acrescente no menu principal do index.html a âncora abaixo:

   <a href="/suporte.html">Suporte</a>

4. Compacte novamente o SITE INTEIRO, deixando index.html na raiz do ZIP.
5. No Cloudflare: Workers & Pages > futbrmanager-site > Deployments >
   Create deployment > Production > enviar o ZIP completo.
6. Verifique https://futbrmanager.com.br/suporte.html com uma conta comum
   e depois com uma conta de administrador.

ATENÇÃO: NÃO envie somente suporte.html como novo deployment de Direct Upload.
Isto poderia remover os demais arquivos do site atual.

## Estados
open = Aberto
in_progress = Em análise
waiting_user = Aguardando jogador
resolved = Resolvido
closed = Encerrado

## Limites da primeira versão
O chamado suporta mensagens de texto, mas ainda não aceita anexos ou imagens.
O jogador acompanha o status abrindo a página; notificações automáticas por
e-mail não estão implementadas nesta versão.

## Testes
O workflow GitHub Actions "Test FutBR website support" valida o fluxo visual
em 3 resoluções, cadastro de chamado, resposta e status administrativo, usando
um Supabase simulado. A base real foi verificada com transações RLS revertidas,
sem criar tickets fictícios.
