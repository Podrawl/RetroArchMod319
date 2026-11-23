#!/usr/bin/env python3
"""Menu: Renomear cópia / Apagar cópia de overlay (só arquivos criados pelo app).
Reaproveita o seletor de arquivos do 'Overlay Preset'.
Uso: patch_copias.py <pasta_do_RetroArch>
"""
import sys

raiz = sys.argv[1]


def trocar(arquivo, antigo, novo):
    caminho = f"{raiz}/{arquivo}"
    s = open(caminho, encoding="utf-8").read()
    n = s.count(antigo)
    if n != 1:
        sys.exit(f"ERRO: {arquivo}: trecho aparece {n} vezes: {antigo[:70]!r}")
    open(caminho, "w", encoding="utf-8").write(s.replace(antigo, novo))
    print(f"ok: {arquivo}")


# 1) textos/enums das duas linhas de menu
trocar(
    "settings/settings_def_menu_main_lists_4.h",
    '      "Move and resize the on-screen buttons and the game screen. Work in progress.")\n#endif\n',
    '      "Move and resize the on-screen buttons and the game screen. Work in progress.")\n'
    'S_ACTION_EX(OVERLAY_COPY_RENAME,\n'
    '      "overlay_copy_rename", SD_FLAG_LAKKA_ADVANCED, NULL, NULL, 0,\n'
    '      "Rename Overlay Copy",\n'
    '      "Rename an overlay copy created by the layout editor. Original overlays cannot be renamed.")\n'
    'S_ACTION_EX(OVERLAY_COPY_DELETE,\n'
    '      "overlay_copy_delete", SD_FLAG_LAKKA_ADVANCED, NULL, NULL, 0,\n'
    '      "Delete Overlay Copy",\n'
    '      "Delete an overlay copy created by the layout editor. Original overlays cannot be deleted.")\n#endif\n',
)

# 2) linhas na lista do overlay
trocar(
    "menu/menu_displaylist.c",
    "               {MENU_ENUM_LABEL_OVERLAY_EDITOR,                            PARSE_ACTION,     false },\n",
    "               {MENU_ENUM_LABEL_OVERLAY_EDITOR,                            PARSE_ACTION,     false },\n"
    "               {MENU_ENUM_LABEL_OVERLAY_COPY_RENAME,                       PARSE_ACTION,     false },\n"
    "               {MENU_ENUM_LABEL_OVERLAY_COPY_DELETE,                       PARSE_ACTION,     false },\n",
)
trocar(
    "menu/menu_displaylist.c",
    "                  case MENU_ENUM_LABEL_OVERLAY_EDITOR:\n",
    "                  case MENU_ENUM_LABEL_OVERLAY_COPY_RENAME:\n"
    "                  case MENU_ENUM_LABEL_OVERLAY_COPY_DELETE:\n"
    "                  case MENU_ENUM_LABEL_OVERLAY_EDITOR:\n",
)

