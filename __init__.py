import json
### Custom util functions
from .utils.modules import *
### Logger for debuging
from .utils.logger import logger

from typing import Any, Optional
from PyQt5.QtWidgets import QWidget
# import the main window object (mw) from aqt
from aqt import AnkiQt, DialogManager, mw
from aqt.theme import theme_manager
from aqt import gui_hooks
## QT dialog windows
# Browser import legacy check (2.1.22)
if module_exists("aqt.browser.browser"):
    from aqt.browser.browser import Browser
else:
    from aqt.browser import Browser
# DeckStats import legacy check
if module_has_attribute("aqt.stats", "NewDeckStats"):
    from aqt.stats import DeckStats, NewDeckStats
else:
    from aqt.stats import DeckStats
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.about import ClosableQDialog
from aqt.preferences import Preferences
from aqt.addons import AddonsDialog
# FilteredDeckConfigDialog import non-legacy check
if module_exists("aqt.filtered_deck"):
    from aqt.filtered_deck import FilteredDeckConfigDialog
# QT page views
from aqt.toolbar import Toolbar, TopToolbar
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar
from aqt.overview import Overview, OverviewBottomBar
from aqt.editor import Editor
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.webview import WebContent

### Load styling injections
from .injections.toolbar import redraw_toolbar_legacy

### Load config data here
from .config import config, get_config

## Addon compatibility fixes
# More Overview Stats 2.1 addon compatibility fix
addon_more_overview_stats_fix = config['addon_more_overview_stats']
addon_advanced_review_bottom_bar = config['addon_advanced_review_bottom_bar']
addon_no_distractions_full_screen = config['addon_no_distractions_full_screen']

## Customization
theme = config['theme']
# Init script/file path
from .utils.css_files import css_files_dir
from .utils.themes import themes, get_theme
logger.debug(css_files_dir)
logger.debug(themes)
themes_parsed = get_theme(theme)
color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark

from .utils.dark_title_bar import set_dark_titlebar, set_dark_titlebar_qt, dwmapi
set_dark_titlebar(mw, dwmapi)
logger.debug(dwmapi)

### CSS injections
def load_custom_style():
    # Theme config
    theme_colors_light = ""
    theme_colors_dark = ""
    for color_name in themes_parsed.get("colors"):
        color = themes_parsed.get("colors").get(color_name)
        if color[3]:
            theme_colors_light += f"{color[3]}: {color[1]};\n        "
            theme_colors_dark += f"{color[3]}: {color[2]};\n        "
        else:
            theme_colors_light += f"--{color_name.lower().replace('_','-')}: {color[color_mode]};\n        "
            theme_colors_dark += f"--{color_name.lower().replace('_','-')}: {color[color_mode]};\n        "
    # Font config
    font = config["font"]
    if config["fallbackFonts"]:
        font = f"{config['font']}, {config['fallbackFonts']}"
    custom_style = """
<style>
    /* Light */ 
    :root,
    :root .isMac,
    :root .isWin,
    :root .isLin {
        %s
    }
    /* Dark */
    :root body.nightMode,
    :root body.isWin.nightMode,
    :root body.isMac.nightMode,
    :root body.isLin.nightMode {
        %s
    }
    html {
        font-family: %s;
        font-size: %spx;
    }
</style>
    """ % (theme_colors_light, theme_colors_dark, font, config["font_size"])
    return custom_style

def load_custom_style_wrapper():
    custom_style = f"""
    const style = document.createElement("style");
    style.innerHTML = `{load_custom_style()[8:-13]}`;
    document.head.appendChild(style);
    """
    return custom_style

## Adds styling on the different webview contents, before the content is set
def on_webview_will_set_content(web_content: WebContent, context: Optional[Any]) -> None:
    logger.debug(context) # Logs content being loaded, find out the instance
    web_content.css.append(css_files_dir['global']) # Global css
    web_content.head += load_custom_style() # Custom styling
    # Deckbrowser
    if isinstance(context, DeckBrowser):
        web_content.css.append(css_files_dir['DeckBrowser'])
    # TopToolbar
    elif isinstance(context, TopToolbar):
        web_content.css.append(css_files_dir['TopToolbar'])
    # BottomToolbar (Buttons)
    elif isinstance(context, DeckBrowserBottomBar) or isinstance(context, OverviewBottomBar):
        web_content.css.append(css_files_dir['BottomBar'])
    # Overview
    elif isinstance(context, Overview):
        if addon_more_overview_stats_fix:
            web_content.head += "<style>center > table tr:first-of-type {display: table-row; flex-direction: unset;}</style>"
        web_content.css.append(css_files_dir['Overview'])
    # Editor
    elif isinstance(context, Editor):
        web_content.css.append(css_files_dir['Editor'])
    # Reviewer
    elif isinstance(context, Reviewer):
        web_content.css.append(css_files_dir['Reviewer'])
        if addon_no_distractions_full_screen:
            web_content.body += """
            <script>
                const timeout = 10, time = 0;
                let check;
                check = setInterval(() => {
                    const outer = document.getElementById('outer');
                    const iframe = document.querySelector("#bottomiFrame")?.contentDocument?.getElementById('outer');
                    if (outer && iframe) {
                        outer.classList.add('ndfs');
                        iframe.classList.add('ndfs')
                    }
                    time++;
                    if (time >= 10) clearInterval(check);
                },1000)
            </script>
            """
    elif isinstance(context, ReviewerBottomBar):
        if addon_advanced_review_bottom_bar:
            web_content.body += "<script>document.getElementById('outer').classList.add('arbb');</script>"
        else:
            web_content.css.append(css_files_dir['BottomBar'])
        web_content.css.append(css_files_dir['ReviewerBottomBar'])
        # Button padding bottom
        web_content.body += "<div style='height: 14px; opacity: 0; pointer-events: none;'></div>"
        web_content.body += "<div id='padFix' style='height: 30px; opacity: 0; pointer-events: none;'><script>const e = document.getElementById('padFix');e.parentElement.removeChild(e);</script></div>"
        mw.bottomWeb.adjustHeightToFit()
    # CardLayout
    elif context_name_includes(context, "aqt.clayout.CardLayout"):
        web_content.css.append(css_files_dir['CardLayout'])
    ## Legacy webviews
    # ResetRequired on card edit (legacy)
    elif context_name_includes(context, "aqt.main.ResetRequired"):
        web_content.css.append(css_files_dir['legacy'])
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

