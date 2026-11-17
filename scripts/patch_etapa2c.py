#!/usr/bin/env python3
"""Etapa 2c: no editor de overlay, tocar na tela do jogo (fora dos botoes) move/redimensiona
a imagem do jogo, editando a "Proporcao de tela personalizada" (x, y, largura, altura).
Ao entrar, liga o modo Personalizado partindo da posicao atual (a imagem nao da salto).
Nada e salvo. Roda DEPOIS de patch_etapa2.py. Uso: patch_etapa2c.py <pasta_do_RetroArch>
"""
import sys

raiz = sys.argv[1]
caminho = f"{raiz}/input/input_driver.c"
s = open(caminho, encoding="utf-8").read()


def trocar(antigo, novo):
    global s
    n = s.count(antigo)
    if n != 1:
        sys.exit(f"ERRO: trecho aparece {n} vezes (esperado 1):\n{antigo}")
    s = s.replace(antigo, novo)


TELA = r'''/* ----- tela do jogo = proporcao personalizada (x, y, largura, altura) ----- */
#define MOD_VP_Y_SINAL 1   /* se arrastar para cima mover a imagem para baixo, trocar para -1 */
static bool  mod_editor_screen = false;
static float mod_raw_x[2];
static float mod_raw_y[2];
static int   mod_win_w = 0;
static int   mod_win_h = 0;
static float mod_scr_px0 = 0.0f;
static float mod_scr_py0 = 0.0f;
static int   mod_scr_x0 = 0, mod_scr_y0 = 0, mod_scr_w0 = 1, mod_scr_h0 = 1;
static float mod_scr_d0 = 1.0f;

static void mod_vp_get(int *x, int *y, int *w, int *h)
{
   settings_t *st = config_get_ptr();
   *x = VIDEO_POS_X(st->video_vp_custom.pos);
   *y = VIDEO_POS_Y(st->video_vp_custom.pos);
   *w = (int)VIDEO_SCALE_W(st->video_vp_custom.dims);
   *h = (int)VIDEO_SCALE_H(st->video_vp_custom.dims);
}

static void mod_vp_set(int x, int y, int w, int h)
{
   settings_t *st = config_get_ptr();
   if (w < 16)    w = 16;
   if (h < 16)    h = 16;
   if (w > 9999)  w = 9999;
   if (h > 9999)  h = 9999;
   if (x < -9999) x = -9999;
   if (x > 9999)  x = 9999;
   if (y < -9999) y = -9999;
   if (y > 9999)  y = 9999;
   st->video_vp_custom.pos  = VIDEO_POS_PACK(x, y);
   st->video_vp_custom.dims = VIDEO_SCALE_PACK(w, h);
   command_event(CMD_EVENT_VIDEO_APPLY_STATE_CHANGES, NULL);
}

/* Liga o modo Personalizado partindo da posicao atual da imagem. */
static void mod_editor_seed_screen(void)
{
   settings_t *st = config_get_ptr();
   struct video_viewport vp;
   memset(&vp, 0, sizeof(vp));
   if (video_driver_get_viewport_info(&vp))
   {
      mod_win_w = (int)VIDEO_SCALE_W(vp.full_dims);
      mod_win_h = (int)VIDEO_SCALE_H(vp.full_dims);
      if (   st->uints.video_aspect_ratio_idx != ASPECT_RATIO_CUSTOM
          || !VIDEO_SCALE_W(st->video_vp_custom.dims)
          || !VIDEO_SCALE_H(st->video_vp_custom.dims))
      {
         st->video_vp_custom.pos  = vp.pos;
         st->video_vp_custom.dims = vp.dims;
      }
   }
   if (st->uints.video_aspect_ratio_idx != ASPECT_RATIO_CUSTOM)
   {
      st->uints.video_aspect_ratio_idx = ASPECT_RATIO_CUSTOM;
      command_event(CMD_EVENT_VIDEO_SET_ASPECT_RATIO, NULL);
   }
   command_event(CMD_EVENT_VIDEO_APPLY_STATE_CHANGES, NULL);
}

/* Dedo 0 em pixels da janela. */
static void mod_scr_finger(int k, float *px, float *py)
{
   *px = ((mod_raw_x[k] + 32767.0f) / 65535.0f) * (float)mod_win_w;
   *py = ((mod_raw_y[k] + 32767.0f) / 65535.0f) * (float)mod_win_h;
}

static void mod_screen_begin(void)
{
   if (mod_win_w <= 0 || mod_win_h <= 0)
      return;
   mod_scr_finger(0, &mod_scr_px0, &mod_scr_py0);
   mod_vp_get(&mod_scr_x0, &mod_scr_y0, &mod_scr_w0, &mod_scr_h0);
   if (mod_scr_w0 < 1) mod_scr_w0 = 1;
   if (mod_scr_h0 < 1) mod_scr_h0 = 1;
   mod_editor_screen = true;
}

static void mod_screen_move(void)
{
   float px, py;
   mod_scr_finger(0, &px, &py);
   mod_vp_set(mod_scr_x0 + (int)(px - mod_scr_px0),
              mod_scr_y0 + MOD_VP_Y_SINAL * (int)(py - mod_scr_py0),
              mod_scr_w0, mod_scr_h0);
}

/* 2 dedos: muda o tamanho mantendo a proporcao, em volta do centro da imagem. */
static void mod_screen_pinch(bool primeira)
{
   float ax, ay, bx, by, dx, dy, dist, f;
   int w, h, cx, cy;
   mod_scr_finger(0, &ax, &ay);
   mod_scr_finger(1, &bx, &by);
   dx   = bx - ax;
   dy   = by - ay;
   dist = sqrtf(dx * dx + dy * dy);
   if (primeira)
   {
      mod_scr_d0 = (dist > 20.0f) ? dist : 20.0f;
      mod_vp_get(&mod_scr_x0, &mod_scr_y0, &mod_scr_w0, &mod_scr_h0);
      if (mod_scr_w0 < 1) mod_scr_w0 = 1;
      if (mod_scr_h0 < 1) mod_scr_h0 = 1;
      return;
   }
   f = dist / mod_scr_d0;
   if (f < 0.2f) f = 0.2f;
   if (f > 5.0f) f = 5.0f;
   w  = (int)((float)mod_scr_w0 * f);
   h  = (int)((float)mod_scr_h0 * f);
   cx = mod_scr_x0 + mod_scr_w0 / 2;
   cy = mod_scr_y0 + mod_scr_h0 / 2;
   mod_vp_set(cx - w / 2, cy - h / 2, w, h);
}

'''

