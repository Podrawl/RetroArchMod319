#!/usr/bin/env python3
"""Etapa 2 do editor de overlay: arrastar (1 dedo) e redimensionar (2 dedos) botoes
do overlay ativo, SO NA MEMORIA (nada e salvo). 3 dedos ou Voltar encerram.
Roda DEPOIS de patch_etapa1.py. Uso: patch_etapa2.py <pasta_do_RetroArch>
Cada troca exige que o trecho exista exatamente uma vez.
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


# ---------------------------------------------------------------- codigo do editor
EDITOR = r'''
/* ===== MOD: editor de overlay (etapa 2) =====
 * Arrastar/redimensionar botoes do overlay ativo, so em memoria. */
#define MOD_MAX_LAYOUTS 64
static overlay_layout_t mod_layouts[MOD_MAX_LAYOUTS];
static bool mod_layout_ok[MOD_MAX_LAYOUTS];

static bool  mod_editor_active     = false;
static bool  mod_editor_wait_close = false;
static int   mod_editor_sel        = -1;
static float mod_editor_grab_dx    = 0.0f;
static float mod_editor_grab_dy    = 0.0f;
static int   mod_editor_fingers    = 0;
static bool  mod_editor_pinch      = false;
static float mod_editor_pinch_d0   = 1.0f;
static float mod_editor_x0         = 0.0f;
static float mod_editor_y0         = 0.0f;

/* Grupo movido/redimensionado junto (direcional inteiro, analogico + circulo) */
#define MOD_MAX_GRP 64
static int   mod_grp[MOD_MAX_GRP];
static int   mod_grp_n = 0;
static float mod_grp_x0[MOD_MAX_GRP];
static float mod_grp_y0[MOD_MAX_GRP];
static float mod_grp_rx0[MOD_MAX_GRP];
static float mod_grp_ry0[MOD_MAX_GRP];
static float mod_grp_px = 0.0f;
static float mod_grp_py = 0.0f;

static void input_overlay_scale(struct overlay *ol,
      const overlay_layout_t *layout);
static void input_overlay_set_vertex_geom(input_overlay_t *ol);

static void mod_editor_apply(input_overlay_t *ol)
{
   size_t pi = (size_t)(ol->active - ol->overlays);
   if (pi >= MOD_MAX_LAYOUTS || !mod_layout_ok[pi])
      return;
   input_overlay_scale(ol->active, &mod_layouts[pi]);
   input_overlay_set_vertex_geom(ol);
}

/* Uma vez por leitura de toques; count = dedos na tela. */
static void mod_editor_frame(input_overlay_t *ol, int count)
{
   bool menu_alive = (menu_state_get_ptr()->flags & MENU_ST_FLAG_ALIVE) != 0;

   /* So considera "menu aberto" depois de ter visto o menu fechado uma vez */
   if (mod_editor_wait_close)
   {
      if (!menu_alive)
         mod_editor_wait_close = false;
   }
   else if (menu_alive)
   {
      mod_editor_active = false;
      return;
   }

   mod_editor_fingers = count;
   if (count == 0)
   {
      mod_editor_sel   = -1;
      mod_editor_pinch = false;
      mod_grp_n        = 0;
   }
   else if (count >= 3)
   {
      static const char msg[] = "Editor de overlay encerrado.";
      mod_editor_active = false;
      mod_editor_sel    = -1;
      mod_editor_pinch  = false;
      runloop_msg_queue_push(msg, sizeof(msg) - 1, 1, 120, true, NULL,
            MESSAGE_QUEUE_ICON_DEFAULT, MESSAGE_QUEUE_CATEGORY_INFO);
   }
}

static bool mod_mask_empty(const struct overlay_desc *d)
{
   size_t k;
   for (k = 0; k < ARRAY_SIZE(d->button_mask.data); k++)
      if (d->button_mask.data[k])
         return false;
   return true;
}

/* Botao so de direcao (cima/baixo/esquerda/direita e diagonais) ou area de dpad */
static bool mod_is_dir(const struct overlay_desc *d)
{
   unsigned k;
   bool any = false;
   if (d->type == OVERLAY_TYPE_DPAD_AREA)
      return true;
   if (d->type != OVERLAY_TYPE_BUTTONS)
      return false;
   for (k = 0; k < 256; k++)
   {
      if (!BIT256_GET(d->button_mask, k))
         continue;
      if (   k == RETRO_DEVICE_ID_JOYPAD_UP   || k == RETRO_DEVICE_ID_JOYPAD_DOWN
          || k == RETRO_DEVICE_ID_JOYPAD_LEFT || k == RETRO_DEVICE_ID_JOYPAD_RIGHT)
         any = true;
      else
         return false;
   }
   return any;
}

static bool mod_is_analog(const struct overlay_desc *d)
{
   return d->type == OVERLAY_TYPE_ANALOG_LEFT
       || d->type == OVERLAY_TYPE_ANALOG_RIGHT;
}

static bool mod_is_nul(const struct overlay_desc *d)
{
   return d->type == OVERLAY_TYPE_BUTTONS && mod_mask_empty(d);
}

/* Dois botoes vizinhos (encostados ou quase) */
static bool mod_adj(const struct overlay_desc *a, const struct overlay_desc *b)
{
   float dx = a->x - b->x, dy = a->y - b->y;
   if (dx < 0.0f) dx = -dx;
   if (dy < 0.0f) dy = -dy;
   return dx <= (a->range_x + b->range_x) * 1.6f
       && dy <= (a->range_y + b->range_y) * 1.6f;
}

static void mod_grp_add(int i)
{
   int k;
   for (k = 0; k < mod_grp_n; k++)
      if (mod_grp[k] == i)
         return;
   if (mod_grp_n < MOD_MAX_GRP)
      mod_grp[mod_grp_n++] = i;
}

/* Monta o grupo do botao tocado t. */
static void mod_build_group(struct overlay *pg, int t)
{
   struct overlay_desc *descs = pg->descs;
   int n = (int)pg->size;
   int i, seed = -1;

   mod_grp_n = 0;

   /* analogico: ele mais os "nul" no mesmo lugar (a imagem do circulo) */
   {
      int anchor = -1;
      if (mod_is_analog(&descs[t]))
         anchor = t;
      else if (mod_is_nul(&descs[t]))
         for (i = 0; i < n; i++)
            if (mod_is_analog(&descs[i]))
            {
               float dx = descs[t].x - descs[i].x, dy = descs[t].y - descs[i].y;
               if (dx < 0.0f) dx = -dx;
               if (dy < 0.0f) dy = -dy;
               if (dx <= 0.5f * descs[i].range_x && dy <= 0.5f * descs[i].range_y)
               {
                  anchor = i;
                  break;
               }
            }
      if (anchor >= 0)
      {
         mod_grp_add(anchor);
         for (i = 0; i < n; i++)
         {
            float dx, dy;
            if (i == anchor || !mod_is_nul(&descs[i]))
               continue;
            dx = descs[i].x - descs[anchor].x;
            dy = descs[i].y - descs[anchor].y;
            if (dx < 0.0f) dx = -dx;
            if (dy < 0.0f) dy = -dy;
            if (dx <= 0.5f * descs[anchor].range_x && dy <= 0.5f * descs[anchor].range_y)
               mod_grp_add(i);
         }
         return;
      }
   }

   /* direcional: todos os botoes de direcao ligados entre si + "nul" do centro */
   if (mod_is_dir(&descs[t]))
      seed = t;
   else if (mod_is_nul(&descs[t]))
      for (i = 0; i < n; i++)
         if (mod_is_dir(&descs[i]) && mod_adj(&descs[t], &descs[i]))
         {
            seed = i;
            break;
         }

   if (seed >= 0)
   {
      int k;
      mod_grp_add(seed);
      for (k = 0; k < mod_grp_n; k++)       /* varre ampliando o grupo */
         for (i = 0; i < n; i++)
            if (mod_is_dir(&descs[i]) && mod_adj(&descs[mod_grp[k]], &descs[i]))
               mod_grp_add(i);
      {
         int dirs = mod_grp_n;
         for (i = 0; i < n; i++)
            if (mod_is_nul(&descs[i]))
               for (k = 0; k < dirs; k++)
                  if (mod_adj(&descs[mod_grp[k]], &descs[i]))
                  {
                     mod_grp_add(i);
                     break;
                  }
      }
      return;
   }

   mod_grp_add(t);
}

/* Um dedo (idx) em (x,y), no mesmo espaco dos botoes (x_shift/y_shift). */
static void mod_editor_touch(input_overlay_t *ol, int idx, float x, float y)
{
   struct overlay_desc *descs = ol->active->descs;

   if (idx == 0)
   {
      mod_editor_x0 = x;
      mod_editor_y0 = y;

      if (mod_editor_sel < 0)
      {
         size_t i;
         float  best = 1e9f;
         for (i = 0; i < ol->active->size; i++)
         {
            struct overlay_desc *d = &descs[i];
            float area = d->range_x * d->range_y;
            if (area <= 0.0f)
               continue;
            if (!input_overlay_coords_inside_hitbox(d, x, y, false))
               continue;
            if (area < best)
            {
               best                = area;
               mod_editor_sel      = (int)i;
               mod_editor_grab_dx  = x - d->x_shift;
               mod_editor_grab_dy  = y - d->y_shift;
            }
         }
         if (mod_editor_sel >= 0)
            mod_build_group(ol->active, mod_editor_sel);
      }
      else if (mod_editor_fingers < 2)
      {
         struct overlay_desc *t = &descs[mod_editor_sel];
         float ddx = (x - mod_editor_grab_dx) - t->x_shift;
         float ddy = (y - mod_editor_grab_dy) - t->y_shift;
         int k;
         for (k = 0; k < mod_grp_n; k++)
         {
            descs[mod_grp[k]].x += ddx;
            descs[mod_grp[k]].y += ddy;
         }
         mod_editor_apply(ol);
      }
   }
   else if (idx == 1 && mod_editor_sel >= 0)
   {
      float dx = x - mod_editor_x0;
      float dy = y - mod_editor_y0;
      float dist = sqrtf(dx * dx + dy * dy);
      int k;

      if (!mod_editor_pinch)
      {
         float minx = 1e9f, maxx = -1e9f, miny = 1e9f, maxy = -1e9f;
         mod_editor_pinch    = true;
         mod_editor_pinch_d0 = (dist > 0.01f) ? dist : 0.01f;
         for (k = 0; k < mod_grp_n; k++)
         {
            struct overlay_desc *d = &descs[mod_grp[k]];
            mod_grp_x0[k]  = d->x;
            mod_grp_y0[k]  = d->y;
            mod_grp_rx0[k] = d->range_x;
            mod_grp_ry0[k] = d->range_y;
            if (d->x < minx) minx = d->x;
            if (d->x > maxx) maxx = d->x;
            if (d->y < miny) miny = d->y;
            if (d->y > maxy) maxy = d->y;
         }
         mod_grp_px = 0.5f * (minx + maxx);
         mod_grp_py = 0.5f * (miny + maxy);
      }
      else
      {
         float f = dist / mod_editor_pinch_d0;
         if (f < 0.3f) f = 0.3f;
         if (f > 3.0f) f = 3.0f;
         for (k = 0; k < mod_grp_n; k++)
         {
            struct overlay_desc *d = &descs[mod_grp[k]];
            d->x       = mod_grp_px + (mod_grp_x0[k] - mod_grp_px) * f;
            d->y       = mod_grp_py + (mod_grp_y0[k] - mod_grp_py) * f;
            d->range_x = mod_grp_rx0[k] * f;
            d->range_y = mod_grp_ry0[k] * f;
         }
         mod_editor_apply(ol);
      }
   }
}
/* ===== fim MOD ===== */

'''

trocar(
    "static bool input_overlay_poll(\n      input_overlay_t *ol,\n",
    EDITOR + "static bool input_overlay_poll(\n      input_overlay_t *ol,\n",
)

# Gancho por dedo: dentro de input_overlay_poll, logo apos calcular x,y
trocar(
    "   x *= touch_scale;\n   y *= touch_scale;\n\n   for (i = 0; i < ol->active->size; i++)\n   {\n      float x_dist, y_dist;\n",
    "   x *= touch_scale;\n   y *= touch_scale;\n\n"
    "   /* MOD: no modo editor, o toque nao aperta botao: edita */\n"
    "   if (mod_editor_active)\n"
    "   {\n"
    "      mod_editor_touch(ol, touch_idx, x, y);\n"
    "      return false;\n"
    "   }\n\n"
    "   for (i = 0; i < ol->active->size; i++)\n   {\n      float x_dist, y_dist;\n",
)

# Gancho por leitura: logo apos contar os dedos
trocar(
    "      ol_state->touch_count = i;\n",
    "      ol_state->touch_count = i;\n"
    "      if (mod_editor_active)\n"
    "         mod_editor_frame(ol, (int)i);\n",
)

# Guarda o layout calculado de cada pagina (para reaplicar depois de mover)
trocar(
    "      input_overlay_parse_layout(current_overlay,\n"
    "            layout_desc, display_aspect_ratio, &overlay_layout);\n"
    "      input_overlay_scale(current_overlay, &overlay_layout);\n",
    "      input_overlay_parse_layout(current_overlay,\n"
    "            layout_desc, display_aspect_ratio, &overlay_layout);\n"
    "      if (i < MOD_MAX_LAYOUTS)\n"
    "      {\n"
    "         mod_layouts[i]   = overlay_layout;\n"
    "         mod_layout_ok[i] = true;\n"
    "      }\n"
    "      input_overlay_scale(current_overlay, &overlay_layout);\n",
)

# Entrada no modo (substitui o corpo da etapa 1)
trocar(
    '''   static const char msg[] =
         "Editor de overlay (teste): jogo pausado. Abra o menu para sair.";
   command_event(CMD_EVENT_RESUME, NULL);''',
    '''   static const char msg[] =
         "Editor: 1 dedo move, 2 dedos mudam o tamanho, 3 dedos ou Voltar saem.";
   mod_editor_active     = true;
   mod_editor_wait_close = true;
   mod_editor_sel        = -1;
   mod_editor_pinch      = false;
   command_event(CMD_EVENT_RESUME, NULL);''',
)

# Saida chamada de fora (ex.: botao Voltar)
s += '''
#ifdef HAVE_OVERLAY
/* MOD: sai do modo editor (chamado, por exemplo, pelo botao Voltar) */
void input_overlay_editor_exit(void)
{
   mod_editor_active = false;
   mod_editor_sel    = -1;
   mod_editor_pinch  = false;
}
#endif
'''

open(caminho, "w", encoding="utf-8").write(s)
print("ok: input/input_driver.c (etapa 2)")