# 3) acoes: o seletor de overlay passa a "agir" em vez de carregar
trocar(
    "menu/cbs/menu_cbs_ok.c",
    "STATIC_DEFAULT_ACTION_OK_FUNC(action_ok_overlay_preset, ACTION_OK_DL_OVERLAY_PRESET)\n",
    r'''STATIC_DEFAULT_ACTION_OK_FUNC(action_ok_overlay_preset_orig, ACTION_OK_DL_OVERLAY_PRESET)
#ifdef HAVE_OVERLAY
/* MOD: copias de overlay (renomear/apagar); definido em input/input_driver.c */
bool input_overlay_mod_is_copy(const char *path);
bool input_overlay_mod_delete(const char *path);
bool input_overlay_mod_rename(const char *path, const char *novo);
void input_overlay_mod_toast(const char *msg);

static unsigned mod_copias_modo = 0;   /* 0 = escolher overlay normal, 1 = renomear, 2 = apagar */
static char     mod_copia_alvo[PATH_MAX_LENGTH];
static char     mod_copia_apagar[PATH_MAX_LENGTH];
static char     mod_copia_nome[PATH_MAX_LENGTH];

/* a entrada normal "Overlay Preset" volta ao comportamento de sempre */
static int action_ok_overlay_preset(const char *path,
      const char *label, unsigned type, size_t idx, size_t entry_idx)
{
   mod_copias_modo = 0;
   return action_ok_overlay_preset_orig(path, label, type, idx, entry_idx);
}

static int action_ok_mod_copia_menu(unsigned modo, const char *path,
      const char *label, unsigned type, size_t idx, size_t entry_idx)
{
   mod_copias_modo     = modo;
   mod_copia_apagar[0] = '\0';
   input_overlay_mod_toast(modo == 1
         ? "Escolha a copia (-mod) que quer renomear."
         : "Escolha a copia (-mod) que quer apagar. Toque duas vezes.");
   return action_ok_overlay_preset_orig(path, label, type, idx, entry_idx);
}

static int action_ok_overlay_copy_rename(const char *path,
      const char *label, unsigned type, size_t idx, size_t entry_idx)
{
   return action_ok_mod_copia_menu(1, path, label, type, idx, entry_idx);
}

static int action_ok_overlay_copy_delete(const char *path,
      const char *label, unsigned type, size_t idx, size_t entry_idx)
{
   return action_ok_mod_copia_menu(2, path, label, type, idx, entry_idx);
}

static void mod_copia_caminho(const char *path, char *dst, size_t len)
{
   const char *menu_path = NULL;
   menu_entries_get_last_stack(&menu_path, NULL, NULL, NULL, NULL);
   if (path && *path && menu_path)
      fill_pathname_join_special(dst, menu_path, path, len);
   else
      strlcpy(dst, path ? path : "", len);
}

static void menu_input_st_string_cb_mod_renomear(void *userdata,
      const char *str)
{
   if (str && *str)
   {
      const char *novo = menu_input_dialog_get_buffer();
      if (novo && *novo && input_overlay_mod_rename(mod_copia_alvo, novo))
         menu_state_get_ptr()->flags |= MENU_ST_FLAG_ENTRIES_NEED_REFRESH;
   }
   menu_input_dialog_end();
}

static int action_ok_mod_copia_renomear(const char *path,
      const char *label, unsigned type, size_t idx, size_t entry_idx)
{
   menu_input_ctx_line_t line = {0};
   const char *base;
   mod_copia_caminho(path, mod_copia_alvo, sizeof(mod_copia_alvo));
   if (!input_overlay_mod_is_copy(mod_copia_alvo))
   {
      input_overlay_mod_toast("So da para renomear copias criadas pelo app.");
      return 0;
   }
   base = path_basename(mod_copia_alvo);
   strlcpy(mod_copia_nome, base, sizeof(mod_copia_nome));
   {
      size_t l = strlen(mod_copia_nome);
      if (l > 4 && !strcasecmp(mod_copia_nome + l - 4, ".cfg"))
         mod_copia_nome[l - 4] = '\0';
   }
   line.label         = "New name (letters, numbers, - and _)";
   line.label_setting = label;
   line.type          = type;
   line.idx           = (unsigned)entry_idx;
   line.text_type     = MENU_INPUT_DIALOG_KB_TYPE_TEXT;
   line.cb            = menu_input_st_string_cb_mod_renomear;
   line.dialog_type   = MENU_INPUT_DIALOG_TYPE_EDIT;
   line.initial_text  = mod_copia_nome;
   if (!menu_input_dialog_start(&line))
      return -1;
   return 0;
}

static int action_ok_mod_copia_apagar(const char *path,
      const char *label, unsigned type, size_t idx, size_t entry_idx)
{
   char alvo[PATH_MAX_LENGTH];
   mod_copia_caminho(path, alvo, sizeof(alvo));
   if (!input_overlay_mod_is_copy(alvo))
   {
      input_overlay_mod_toast("So da para apagar copias criadas pelo app.");
      return 0;
   }
   if (strcmp(alvo, mod_copia_apagar))
   {
      char msg[PATH_MAX_LENGTH + 64];
      strlcpy(mod_copia_apagar, alvo, sizeof(mod_copia_apagar));
      snprintf(msg, sizeof(msg), "Toque de novo para APAGAR: %s", path_basename(alvo));
      input_overlay_mod_toast(msg);
      return 0;
   }
   mod_copia_apagar[0] = '\0';
   if (input_overlay_mod_delete(alvo))
      menu_state_get_ptr()->flags |= MENU_ST_FLAG_ENTRIES_NEED_REFRESH;
   return 0;
}
#else
#define action_ok_overlay_preset action_ok_overlay_preset_orig
#endif
''',
)
# entradas do menu -> acoes (mesma lista onde o editor foi ligado)
trocar(
    "menu/cbs/menu_cbs_ok.c",
    "         {MENU_ENUM_LABEL_OVERLAY_EDITOR,                      action_ok_overlay_editor},\n",
    "         {MENU_ENUM_LABEL_OVERLAY_EDITOR,                      action_ok_overlay_editor},\n"
    "         {MENU_ENUM_LABEL_OVERLAY_COPY_RENAME,                 action_ok_overlay_copy_rename},\n"
    "         {MENU_ENUM_LABEL_OVERLAY_COPY_DELETE,                 action_ok_overlay_copy_delete},\n",
)
# arquivo escolhido no seletor de overlay
trocar(
    "menu/cbs/menu_cbs_ok.c",
    "         case FILE_TYPE_OVERLAY:\n            BIND_ACTION_OK(cbs, action_ok_set_path_overlay);\n            break;\n",
    "         case FILE_TYPE_OVERLAY:\n"
    "#ifdef HAVE_OVERLAY\n"
    "            if (mod_copias_modo == 1)\n"
    "            {\n"
    "               BIND_ACTION_OK(cbs, action_ok_mod_copia_renomear);\n"
    "               break;\n"
    "            }\n"
    "            if (mod_copias_modo == 2)\n"
    "            {\n"
    "               BIND_ACTION_OK(cbs, action_ok_mod_copia_apagar);\n"
    "               break;\n"
    "            }\n"
    "#endif\n"
    "            BIND_ACTION_OK(cbs, action_ok_set_path_overlay);\n"
    "            break;\n",
)
print("patch_copias aplicado")