# 1) funcoes da tela, antes de mod_editor_frame
trocar(
    "/* Uma vez por leitura de toques; count = dedos na tela. */\n",
    TELA + "/* Uma vez por leitura de toques; count = dedos na tela. */\n",
)

# 2) mod_editor_frame recebe o estado dos toques (para guardar a posicao bruta dos dedos)
trocar(
    "static void mod_editor_frame(input_overlay_t *ol, int count)\n{\n",
    "static void mod_editor_frame(input_overlay_t *ol, int count,\n"
    "      const input_overlay_state_t *st)\n{\n"
    "   int kk;\n",
)
trocar(
    "         mod_editor_frame(ol, (int)i);\n",
    "         mod_editor_frame(ol, (int)i, ol_state);\n",
)

trocar(
    "   bool menu_alive = (menu_state_get_ptr()->flags & MENU_ST_FLAG_ALIVE) != 0;\n",
    "   bool menu_alive = (menu_state_get_ptr()->flags & MENU_ST_FLAG_ALIVE) != 0;\n"
    "\n"
    "   for (kk = 0; kk < 2 && kk < count; kk++)\n"
    "   {\n"
    "      mod_raw_x[kk] = (float)VIDEO_POS_X(st->touch[kk]);\n"
    "      mod_raw_y[kk] = (float)VIDEO_POS_Y(st->touch[kk]);\n"
    "   }\n",
)

# 3) ao ver o menu fechado pela primeira vez: liga Personalizado partindo da posicao atual
trocar(
    "      if (!menu_alive)\n         mod_editor_wait_close = false;\n",
    "      if (!menu_alive)\n"
    "      {\n"
    "         mod_editor_wait_close = false;\n"
    "         mod_editor_seed_screen();\n"
    "      }\n",
)

# 4) soltou os dedos: encerra tela tambem
trocar(
    "      mod_editor_sel   = -1;\n      mod_editor_pinch = false;\n      mod_grp_n        = 0;\n",
    "      mod_editor_sel    = -1;\n      mod_editor_pinch  = false;\n      mod_editor_screen = false;\n      mod_grp_n         = 0;\n",
)

# 5) toque que nao pegou botao -> comeca a arrastar a tela
trocar(
    "      if (mod_editor_sel < 0)\n      {\n         size_t i;\n         float  best = 1e9f;\n",
    "      if (mod_editor_sel < 0 && !mod_editor_screen)\n      {\n         size_t i;\n         float  best = 1e9f;\n",
)
trocar(
    "         if (mod_editor_sel >= 0)\n            mod_build_group(ol->active, mod_editor_sel);\n      }\n",
    "         if (mod_editor_sel >= 0)\n            mod_build_group(ol->active, mod_editor_sel);\n"
    "         else\n            mod_screen_begin();\n      }\n"
    "      else if (mod_editor_screen)\n      {\n"
    "         if (mod_editor_fingers < 2)\n            mod_screen_move();\n      }\n",
)

# 6) segundo dedo na tela -> redimensiona a tela
trocar(
    "   else if (idx == 1 && mod_editor_sel >= 0)\n   {\n",
    "   else if (idx == 1 && mod_editor_screen)\n"
    "   {\n"
    "      mod_screen_pinch(!mod_editor_pinch);\n"
    "      mod_editor_pinch = true;\n"
    "   }\n"
    "   else if (idx == 1 && mod_editor_sel >= 0)\n   {\n",
)

# 7) entrada: limpa o estado da tela e novo aviso
trocar(
    "   mod_editor_sel        = -1;\n   mod_editor_pinch      = false;\n   command_event(CMD_EVENT_RESUME, NULL);",
    "   mod_editor_sel        = -1;\n   mod_editor_pinch      = false;\n   mod_editor_screen     = false;\n   command_event(CMD_EVENT_RESUME, NULL);",
)
trocar(
    '"Editor: 1 dedo move, 2 dedos mudam o tamanho, 3 dedos ou Voltar saem.";',
    '"Editor: toque num botao ou na tela do jogo. 1 dedo move, 2 dedos mudam o tamanho. 3 dedos ou Voltar saem.";',
)

open(caminho, "w", encoding="utf-8").write(s)
print("ok: input/input_driver.c (etapa 2c)")
