import json
### Custom util functions
from .utils.modules import *
### Logger for debuging
from .utils.logger import logger

from typing import Any, List, Optional
from PyQt5.QtWidgets import QWidget
from platform import system, version, release
from ctypes import *
# import the main window object (mw) from aqt
from aqt import AnkiQt, DialogManager, mw
from aqt.theme import theme_manager, colors
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
from aqt.webview import AnkiWebView, WebContent

### Load config data here
from .config import config, write_config, get_config

## Addon compatibility fixes
# More Overview Stats 2.1 addon compatibility fix
addon_more_overview_stats_fix = config['addon_more_overview_stats']
addon_advanced_review_bottom_bar = config['addon_advanced_review_bottom_bar']

## Customization
theme = config['theme']
# Init script/file path
from .utils.css_files import css_files_dir
from .utils.themes import themes, write_theme, get_theme
logger.debug(css_files_dir)
logger.debug(themes)
themes_parsed = get_theme(theme)
color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark

dwmapi = None
## Darkmode windows titlebar thanks to miere43
def set_dark_titlebar(window, dwmapi) -> None:
    if dwmapi:
        handler_window = c_void_p(int(window.winId()))
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = c_int(19)
        DWMWA_USE_IMMERSIVE_DARK_MODE = c_int(20)
        windows_version = int(version().split('.')[2])
        attribute = DWMWA_USE_IMMERSIVE_DARK_MODE if windows_version >= 18985 else DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1
        if windows_version >= 17763 and int(release()) >= 10:
            dwmapi.DwmSetWindowAttribute(handler_window, attribute, byref(c_int(1)), c_size_t(4))
def set_dark_titlebar_qt(obj, dwmapi, fix=True) -> None:
    if dwmapi and theme_manager.get_night_mode():
        set_dark_titlebar(obj, dwmapi)
        # Trick to refresh the titlebar after dark titlebar is set
        if fix:
            obj.showFullScreen()
            obj.showNormal()
if system() == "Windows" and theme_manager.get_night_mode():
    dwmapi = WinDLL("dwmapi")
    if dwmapi:
        dwmapi.DwmSetWindowAttribute.argtypes = [c_void_p, c_int, c_void_p, c_size_t]
        dwmapi.DwmSetWindowAttribute.restype = c_int
        set_dark_titlebar(mw, dwmapi)
logger.debug(dwmapi)

### CSS injections
def load_custom_style():
    theme_colors = ""
    for color_name in themes_parsed.get("colors"):
        color = themes_parsed.get("colors").get(color_name)
        if color[3]:
            theme_colors += f"{color[3]}: {color[color_mode]};\n        "
        else:
            theme_colors += f"--{color_name.lower().replace('_','-')}: {color[color_mode]};\n        "
    custom_style = """
<style>
    :root,
    :root .isMac,
    :root .isWin,
    :root .isLin {
        %s
    }
    html {
        font-family: %s;
        font-size: %spx;
    }
</style>
    """ % (theme_colors, config["font"], config["font_size"])
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
    elif isinstance(context, ReviewerBottomBar):
        if addon_advanced_review_bottom_bar:
            web_content.body += "<script>document.getElementById('outer').classList.add('arbb');</script>"
        else:
            web_content.css.append(css_files_dir['BottomBar'])
        web_content.css.append(css_files_dir['ReviewerBottomBar'])
        # Button padding bottom
        web_content.body += "<div style='height: 9px; opacity: 0; pointer-events: none;'></div>"
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

# TopToolbar styling fix through height change by adding <br> tag
def redraw_toolbar() -> None:
    # Reload the webview content with added <br/> tag, making the bar larger in height
    mw.toolbar.web.setFixedHeight(60)
    mw.toolbar.web.eval("""
        var br = document.createElement("br");
        document.body.appendChild(br);
    """)

    if 'Qt6' in QPalette.ColorRole.__module__:
        mw.toolbar.web.eval("""
            var div = document.createElement("div");
            div.style.width = "5px";
            div.style.height = "10px";
            document.body.appendChild(div);
        """)
    # Auto adjust the height, then redraw the toolbar
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw()

def redraw_toolbar_legacy(links: List[str], _: Toolbar) -> None:
    # Utilizing the link hook, we inject <br/> tag through javascript
    inject_br = """
        <script>
            while (document.body.querySelectorAll("br").length > 1)
                document.body.querySelectorAll("br")[0].remove();
            var br = document.createElement("br");
            document.body.appendChild(br);
        </script>
    """
    mw.toolbar.web.setFixedHeight(60)
    links.append(inject_br)
    mw.toolbar.web.adjustHeightToFit()

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
        context.setStyleSheet(open(css_files_dir['QNewDeckStats'], encoding='utf-8').read())
    # About
    elif dialog_name == "About":
        context: ClosableQDialog = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QAbout'], encoding='utf-8').read())
    # Preferences
    elif dialog_name == "Preferences":
        context: Preferences = dialog_manager._dialogs[dialog_name][1]
        context.setStyleSheet(open(css_files_dir['QPreferences'], encoding='utf-8').read())
    # sync_log - kore ha nani desu???
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
        ## Haven't found a solution for preferences yet :c
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

from . import preferences