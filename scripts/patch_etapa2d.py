#!/usr/bin/env python3
"""Etapa 2d: botoes na tela do editor para ajustar o TAMANHO da tela do jogo,
simetrico em volta do centro: Altura -, Altura +, Largura -, Largura + (passo de 4 px,
segurar repete) e Fechar. Arrastar com 1 dedo (fora dos botoes) continua movendo a posicao;
o gesto de pinca da tela foi removido.
Roda DEPOIS de patch_etapa2c.py. Uso: patch_etapa2d.py <pasta_do_RetroArch>
"""
import sys

raiz = sys.argv[1]
arquivos = {}


def abrir(arq):
    if arq not in arquivos:
        with open(f"{raiz}/{arq}", encoding="utf-8") as f:
            arquivos[arq] = f.read()
    return arquivos[arq]


def trocar(arq, antigo, novo):
    s = abrir(arq)
    n = s.count(antigo)
    if n != 1:
        sys.exit(f"ERRO: em {arq} o trecho aparece {n} vezes (esperado 1):\n{antigo}")
    arquivos[arq] = s.replace(antigo, novo)


INPUT = "input/input_driver.c"

UI = r'''SALVAR_PLACEHOLDER/* ----- botoes do editor: tamanho da tela do jogo, simetrico em volta do centro ----- */
static int  mod_ui_held   = -1;
static char mod_ui_title[96];
static int mod_ui_hold_n = 0;
static int mod_ui_timer  = 0;   /* quadros restantes com o painel visivel */
static int mod_main_page = 0;   /* pagina marcada como principal (so memoria por enquanto) */

/* 10 retangulos (x, y, largura, altura) em pixels da janela:
 * 0-3 altura/largura, 4 fechar, 5-6 pagina anterior/proxima, 7 titulo (toque = marcar como principal), 8 centralizar, 9 original */
static int mod_ui_rects(int *r)
{
   int bw, bh, gap, x0, y0, k;
   if (mod_win_w <= 0 || mod_win_h <= 0)
      return 0;
   {
      int un = (mod_win_w < mod_win_h) ? mod_win_w : mod_win_h;
      bh  = un * 8 / 100;
      bw  = un * 22 / 100;
   }
   gap = bh / 5;
   x0  = mod_win_w / 2 - bw - gap / 2;
   y0  = mod_win_h / 2 - (7 * bh + 6 * gap) / 2;
   for (k = 0; k < 4; k++)
   {
      r[k * 4 + 0] = x0 + (k % 2) * (bw + gap);
      r[k * 4 + 1] = y0 + (2 + k / 2) * (bh + gap);
      r[k * 4 + 2] = bw;
      r[k * 4 + 3] = bh;
   }
   r[16] = x0;                      /* Fechar: ultima fileira, largura toda */
   r[17] = y0 + 6 * (bh + gap);
   r[18] = 2 * bw + gap;
   r[19] = bh;
   r[32] = x0;                      /* Centralizar: metade esquerda */
   r[33] = y0 + 4 * (bh + gap);
   r[34] = bw;
   r[35] = bh;
   r[36] = x0 + bw + gap;           /* Original: metade direita */
   r[37] = y0 + 4 * (bh + gap);
   r[38] = bw;
   r[39] = bh;
   r[40] = x0;                      /* Salvar novo */
   r[41] = y0 + 5 * (bh + gap);
   r[42] = bw;
   r[43] = bh;
   r[44] = x0 + bw + gap;           /* Sobrescrever */
   r[45] = y0 + 5 * (bh + gap);
   r[46] = bw;
   r[47] = bh;
   for (k = 0; k < 2; k++)
   {
      r[20 + k * 4 + 0] = x0 + k * (bw + gap);
      r[20 + k * 4 + 1] = y0 + (bh + gap);
      r[20 + k * 4 + 2] = bw;
      r[20 + k * 4 + 3] = bh;
   }
   r[28] = x0;
   r[29] = y0;
   r[30] = 2 * bw + gap;
   r[31] = bh;
   return 12;
}

/* Chamado pelo desenho dos widgets: devolve quantos botoes ha (0 = editor fechado). */
int input_overlay_editor_ui(int *r, const char **lab, int max)
{
   static const char *nomes[12] =
      { "Altura -", "Altura +", "Largura -", "Largura +", "Fechar",
        "Pag <", "Pag >", NULL, "Centralizar", "Original",
        "Salvar novo", "Sobrescrever" };
   int k, n;
   if (!mod_editor_active || mod_editor_wait_close || mod_ui_timer <= 0 || max < 12)
      return 0;
   n = mod_ui_rects(r);
   for (k = 0; k < n; k++)
      lab[k] = nomes[k];
   {
      input_overlay_t *ol = input_driver_st.overlay_ptr;
      if (ol && ol->active)
         snprintf(mod_ui_title, sizeof(mod_ui_title), "%s%s (%u de %u)",
               ((unsigned)ol->index == (unsigned)mod_main_page) ? "* " : "",
               ol->active->name, (unsigned)ol->index + 1, (unsigned)ol->size);
      else
         snprintf(mod_ui_title, sizeof(mod_ui_title), "?");
      lab[7] = mod_ui_title;
   }
   return n;
}

static int mod_ui_hit(float px, float py)
{
   int r[48];
   int k, n;
   if (mod_ui_timer <= 0)
      return -1;
   n = mod_ui_rects(r);
   for (k = 0; k < n; k++)
      if (   px >= (float)r[k * 4 + 0] && px < (float)(r[k * 4 + 0] + r[k * 4 + 2])
          && py >= (float)r[k * 4 + 1] && py < (float)(r[k * 4 + 1] + r[k * 4 + 3]))
         return k;
   return -1;
}

/* Vai para a pagina anterior/proxima (pula as de nome "hidden..."). */
static void mod_page_goto(int dir)
{
   input_overlay_t *ol = input_driver_st.overlay_ptr;
   size_t   tries;
   unsigned idx;
   bool     tmp = false;
   if (!ol || ol->size < 2)
      return;
   idx = (unsigned)ol->index;
   for (tries = 0; tries < ol->size; tries++)
   {
      idx = (unsigned)((idx + (dir > 0 ? 1 : ol->size - 1)) % ol->size);
      if (strncmp(ol->overlays[idx].name, "hidden", 6) != 0)
         break;
   }
   if (idx == (unsigned)ol->index
         || strncmp(ol->overlays[idx].name, "hidden", 6) == 0)
      return;
   ol->next_index   = idx;
   command_event(CMD_EVENT_OVERLAY_NEXT, &tmp);
   mod_editor_sel   = -1;
   mod_grp_n        = 0;
}

static void mod_ui_press(int b)
{
   int x, y, w, h;
   if (b == 4)
   {
      static const char msg[] = "Editor de overlay encerrado.";
      mod_editor_active = false;
      mod_editor_sel    = -1;
      mod_editor_pinch  = false;
      command_event(CMD_EVENT_UNPAUSE, NULL);
      runloop_msg_queue_push(msg, sizeof(msg) - 1, 1, 120, true, NULL,
            MESSAGE_QUEUE_ICON_DEFAULT, MESSAGE_QUEUE_CATEGORY_INFO);
      return;
   }
   if (b == 7)
   {
      input_overlay_t *ol = input_driver_st.overlay_ptr;
      if (ol)
         mod_main_page = (int)ol->index;
      return;
   }
   if (b == 5 || b == 6)
   {
      mod_page_goto(b == 6 ? 1 : -1);
      return;
   }
   if (b == 10 || b == 11)
   {
      mod_save_cfg(b == 11);
      return;
   }
   mod_vp_get(&x, &y, &w, &h);
   switch (b)
   {
      /* x,y sao deslocamento da ancora (centro): ao mudar w/h a imagem ja cresce
       * para os dois lados sozinha, entao x,y NAO mudam. */
      case 0: h -= 4; break;
      case 1: h += 4; break;
      case 2: w -= 4; break;
      case 3: w += 4; break;
      case 8: x = 0; y = 0; break;
      case 9:
      {
         /* proporcao original do jogo (a do nucleo), a maior que cabe na tela, centralizada */
         video_driver_state_t *vs = video_state_get_ptr();
         float asp = vs->av_info.geometry.aspect_ratio;
         if (asp <= 0.0f && vs->av_info.geometry.base_height)
            asp = (float)vs->av_info.geometry.base_width
                / (float)vs->av_info.geometry.base_height;
         if (asp <= 0.0f || mod_win_w <= 0 || mod_win_h <= 0)
            return;
         w = mod_win_w;
         h = (int)((float)w / asp);
         if (h > mod_win_h)
         {
            h = mod_win_h;
            w = (int)((float)h * asp);
         }
         x = 0;
         y = 0;
         break;
      }
      default: return;
   }
   mod_vp_set(x, y, w, h);
}

'''

