# Desenho do editor de overlay (RASCUNHO, nada implementado)

Base: RetroArch master (commit lido em 01-ANALISE/overlay-viewport*/00-commit.txt).

## Comportamento
- Entrada de menu: Configurações > menu de overlay existente do RetroArch ("On-Screen Overlay" em inglês; nome exato em PT a confirmar no app) > "Editar layout do overlay". (Correção: "Tela e Overlay" era nome inventado.)
- Pausa o jogo, mostra overlay ativo + caixa da tela do jogo. Arrastar botões, arrastar/redimensionar a caixa da tela. Salvar / Cancelar.
- Ao salvar, pergunta: "Só este jogo" ou "Todos os jogos deste sistema (núcleo)".
- Salva COPIA ao lado do .cfg original (ex.: psx.cfg -> psx-meu.cfg), mantendo caminhos das imagens. Original nunca é alterado.
- "Global de verdade" (todos os consoles) NAO é oferecido: aplicaria layout de PS1 no GBA.

## Confirmado no código (01-ANALISE)
- Escolha do overlay: settings->paths.path_overlay (`input_overlay`), com preset manual; auto-escolha em gamepads/Named_Overlays só se opção ligada e sem preset.
- Overrides (núcleo/jogo) existem: config_load_override / config_save_overrides em configuration.c.
- Página de overlay tem viewport próprio (struct overlay.viewport, flag OVERLAY_HAS_VIEWPORT, chave `overlayN_viewport` em tasks/task_overlay.c). Vídeo lê isso em video_driver.c (set_overlay_viewport).
- Funções de escala/recalculo: input_overlay_scale, input_overlay_set_scale_factor, input_overlay_update_desc_geom (input/input_driver.c).

## Hipóteses (verificar antes de codar)
- Nome/forma exata do modo "fill" do viewport no .cfg.
- Como interceptar o toque no android_input.c sem acionar botões do jogo.
- Como adicionar entrada nova nos menus Ozone / MaterialUI / XMB / RGUI.
- Comportamento de salvar override por núcleo vs por jogo para `input_overlay`.

## Etapas propostas (cada uma gera APK de teste)
0. Build de teste com nome de pacote próprio (instala ao lado do seu RetroArch).
1. Entrada de menu + tela de edição que só mostra caixas (sem salvar).
2. Arrastar/redimensionar botões e viewport (só na memória).
3. Salvar cópia .cfg + escolha jogo/núcleo.
4. Acabamento (grade, desfazer, várias páginas, retrato/paisagem).

## Ajustes pedidos pelo usuário (16/11)
- Editar SÓ mover/redimensionar botões e posicionar a tela. Função de cada botão NÃO é editada: já vem no .cfg (nome do bind em cada overlayN_descM).
- Várias páginas por .cfg (ex.: horizontal e vertical): o editor edita a página ativa e deixa trocar de página; viewport é por página.
- Opção de renomear a cópia ao salvar (ex.: psx-meu.cfg -> nome escolhido).
- RISCO a verificar: se a imagem do overlay for UMA imagem de tela cheia com os botões desenhados, mover o hitbox não move o desenho. Só funciona bem com imagem por botão (overlayN_descM_overlay). Checar nos .cfg da pasta flat.

## Extras pedidos (16/11) - FORA do editor, depois dele
- overlay_next (RARCH_OVERLAY_NEXT) é a ÚNICA função de troca de página encontrada (input_defines.h, task_overlay.c). Existe também troca automática retrato/paisagem pelo nome da página.
- Ocultar já existente: só "ocultar no menu" e "ocultar com controle físico conectado". Não achei ocultar por inatividade/toque (busca não exaustiva).
- Ideias: (A) opção "ocultar botões após X s sem toque" (volta ao tocar); (B) nova função de botão "ocultar/mostrar overlay" sem trocar de página.
- Analógico: input_overlay_get_analog_state (input_driver.c ~6004): mapeamento linear distância/(range*saturate), sem zona morta nem curva; opção existente input_overlay_analog_recenter_zone; saturação por botão (analog_saturate_pct). Causa real do "ruim" NÃO confirmada: precisa sintoma + núcleo.
- Hipótese a checar: nomes de hotkey (save_state/load_state) direto em botões de overlay.