if attribute_exists(gui_hooks, "main_window_did_init"):
    #gui_hooks.main_window_did_init.append(redraw_toolbar)
    pass
elif attribute_exists(gui_hooks, "top_toolbar_did_init_links"):
    gui_hooks.top_toolbar_did_init_links.append(redraw_toolbar_legacy)

# Dialog window styling
def on_dialog_manager_did_open_dialog(dialog_manager: DialogManager, dialog_name: str, dialog_instance: QWidget) -> None:
    logger.debug(dialog_name)
    dialog: AnkiQt = dialog_manager._dialogs[dialog_name][1]
    # If dwmapi found and nightmode is enabled, set dark titlebar to dialog window
    set_dark_titlebar_qt(dialog, dwmapi)
    # AddCards
    if dialog_name == "AddCards":
        context: AddCards = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QAddCards'], encoding='utf-8').read())
    # Addons popup
    elif dialog_name == "AddonsDialog":
        context: AddonsDialog = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QAddonsDialog'], encoding='utf-8').read())
    # Browser
    elif dialog_name == "Browser":
        context: Browser = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QBrowser'], encoding='utf-8').read())
        pass
    # EditCurrent
    elif dialog_name == "EditCurrent":
        context: EditCurrent = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QEditCurrent'], encoding='utf-8').read())
    # FilteredDeckConfigDialog
    elif module_exists("aqt.filtered_deck") and dialog_name == "FilteredDeckConfigDialog":
        context: FilteredDeckConfigDialog = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QFilteredDeckConfigDialog'], encoding='utf-8').read())
    # Statistics / NewDeckStats
    elif dialog_name == "NewDeckStats":
        context: NewDeckStats = dialog_manager._dialogs[dialog_name][1]
        context.form.web.eval(load_custom_style_wrapper())
        context.setStyleSheet(open(css_files_dir['QNewDeckStats'], encoding='utf-8').read())
    # About
    elif dialog_name == "About":
        context: ClosableQDialog = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QAbout'], encoding='utf-8').read())
    # Preferences
    elif dialog_name == "Preferences":
        context: Preferences = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QPreferences'], encoding='utf-8').read())
    # sync_log - 这是什么？？？
    elif dialog_name == "sync_log":
        pass

if attribute_exists(gui_hooks, "dialog_manager_did_open_dialog"):
    gui_hooks.dialog_manager_did_open_dialog.append(on_dialog_manager_did_open_dialog)
else:
    ## Legacy dialog window styling
    # Implemented by monkey patching, instead of hooks :c
    # setupDialogGC is being called on almost all dialog windows, utilizing this, the
    # function is used as a type of hook to inject CSS styling on the QT instances
    def monkey_setup_dialog_gc(obj: Any) -> None:
        obj.finished.connect(lambda: mw.gcWindow(obj))
        logger.debug(obj)
        set_dark_titlebar_qt(obj, dwmapi)
        # AddCards
        if isinstance(obj, AddCards):
            obj.setStyleSheet(open(css_files_dir['QAddCards'], encoding='utf-8').read())
        # EditCurrent
        elif isinstance(obj, EditCurrent):
            obj.setStyleSheet(open(css_files_dir['QEditCurrent'], encoding='utf-8').read())
        # Statistics / DeckStats
        elif isinstance(obj, DeckStats):
            obj.setStyleSheet(open(css_files_dir['QNewDeckStats'], encoding='utf-8').read())
        # About
        elif isinstance(obj, ClosableQDialog):
            obj.setStyleSheet(open(css_files_dir['QAbout'], encoding='utf-8').read())
        # Preferences
        ## Haven't found a solution for legacy preferences yet :c
    mw.setupDialogGC = monkey_setup_dialog_gc # Should be rare enough for other addons to also patch this I hope.

    # Addons popup
    if attribute_exists(gui_hooks, "addons_dialog_will_show"):
        def on_addons_dialog_will_show(dialog: AddonsDialog) -> None:
            logger.debug(dialog)
            set_dark_titlebar_qt(dialog, dwmapi)
            dialog.setStyleSheet(open(css_files_dir['QAddonsDialog'], encoding='utf-8').read())
        gui_hooks.addons_dialog_will_show.append(on_addons_dialog_will_show)
    # Browser
    if attribute_exists(gui_hooks, "browser_will_show"):
        def on_browser_will_show(browser: Browser) -> None:
            logger.debug(browser)
            set_dark_titlebar_qt(browser, dwmapi)
            browser.setStyleSheet(open(css_files_dir['QBrowser'], encoding='utf-8').read())
        gui_hooks.browser_will_show.append(on_browser_will_show)

# Dialog updates
from .utils import dialog 

def updateTheme(_):
    global theme, themes_parsed, color_mode
    config = get_config()
    theme = config['theme']
    themes_parsed = get_theme(theme)
    color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark

## Communication through script using rarely used hook (might change to custom hooks in the future)
gui_hooks.debug_console_will_show.append(updateTheme)