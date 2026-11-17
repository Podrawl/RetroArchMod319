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

UI = r'''/* ----- botoes do editor: tamanho da tela do jogo, simetrico em volta do centro ----- */
static int mod_ui_held   = -1;
static int mod_ui_hold_n = 0;

/* 5 retangulos (x, y, largura, altura) em pixels da janela */
static int mod_ui_rects(int *r)
{
   int bw, bh, gap, x0, y0, k;
   if (mod_win_w <= 0 || mod_win_h <= 0)
      return 0;
   bh  = mod_win_h * 12 / 100;
   bw  = mod_win_h * 30 / 100;
   gap = bh / 5;
   x0  = mod_win_w / 2 - bw - gap / 2;
   y0  = mod_win_h / 2 - (3 * bh + 2 * gap) / 2;
   for (k = 0; k < 4; k++)
   {
      r[k * 4 + 0] = x0 + (k % 2) * (bw + gap);
      r[k * 4 + 1] = y0 + (k / 2) * (bh + gap);
      r[k * 4 + 2] = bw;
      r[k * 4 + 3] = bh;
   }
   r[16] = x0;
   r[17] = y0 + 2 * (bh + gap);
   r[18] = 2 * bw + gap;
   r[19] = bh;
   return 5;
}

/* Chamado pelo desenho dos widgets: devolve quantos botoes ha (0 = editor fechado). */
int input_overlay_editor_ui(int *r, const char **lab, int max)
{
   static const char *nomes[5] =
      { "Altura -", "Altura +", "Largura -", "Largura +", "Fechar" };
   int k, n;
   if (!mod_editor_active || mod_editor_wait_close || max < 5)
      return 0;
   n = mod_ui_rects(r);
   for (k = 0; k < n; k++)
      lab[k] = nomes[k];
   return n;
}

static int mod_ui_hit(float px, float py)
{
   int r[20];
   int k, n = mod_ui_rects(r);
   for (k = 0; k < n; k++)
      if (   px >= (float)r[k * 4 + 0] && px < (float)(r[k * 4 + 0] + r[k * 4 + 2])
          && py >= (float)r[k * 4 + 1] && py < (float)(r[k * 4 + 1] + r[k * 4 + 3]))
         return k;
   return -1;
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
      runloop_msg_queue_push(msg, sizeof(msg) - 1, 1, 120, true, NULL,
            MESSAGE_QUEUE_ICON_DEFAULT, MESSAGE_QUEUE_CATEGORY_INFO);
      return;
   }
   mod_vp_get(&x, &y, &w, &h);
   switch (b)
   {
      case 0: h -= 4; y += 2; break;
      case 1: h += 4; y -= 2; break;
      case 2: w -= 4; x += 2; break;
      case 3: w += 4; x -= 2; break;
      default: return;
   }
   mod_vp_set(x, y, w, h);
}

'''

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
    "               if (mod_ui_hold_n > 24 && (mod_ui_hold_n % 4) == 0)\n"
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
      int         ur[5 * 4];
      const char *ulab[5];
      int         un = input_overlay_editor_ui(ur, ulab, 5);
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