import os
UI = UI.replace('SALVAR_PLACEHOLDER', open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salvar_cfg.c.txt'), encoding='utf-8').read())

# 0) 3 dedos tambem despausa; tamanho da janela atualizado a cada leitura (vertical/horizontal)
trocar(
    INPUT,
    "      mod_editor_pinch  = false;\n      runloop_msg_queue_push(msg, sizeof(msg) - 1, 1, 120, true, NULL,",
    "      mod_editor_pinch  = false;\n      command_event(CMD_EVENT_UNPAUSE, NULL);\n      runloop_msg_queue_push(msg, sizeof(msg) - 1, 1, 120, true, NULL,",
)
trocar(
    INPUT,
    "      mod_raw_y[kk] = (float)VIDEO_POS_Y(st->touch[kk]);\n   }\n",
    "      mod_raw_y[kk] = (float)VIDEO_POS_Y(st->touch[kk]);\n   }\n"
    "   {\n"
    "      struct video_viewport vp2;\n"
    "      memset(&vp2, 0, sizeof(vp2));\n"
    "      if (video_driver_get_viewport_info(&vp2))\n"
    "      {\n"
    "         mod_win_w = (int)VIDEO_SCALE_W(vp2.full_dims);\n"
    "         mod_win_h = (int)VIDEO_SCALE_H(vp2.full_dims);\n"
    "      }\n"
    "   }\n",
)

trocar(
    INPUT,
    "   {\n      struct video_viewport vp2;\n",
    "   if (count > 0)\n      mod_ui_timer = 300;\n   else if (mod_ui_timer > 0)\n      mod_ui_timer--;\n   {\n      struct video_viewport vp2;\n",
)

trocar(
    INPUT,
    "         mod_editor_seed_screen();\n",
    "         mod_editor_seed_screen();\n         mod_ui_timer = 300;\n         mod_snap_take(input_driver_st.overlay_ptr);\n",
)

# 1) funcoes dos botoes, antes de mod_editor_frame (depois do bloco da tela)
trocar(
    INPUT,
    "/* Uma vez por leitura de toques; count = dedos na tela. */\n",
    UI + "/* Uma vez por leitura de toques; count = dedos na tela. */\n",
)

# 2) soltou os dedos: libera o botao segurado
trocar(
    INPUT,
    "      mod_editor_screen = false;\n      mod_grp_n         = 0;\n",
    "      mod_editor_screen = false;\n      mod_ui_held       = -1;\n      mod_grp_n         = 0;\n",
)

# 3) toque do dedo 0: primeiro ve se pegou um botao do editor
trocar(
    INPUT,
    "   if (idx == 0)\n   {\n      mod_editor_x0 = x;\n      mod_editor_y0 = y;\n",
    "   if (idx == 0)\n   {\n      mod_editor_x0 = x;\n      mod_editor_y0 = y;\n"
    "\n"
    "      if (mod_editor_sel < 0 && !mod_editor_screen)\n"
    "      {\n"
    "         float upx, upy;\n"
    "         int   ub;\n"
    "         mod_scr_finger(0, &upx, &upy);\n"
    "         ub = mod_ui_hit(upx, upy);\n"
    "         if (ub >= 0 && (mod_ui_held < 0 || mod_ui_held == ub))\n"
    "         {\n"
    "            if (mod_ui_held != ub)\n"
    "            {\n"
    "               mod_ui_held   = ub;\n"
    "               mod_ui_hold_n = 0;\n"
    "               mod_ui_press(ub);\n"
    "            }\n"
    "            else\n"
    "            {\n"
    "               mod_ui_hold_n++;\n"
    "               if ((ub < 4) && mod_ui_hold_n > 24 && (mod_ui_hold_n % 4) == 0)\n"
    "                  mod_ui_press(ub);\n"
    "            }\n"
    "            return;\n"
    "         }\n"
    "         if (mod_ui_held >= 0)\n"
    "            return;\n"
    "      }\n",
)

# 4) sem pinca para a tela (o tamanho e pelos botoes)
trocar(
    INPUT,
    "   else if (idx == 1 && mod_editor_screen)\n   {\n      mod_screen_pinch(!mod_editor_pinch);\n      mod_editor_pinch = true;\n   }\n",
    "   else if (idx == 1 && mod_editor_screen)\n   {\n      /* tamanho da tela: pelos botoes do editor */\n   }\n",
)

# 5) novo aviso
trocar(
    INPUT,
    '"Editor: toque num botao ou na tela do jogo. 1 dedo move, 2 dedos mudam o tamanho. 3 dedos ou Voltar saem.";',
    '"Editor: arraste botoes ou a tela do jogo. Botoes no centro mudam o tamanho. Voltar sai.";',
)

# ---------------------------------------------------------------- desenho nos widgets
WID = "gfx/gfx_widgets.c"
DESENHO = r'''   /* MOD: botoes do editor de overlay (tamanho da tela do jogo) */
   {
      extern int input_overlay_editor_ui(int *r, const char **lab, int max);
      int         ur[12 * 4];
      const char *ulab[12];
      int         un = input_overlay_editor_ui(ur, ulab, 12);
      if (un > 0)
      {
         int      ui;
         int      out_w = (int)VIDEO_SCALE_W(output_dims);
         int      out_h = (int)VIDEO_SCALE_H(output_dims);
         int      lay_w = (int)VIDEO_SCALE_W(video_info->dims);
         int      lay_h = (int)VIDEO_SCALE_H(video_info->dims);
         float    fill[16] = {
            0.05f, 0.05f, 0.10f, 0.78f,
            0.05f, 0.05f, 0.10f, 0.78f,
            0.05f, 0.05f, 0.10f, 0.78f,
            0.05f, 0.05f, 0.10f, 0.78f,
         };
         if (out_w > 0 && out_h > 0)
         {
            gfx_display_blend_begin(dispctx, userdata);
            for (ui = 0; ui < un; ui++)
            {
               int bx = ur[ui * 4 + 0] * lay_w / out_w;
               int by = ur[ui * 4 + 1] * lay_h / out_h;
               int bw = ur[ui * 4 + 2] * lay_w / out_w;
               int bh = ur[ui * 4 + 3] * lay_h / out_h;
               gfx_display_draw_quad(
                     p_disp, userdata, video_info->dims,
                     bx, by, VIDEO_SCALE_PACK(bw, bh),
                     video_info->dims, fill, NULL);
            }
            gfx_display_blend_end(dispctx, userdata);
            for (ui = 0; ui < un; ui++)
            {
               int bx = ur[ui * 4 + 0] * lay_w / out_w;
               int by = ur[ui * 4 + 1] * lay_h / out_h;
               int bw = ur[ui * 4 + 2] * lay_w / out_w;
               int bh = ur[ui * 4 + 3] * lay_h / out_h;
               gfx_display_draw_text(
                     p_dispwidget->gfx_widget_fonts.regular.font,
                     ulab[ui],
                     (float)(bx + bw / 2), (float)(by + bh * 65 / 100),
                     video_info->dims,
                     0xFFFFFFFF, TEXT_ALIGN_CENTER,
                     1.0f, false, 0.0f, false);
               p_dispwidget->gfx_widget_fonts.regular.usage_count++;
            }
            gfx_widgets_flush_text(video_info->dims,
                  &p_dispwidget->gfx_widget_fonts.regular);
         }
      }
   }

'''
trocar(
    WID,
    "#ifdef HAVE_TRANSLATE\n   /* AI Service overlay */\n",
    DESENHO + "#ifdef HAVE_TRANSLATE\n   /* AI Service overlay */\n",
)

for arq, conteudo in arquivos.items():
    with open(f"{raiz}/{arq}", "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("ok:", arq)
