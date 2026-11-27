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

UI = r'''SALVAR_PLACEHOLDERBOTOES_PLACEHOLDER/* ----- botoes do editor: tamanho da tela do jogo, simetrico em volta do centro ----- */
static int  mod_ui_held   = -1;
static bool mod_ui_held_g = false;
static char mod_ui_title[96];
static int mod_ui_hold_n = 0;
static int mod_ui_timer  = 0;   /* quadros restantes com o painel visivel */
static int mod_main_page = 0;   /* pagina marcada como principal (so memoria por enquanto) */

/* 18 retangulos (x, y, largura, altura) em pixels; w=0 = escondido.
 * 0-3 altura/largura, 4 fechar, 5-6 pagina anterior/proxima, 7 titulo (toque = marcar como principal),
 * 8 centralizar, 9 original, 10 salvar novo, 11 sobrescrever, 12 ir para aba Botoes, 13 voltar para aba Tela,
 * 14-15 candidato anterior/proximo, 16 candidato (toque = adicionar), 17 remover botao */
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
   for (k = 0; k < 72; k++)
      r[k] = 0;
#define MOD_R(i, row, col, span) do { \
   r[(i) * 4 + 0] = x0 + (col) * (bw + gap); \
   r[(i) * 4 + 1] = y0 + (row) * (bh + gap); \
   r[(i) * 4 + 2] = (span) * bw + ((span) - 1) * gap; \
   r[(i) * 4 + 3] = bh; } while (0)
   if (mod_grid_open)
   {
      /* caixa: 0 fundo, 1 titulo, 2 area da lista (rolagem), 13 fechar */
      int bxw = (mod_win_w >= mod_win_h) ? mod_win_w * 62 / 100 : mod_win_w * 92 / 100;
      int bxh = (mod_win_w >= mod_win_h) ? mod_win_h * 90 / 100 : mod_win_h * 62 / 100;
      int pad = gap * 2;
      int rh  = (bxh - 2 * pad - 7 * gap) / 8;
      int bx0 = mod_win_w / 2 - bxw / 2;
      int by0 = mod_win_h / 2 - bxh / 2;
      r[0] = bx0;
      r[1] = by0;
      r[2] = bxw;
      r[3] = bxh;
      r[4] = bx0 + pad;
      r[5] = by0 + pad;
      r[6] = bxw - 2 * pad;
      r[7] = rh;
      r[8]  = bx0 + pad;
      r[9]  = by0 + pad + (rh + gap);
      r[10] = bxw - 2 * pad;
      r[11] = 6 * rh + 5 * gap;
      r[13 * 4 + 0] = bx0 + pad;
      r[13 * 4 + 1] = by0 + pad + 7 * (rh + gap);
      r[13 * 4 + 2] = bxw - 2 * pad;
      r[13 * 4 + 3] = rh;
      mod_grid_rh    = rh;
      mod_grid_pitch = rh + gap;
      return 18;
   }
   MOD_R(7, 0, 0, 2);
   MOD_R(5, 1, 0, 1);
   MOD_R(6, 1, 1, 1);
   MOD_R(10, 5, 0, 1);
   MOD_R(11, 5, 1, 1);
   MOD_R(0, 2, 0, 1);
   MOD_R(1, 2, 1, 1);
   MOD_R(2, 3, 0, 1);
   MOD_R(3, 3, 1, 1);
   MOD_R(8, 4, 0, 1);
   MOD_R(9, 4, 1, 1);
   MOD_R(12, 6, 0, 1);
   MOD_R(4, 6, 1, 1);
#undef MOD_R
   return 18;
}

/* Chamado pelo desenho dos widgets: devolve quantos botoes ha (0 = editor fechado). */
int input_overlay_editor_ui(int *r, const char **lab, int max)
{
   static const char *nomes[18] =
      { "Altura -", "Altura +", "Largura -", "Largura +", "Fechar",
        "Pag <", "Pag >", NULL, "Centralizar", "Original",
        "Salvar novo", "Sobrescrever", "Botoes", NULL,
        NULL, NULL, NULL, NULL };
   int k, n;
   mod_grid_step();
   if (!mod_editor_active)
   {
      mod_grid_open = false;
      mod_grid_down = false;
   }
   mod_temp_tick();
   if (mod_reload_wait > 0 || mod_apply_left > 0)
      mod_reload_check(input_driver_st.overlay_ptr);
   if (!mod_editor_active || mod_editor_wait_close || mod_ui_timer <= 0 || max < 18)
      return 0;
   n = mod_ui_rects(r);
   for (k = 0; k < n; k++)
      lab[k] = nomes[k];
   {
      input_overlay_t *ol = input_driver_st.overlay_ptr;
      if (mod_grid_open)
      {
         static char hdr[96];
         for (k = 0; k < 18; k++)
            lab[k] = NULL;
         mod_cfg_system_name(ol, hdr, sizeof(hdr));
         lab[1]  = hdr;
         lab[13] = "Fechar";
         return n;
      }
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
   int r[72];
   int k, n;
   if (mod_ui_timer <= 0)
      return -1;
   n = mod_ui_rects(r);
   for (k = n - 1; k >= 0; k--)
      if (   r[k * 4 + 2] > 0 && px >= (float)r[k * 4 + 0] && px < (float)(r[k * 4 + 0] + r[k * 4 + 2])
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
   if (mod_grid_open)
   {
      if (b == 2 && mod_grid_item >= 0)
      {
         mod_reg_sel   = mod_grid_item;
         mod_grid_open = false;
         mod_struct_op(1);
      }
      else if (b == 13)
         mod_grid_open = false;
      return;
   }
   if (b == 12)
   {
      mod_reg_build(input_driver_st.overlay_ptr);
      mod_grid_off    = 0.0f;
      mod_grid_vel    = 0.0f;
      mod_grid_open   = true;
      mod_grid_down   = true;
      mod_grid_moved  = true;
      mod_grid_b      = -1;
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

static int mod_grid_maxoff(void)
{
   int cand[MOD_REG_MAX];
   int nc = mod_reg_cand(input_driver_st.overlay_ptr, cand, MOD_REG_MAX);
   int mx = nc * mod_grid_pitch - (mod_grid_pitch - mod_grid_rh) - mod_grid_vh;
   return (mx > 0) ? mx : 0;
}

/* inercia: chamado a cada quadro desenhado */
static void mod_grid_step(void)
{
   if (!mod_grid_open || mod_grid_down)
      return;
   if (mod_grid_vel > 0.4f || mod_grid_vel < -0.4f)
   {
      int mx = mod_grid_maxoff();
      mod_grid_off += mod_grid_vel;
      mod_grid_vel *= 0.94f;
      if (mod_grid_off < 0.0f)
      {
         mod_grid_off = 0.0f;
         mod_grid_vel = 0.0f;
      }
      if (mod_grid_off > (float)mx)
      {
         mod_grid_off = (float)mx;
         mod_grid_vel = 0.0f;
      }
   }
   else
      mod_grid_vel = 0.0f;
}

static void mod_grid_touch(float px, float py)
{
   int r[72];
   if (mod_ui_rects(r) <= 0)
      return;
   mod_grid_vh = r[11];
   if (!mod_grid_down)
   {
      mod_grid_down  = true;
      mod_grid_moved = false;
      mod_grid_b     = mod_ui_hit(px, py);
      mod_grid_item  = -1;
      if (mod_grid_b == 2 && mod_grid_pitch > 0)
      {
         int cand[MOD_REG_MAX];
         int nc = mod_reg_cand(input_driver_st.overlay_ptr, cand, MOD_REG_MAX);
         int rel = (int)py - r[9] + (int)mod_grid_off;
         int it  = rel / mod_grid_pitch;
         if (rel >= 0 && it < nc && (rel % mod_grid_pitch) < mod_grid_rh)
            mod_grid_item = it;
      }
      mod_grid_sy  = (int)py;
      mod_grid_s0  = (int)mod_grid_off;
      mod_grid_lpy = py;
      mod_grid_vel = 0.0f;
      return;
   }
   {
      float dy = py - (float)mod_grid_sy;
      if (dy > 14.0f || dy < -14.0f)
         mod_grid_moved = true;
      if (mod_grid_moved)
      {
         int mx = mod_grid_maxoff();
         float no = (float)mod_grid_s0 - dy;
         if (no < 0.0f)
            no = 0.0f;
         if (no > (float)mx)
            no = (float)mx;
         mod_grid_off = no;
         mod_grid_vel = 0.6f * mod_grid_vel + 0.4f * (mod_grid_lpy - py);
      }
      mod_grid_lpy = py;
   }
}

static void mod_grid_release(void)
{
   if (!mod_grid_down)
      return;
   mod_grid_down = false;
   if (!mod_grid_open || mod_grid_moved)
      return;
   if (mod_grid_b < 0)
   {
      mod_grid_open = false;
      return;
   }
   mod_ui_press(mod_grid_b);
}

'''

