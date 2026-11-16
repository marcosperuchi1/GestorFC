# FutBR Manager 18.341 — reparo do atualizador assinado no Windows

## Diagnóstico

O aplicativo 18.339 encontra a atualização 18.340 mas se recusa a instalá-la com o erro Tauri/Minisign:

`The signature was created with a different key than the one provided`.

O diagnóstico no GitHub Actions confirmou que as assinaturas publicadas das versões 18.339 e 18.340 têm o mesmo identificador de chave entre si, mas não correspondem à variável de chave pública `FUTBR_UPDATER_PUBLIC_KEY`. O download via R2 e o manifesto `latest.json` estavam íntegros; o bloqueio criptográfico do Tauri atuou corretamente. O simples fato de existir um `.sig` e de seu SHA-256 bater **não é prova de que a assinatura valida contra a chave embutida no aplicativo**.

## Solução para 18.341

- O workflow `.github/workflows/build-desktop-updater-18341.yml` deriva a chave pública **da chave privada efetivamente usada pelo próprio processo de assinatura**, no runner, sem publicar o segredo.
- A configuração Tauri usa a chave derivada antes do build. A versão passa para `18.341.0`, sem mudar o identificador do aplicativo nem os caminhos de saves.
- O verificador `verify_desktop_updater_signature_18341.py` compara o identificador de chave de assinatura com o do Tauri embutido, valida os arquivos e preserva os testes de nacionalidade de Roberto Firmino (BRA), Matt Badiee (USA), pesquisa de artilheiros e integridade dos saves.
- A verificação `minisign::verify` no helper Rust valida criptograficamente o instalador inteiro antes de permitir a publicação do `latest.json` no R2.
- A chave privada **nunca** deve ser registrada no código, em logs ou em artefatos publicados.

## Instalação de reparo (uma única vez)

Como as versões 18.339 e 18.340 foram distribuídas com chave pública incompatível, não podem receber um update automático assinado com a chave corrigida. Os jogadores afetados precisam baixar o instalador verificado `FutBR-Manager-18.341-Windows.exe`, fechar o jogo e instalá-lo **por cima** da versão antiga, sem apagar dados do aplicativo. Recomenda-se um backup dos saves.

A partir da 18.341, o atualizador Tauri estará configurado para conferir pacotes futuros com a mesma chave de assinatura. Para confirmar a retomada automática, é necessário lançar uma nova versão superior à 18.341 e testar em uma instalação real.

## Política de assinatura futura

**Não gere nem substitua a chave privada** usada na 18.341. A variável antiga `FUTBR_UPDATER_PUBLIC_KEY` não deve voltar a ser usada sem comprovação criptográfica de que corresponde à chave privada. Os workflows de próximas versões devem manter a derivação/validação introduzida nesta versão ou usar a chave pública verificada e imutável correspondente.

Não publique versões antigas sobre o manifesto de atualização mais recente. O manifesto deve ser enviado ao R2 somente depois do instalador verificado e da assinatura.
