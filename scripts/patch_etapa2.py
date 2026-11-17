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
static float mod_editor_rx0        = 0.0f;
static float mod_editor_ry0        = 0.0f;
static float mod_editor_x0         = 0.0f;
static float mod_editor_y0         = 0.0f;

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
      }
      else if (mod_editor_fingers < 2)
      {
         struct overlay_desc *d = &descs[mod_editor_sel];
         d->x += (x - mod_editor_grab_dx) - d->x_shift;
         d->y += (y - mod_editor_grab_dy) - d->y_shift;
         mod_editor_apply(ol);
      }
   }
   else if (idx == 1 && mod_editor_sel >= 0)
   {
      struct overlay_desc *d = &descs[mod_editor_sel];
      float dx = x - mod_editor_x0;
      float dy = y - mod_editor_y0;
      float dist = sqrtf(dx * dx + dy * dy);

      if (!mod_editor_pinch)
      {
         mod_editor_pinch    = true;
         mod_editor_pinch_d0 = (dist > 0.01f) ? dist : 0.01f;
         mod_editor_rx0      = d->range_x;
         mod_editor_ry0      = d->range_y;
      }
      else
      {
         float k = dist / mod_editor_pinch_d0;
         if (k < 0.3f) k = 0.3f;
         if (k > 3.0f) k = 3.0f;
         d->range_x = mod_editor_rx0 * k;
         d->range_y = mod_editor_ry0 * k;
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