import os
UI = UI.replace('BOTOES_PLACEHOLDER', open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'botoes_cfg.c.txt'), encoding='utf-8').read())
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
    "   if (count > 0 || mod_grid_open)\n      mod_ui_timer = 300;\n   else if (mod_ui_timer > 0)\n      mod_ui_timer--;\n   {\n      struct video_viewport vp2;\n",
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
    "      mod_editor_screen = false;\n      mod_ui_held       = -1;\n      mod_tap_block     = false;\n      mod_grid_release();\n      mod_grp_n         = 0;\n",
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
    "         if (mod_grid_open)\n"
    "         {\n"
    "            mod_grid_touch(upx, upy);\n"
    "            return;\n"
    "         }\n"
    "         ub = mod_ui_hit(upx, upy);\n"
    "         if (ub >= 0 && (mod_ui_held < 0 || mod_ui_held == ub))\n"
    "         {\n"
    "            if (mod_ui_held != ub)\n"
    "            {\n"
    "               mod_ui_held   = ub;\n"
    "               mod_ui_held_g = mod_grid_open;\n"
    "               mod_ui_hold_n = 0;\n"
    "               mod_ui_press(ub);\n"
    "            }\n"
    "            else\n"
    "            {\n"
    "               mod_ui_hold_n++;\n"
    "               if ((ub < 4) && !mod_ui_held_g && mod_ui_hold_n > 24 && (mod_ui_hold_n % 4) == 0)\n"
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
      extern bool input_overlay_editor_grid_open(void);
      int         ur[18 * 4];
      const char *ulab[18];
      int         un = input_overlay_editor_ui(ur, ulab, 18);
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
         float    fill_bg[16] = {
            0.16f, 0.17f, 0.19f, 0.97f, 0.16f, 0.17f, 0.19f, 0.97f,
            0.16f, 0.17f, 0.19f, 0.97f, 0.16f, 0.17f, 0.19f, 0.97f,
         };
         float    fill_row[16] = {
            0.32f, 0.33f, 0.36f, 1.0f, 0.32f, 0.33f, 0.36f, 1.0f,
            0.32f, 0.33f, 0.36f, 1.0f, 0.32f, 0.33f, 0.36f, 1.0f,
         };
         bool     gmode = input_overlay_editor_grid_open();
         if (out_w > 0 && out_h > 0)
         {
            gfx_display_blend_begin(dispctx, userdata);
            for (ui = 0; ui < un; ui++)
            {
               int bx = ur[ui * 4 + 0] * lay_w / out_w;
               int by = ur[ui * 4 + 1] * lay_h / out_h;
               int bw = ur[ui * 4 + 2] * lay_w / out_w;
               int bh = ur[ui * 4 + 3] * lay_h / out_h;
               if (bw <= 0 || (gmode && ui != 0))
                  continue;
               gfx_display_draw_quad(
                     p_disp, userdata, video_info->dims,
                     bx, by, VIDEO_SCALE_PACK(bw, bh),
                     video_info->dims,
                     (gmode && ui == 0) ? fill_bg : (gmode ? fill_row : fill), NULL);
            }
            gfx_display_blend_end(dispctx, userdata);
            /* lista rolavel dos botoes (com recorte) */
            {
               extern int  input_overlay_editor_item_count(void);
               extern bool input_overlay_editor_item(int i, const char **lab, const char **img);
               extern void input_overlay_editor_grid_metrics(int *rh, int *pitch, int *off);
               extern bool image_texture_load(struct texture_image *img, const char *path);
               static char      mod_tex_path[16][1024];
               static uintptr_t mod_tex_id[16];
               static unsigned  mod_tex_age[16];
               static unsigned  mod_tex_clk = 0;
               int ti;
               if (!gmode)
               {
                  for (ti = 0; ti < 16; ti++)
                     if (mod_tex_id[ti])
                     {
                        video_driver_texture_unload(&mod_tex_id[ti]);
                        mod_tex_id[ti]      = 0;
                        mod_tex_path[ti][0] = '\0';
                     }
               }
               else
               {
                  int cnt = input_overlay_editor_item_count();
                  int rh, pitch, off, i;
                  int vx = ur[8]  * lay_w / out_w;
                  int vy = ur[9]  * lay_h / out_h;
                  int vw = ur[10] * lay_w / out_w;
                  int vh = ur[11] * lay_h / out_h;
                  input_overlay_editor_grid_metrics(&rh, &pitch, &off);
                  rh    = rh    * lay_h / out_h;
                  pitch = pitch * lay_h / out_h;
                  off   = off   * lay_h / out_h;
                  mod_tex_clk++;
                  gfx_widgets_flush_text(video_info->dims,
                        &p_dispwidget->gfx_widget_fonts.regular);
                  gfx_display_scissor_begin(p_disp, userdata, video_info->dims,
                        vx, vy, VIDEO_SCALE_PACK(vw, vh));
                  if (cnt == 0)
                  {
                     gfx_display_draw_text(
                           p_dispwidget->gfx_widget_fonts.regular.font,
                           "Nenhum botao encontrado no .cfg",
                           (float)(vx + vw / 2), (float)(vy + rh * 65 / 100),
                           video_info->dims, 0xFFFFFFFF, TEXT_ALIGN_CENTER,
                           1.0f, false, 0.0f, false);
                     p_dispwidget->gfx_widget_fonts.regular.usage_count++;
                  }
                  for (i = 0; i < cnt; i++)
                  {
                     const char *lb = NULL, *ip = NULL;
                     int iy = vy + i * pitch - off;
                     int sl;
                     if (iy + rh < vy || iy > vy + vh)
                        continue;
                     if (!input_overlay_editor_item(i, &lb, &ip))
                        continue;
                     if (ip)
                     {
                        for (sl = 0; sl < 16; sl++)
                           if (mod_tex_id[sl] && !strcmp(mod_tex_path[sl], ip))
                              break;
                        if (sl == 16)
                        {
                           struct texture_image ti_img;
                           int old = 0;
                           for (sl = 0; sl < 16 && mod_tex_id[sl]; sl++)
                              if (mod_tex_age[sl] < mod_tex_age[old])
                                 old = sl;
                           if (sl == 16)
                           {
                              sl = old;
                              video_driver_texture_unload(&mod_tex_id[sl]);
                              mod_tex_id[sl] = 0;
                           }
                           memset(&ti_img, 0, sizeof(ti_img));
                           ti_img.supports_rgba = (video_driver_get_disp_flags() & VIDEO_FLAG_USE_RGBA) ? true : false;
                           if (image_texture_load(&ti_img, ip))
                           {
                              if (!video_driver_texture_load(&ti_img,
                                    TEXTURE_FILTER_MIPMAP_LINEAR, &mod_tex_id[sl]))
                                 mod_tex_id[sl] = 0;
                              image_texture_free(&ti_img);
                           }
                           strlcpy(mod_tex_path[sl], ip, sizeof(mod_tex_path[sl]));
                           if (!mod_tex_id[sl])
                              mod_tex_path[sl][0] = '\0';
                        }
                        if (sl < 16 && mod_tex_id[sl])
                        {
                           float white[16] = {
                              1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
                              1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f };
                           int side = rh * 80 / 100;
                           mod_tex_age[sl] = mod_tex_clk;
                           gfx_widgets_draw_icon(userdata, p_disp, video_info->dims,
                                 VIDEO_SCALE_PACK(side, side), mod_tex_id[sl],
                                 (float)(vx + rh * 10 / 100), (float)(iy + rh * 10 / 100),
                                 0.0f, 1.0f, 0.0f, white);
                        }
                     }
                     gfx_display_draw_text(
                           p_dispwidget->gfx_widget_fonts.regular.font, lb,
                           (float)(vx + rh * 110 / 100), (float)(iy + rh * 65 / 100),
                           video_info->dims, 0xFFFFFFFF, TEXT_ALIGN_LEFT,
                           1.0f, false, 0.0f, false);
                     p_dispwidget->gfx_widget_fonts.regular.usage_count++;
                  }
                  gfx_widgets_flush_text(video_info->dims,
                        &p_dispwidget->gfx_widget_fonts.regular);
                  if (dispctx && dispctx->scissor_end)
                     dispctx->scissor_end(userdata,
                           gfx_display_output_dims(p_disp, video_info->dims));
               }
            }
            for (ui = 0; ui < un; ui++)
            {
               int bx = ur[ui * 4 + 0] * lay_w / out_w;
               int by = ur[ui * 4 + 1] * lay_h / out_h;
               int bw = ur[ui * 4 + 2] * lay_w / out_w;
               int bh = ur[ui * 4 + 3] * lay_h / out_h;
               if (bw <= 0 || !ulab[ui])
                  continue;
               gfx_display_draw_text(
                     p_dispwidget->gfx_widget_fonts.regular.font,
                     ulab[ui],
                     (float)((gmode && ui >= 2 && ui < 8) ? (bx + bh * 110 / 100) : (bx + bw / 2)),
                     (float)(by + bh * 65 / 100),
                     video_info->dims,
                     0xFFFFFFFF, (gmode && ui >= 2 && ui < 8) ? TEXT_ALIGN_LEFT : TEXT_ALIGN_CENTER,
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

# 4b: declaracoes, selecao (toque triplo remove), checagem do recarregamento
trocar(
    INPUT,
    "static float mod_grp_py = 0.0f;\n",
    "static float mod_grp_py = 0.0f;\n"
    "static int   mod_rm_grp[MOD_MAX_GRP];\n"
    "static int   mod_rm_n       = 0;\n"
    "static int   mod_rm_page    = -1;\n"
    "static bool  mod_rm_confirm = false;\n"
    "static int   mod_tap_n      = 0;\n"
    "static int   mod_tap_key    = -1;\n"
    "static int   mod_tap_pg     = -1;\n"
    "static unsigned mod_tap_fr  = 0;\n"
    "static unsigned mod_tap_now = 0;\n"
    "static float mod_tap_x      = 0.0f;\n"
    "static float mod_tap_y      = 0.0f;\n"
    "static bool  mod_tap_block  = false;\n",
)
trocar(
    INPUT,
    "      if (mod_editor_sel < 0 && !mod_editor_screen)\n      {\n         size_t i;\n",
    "      if (mod_editor_sel < 0 && !mod_editor_screen && !mod_tap_block)\n      {\n         size_t i;\n",
)
trocar(
    INPUT,
    "         if (mod_editor_sel >= 0)\n            mod_build_group(ol->active, mod_editor_sel);\n",
    "         if (mod_editor_sel >= 0)\n         {\n            int gk, gmin = 1 << 30;\n"
    "            mod_build_group(ol->active, mod_editor_sel);\n"
    "            memcpy(mod_rm_grp, mod_grp, sizeof(mod_rm_grp));\n"
    "            mod_rm_n       = mod_grp_n;\n"
    "            mod_rm_page    = (int)ol->index;\n"
    "            for (gk = 0; gk < mod_grp_n; gk++)\n"
    "               if (mod_grp[gk] < gmin)\n"
    "                  gmin = mod_grp[gk];\n"
    "            if (gmin == mod_tap_key && mod_rm_page == mod_tap_pg\n"
    "                  && mod_tap_now - mod_tap_fr < 90)\n"
    "               mod_tap_n++;\n"
    "            else\n"
    "               mod_tap_n = 1;\n"
    "            mod_tap_key = gmin;\n"
    "            mod_tap_pg  = mod_rm_page;\n"
    "            mod_tap_fr  = mod_tap_now;\n"
    "            mod_tap_x   = x;\n"
    "            mod_tap_y   = y;\n"
    "            if (mod_tap_n >= 3)\n"
    "            {\n"
    "               mod_tap_n      = 0;\n"
    "               mod_tap_key    = -1;\n"
    "               mod_tap_block  = true;\n"
    "               mod_editor_sel = -1;\n"
    "               mod_grp_n      = 0;\n"
    "               mod_struct_op(2);\n"
    "            }\n         }\n",
)
trocar(
    INPUT,
    "         float ddx = (x - mod_editor_grab_dx) - t->x_shift;\n",
    "         float ddx = (x - mod_editor_grab_dx) - t->x_shift;\n"
    "         if (fabsf(x - mod_tap_x) > 0.02f || fabsf(y - mod_tap_y) > 0.02f)\n"
    "            mod_tap_n = 0;\n",
)
trocar(
    INPUT,
    "      const input_overlay_state_t *st)\n{\n   int kk;\n",
    "      const input_overlay_state_t *st)\n{\n   int kk;\n   mod_tap_now++;\n   mod_reload_check(ol);\n",
)
trocar(
    INPUT,
    "         if (mod_ui_held >= 0)\n            return;\n",
    "         if (mod_ui_held >= 0 || mod_grid_open)\n            return;\n",
)

for arq, conteudo in arquivos.items():
    with open(f"{raiz}/{arq}", "w", encoding="utf-8") as f:
        f.write(conteudo)
    print("ok:", arq)
