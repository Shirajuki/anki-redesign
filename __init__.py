import os
import logging
from .utils import *
from typing import Any, List, Optional
from PyQt5.QtWidgets import QWidget
from platform import system, version, release
from ctypes import *
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
from aqt.webview import AnkiWebView, WebContent, AnkiWebPage

### Load config data here
config = mw.addonManager.getConfig(__name__)

## Addon compatibility fixes
# More Overview Stats 2.1 addon compatibility fix
addon_more_overview_stats_fix = True if config['addon_more_overview_stats'].lower() == "true" else False
addon_recolor_fix = True if config['addon_recolor_fix'].lower() == "true" else False

## Customization
primary_color = config['primary_color']
link_color = config['link_color']
font = config['font']
custom_style = """
    <style>
        :root,
        :root .isMac,
        :root .isWin,
        :root .isLin {
            --primary-color: %s;
            --link-color: %s;
        }
        html {
            font-family: %s;
        }
    </style>
    """ % (primary_color, link_color, font)

### Init script/file path
mw.addonManager.setWebExports(__name__, r"files/.*\.(css|svg|gif|png)|user_files/.*\.(css|svg|gif|png)")
addon_package = mw.addonManager.addonFromModule(__name__)

this_script_dir = os.path.dirname(__file__)
files_dir = os.path.join(this_script_dir, 'files')
user_files_dir = os.path.join(this_script_dir, 'user_files')
css_files_dir = {
  'BottomBar': f"/_addons/{addon_package}/files/BottomBar.css",
  'CardLayout': f"/_addons/{addon_package}/files/CardLayout.css",
  'DeckBrowser': f"/_addons/{addon_package}/files/DeckBrowser.css",
  'Editor': f"/_addons/{addon_package}/files/Editor.css",
  'global': f"/_addons/{addon_package}/files/global.css",
  'legacy': f"/_addons/{addon_package}/files/legacy.css",
  'Overview': f"/_addons/{addon_package}/files/Overview.css", 
  'QAbout': os.path.join(files_dir, 'QAbout.css'),
  'QAddCards': os.path.join(files_dir, 'QAddCards.css'),
  'QAddonsDialog': os.path.join(files_dir, 'QAddonsDialog.css'),
  'QBrowser': os.path.join(files_dir, 'QBrowser.css'),
  'QFilteredDeckConfigDialog': os.path.join(files_dir, 'QFilteredDeckConfigDialog.css'),
  'QEditCurrent': os.path.join(files_dir, 'QEditCurrent.css'),
  'QNewDeckStats': os.path.join(files_dir, 'QNewDeckStats.css'),
  'QPreferences': os.path.join(files_dir, 'QPreferences.css'),
  'Reviewer': f"/_addons/{addon_package}/files/Reviewer.css",
  'ReviewerBottomBar': f"/_addons/{addon_package}/files/ReviewerBottomBar.css",
  'TopToolbar': f"/_addons/{addon_package}/files/TopToolbar.css",
}
# Replace pathing for user customised styled files
for file in os.listdir(user_files_dir):
  file = file.replace(".css", "")
  if css_files_dir.get(file, "") != "":
    if file.startswith("Q"):
        css_files_dir[file] = os.path.join(user_files_dir, file+'.css')
    else:
        css_files_dir[file] = f"/_addons/{addon_package}/user_files/{file}.css"

### Logger for debuging
# declare an empty logger class
class EmptyLogger():
    def debug(self, *_):
        return None

# init logger
if 'ANKI_REDESIGN_DEBUG_LOGGING' in os.environ:
    filename =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_files", "test.log")
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
    datefmt='%Y%m%d-%H:%M:%S',
    filename=filename, 
    level=logging.DEBUG)
    logger = logging.getLogger('anki-redesign')
    logger.setLevel(logging.DEBUG)
    logger.debug("Initialized anki")
else:
    logger = EmptyLogger()
logger.debug(css_files_dir)

dwmapi = None
## Darkmode windows titlebar thanks to miere43
# https://stackoverflow.com/questions/57124243/winforms-dark-title-bar-on-windows-10
# https://github.com/miere43/anki-dark-titlebar/blob/main/__init__.py
def set_dark_titlebar(window, dwmapi) -> None:
    handler_window = c_void_p(int(window.winId()))
    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = c_int(19)
    DWMWA_USE_IMMERSIVE_DARK_MODE = c_int(20)
    windows_version = int(version().split('.')[2])
    attribute = DWMWA_USE_IMMERSIVE_DARK_MODE if windows_version >= 18985 else DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1
    if windows_version >= 17763 and int(release()) >= 10:
        dwmapi.DwmSetWindowAttribute(handler_window, attribute, byref(c_int(1)), c_size_t(4))
def set_dark_titlebar_qt(obj, fix=True) -> None:
    if dwmapi and theme_manager.get_night_mode():
        set_dark_titlebar(obj, dwmapi)
        # Trick to refresh the titlebar after dark titlebar is set
        if fix:
            obj.showFullScreen()
            obj.showNormal()
if system() == "Windows" and theme_manager.get_night_mode():
    dwmapi = WinDLL("dwmapi")
    dwmapi.DwmSetWindowAttribute.argtypes = [c_void_p, c_int, c_void_p, c_size_t]
    dwmapi.DwmSetWindowAttribute.restype = c_int
    set_dark_titlebar(mw, dwmapi)
logger.debug(dwmapi)

### CSS injections
## Adds styling on the different webview contents, before the content is set
def on_webview_will_set_content(web_content: WebContent, context: Optional[Any]) -> None:
    logger.debug(context) # Logs content being loaded, find out the instance
    web_content.css.append(css_files_dir['global']) # Global css
    web_content.head += custom_style # Custom styling
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
        web_content.css.append(css_files_dir['BottomBar'])
        web_content.css.append(css_files_dir['ReviewerBottomBar'])
        # Button padding bottom
        web_content.body += "<div style='height: 9px; opacity: 0; pointer-events: none;'></div>"
        web_content.body += "<div id='padFix' style='height: 30px; opacity: 0; pointer-events: none;'><script>const e = document.getElementById('padFix');e.parentElement.removeChild(e);</script></div>"
        mw.bottomWeb.adjustHeightToFit();
    # CardLayout
    elif context_name_includes(context, "aqt.clayout.CardLayout"):
        web_content.css.append(css_files_dir['CardLayout'])
    ## Legacy webviews
    # ResetRequired on card edit (legacy)
    elif context_name_includes(context, "aqt.main.ResetRequired"):
        web_content.css.append(css_files_dir['legacy'])
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

# TopToolbar styling fix through height change by adding <br> tag
def redrawToolbar() -> None:
    # Reload the webview content with added <br/> tag, making the bar larger in height
    mw.toolbar.web.setFixedHeight(60)
    mw.toolbar.web.eval("""
        const br = document.createElement("br");
        document.body.appendChild(br);
    """)
    # Auto adjust the height, then redraw the toolbar
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw()
def redrawToolbarLegacy(links: List[str], _: Toolbar) -> None:
    # Utilizing the link hook, we inject <br/> tag through javascript
    inject_br = """
        <script>
            const br = document.createElement("br");
            document.body.appendChild(br);
        </script>
    """
    mw.toolbar.web.setFixedHeight(60)
    links.append(inject_br)
if attribute_exists(gui_hooks, "main_window_did_init"):
    gui_hooks.main_window_did_init.append(redrawToolbar)
elif attribute_exists(gui_hooks, "top_toolbar_did_init_links"):
    gui_hooks.top_toolbar_did_init_links.append(redrawToolbarLegacy)

# Dialog window styling
def on_dialog_manager_did_open_dialog(dialog_manager: DialogManager, dialog_name: str, dialog_instance: QWidget):
    logger.debug(dialog_name)
    dialog: AnkiQt = dialog_manager._dialogs[dialog_name][1]
    # If dwmapi found and nightmode is enabled, set dark titlebar to dialog window
    set_dark_titlebar_qt(dialog)
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
    # Sad monkey patch, instead of hooks :c
    # setupDialogGC is being called on almost all dialog windows, utilizing this, the
    # function is used as a type of hook to inject CSS styling on the QT instances
    def monkeySetupDialogGC(obj: Any) -> None:
        obj.finished.connect(lambda: mw.gcWindow(obj))
        logger.debug(obj)
        set_dark_titlebar_qt(obj)
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
        ## Haven't found a solution for preferences yet
    mw.setupDialogGC = monkeySetupDialogGC # Should be rare enough for other addons to also patch this I hope.

    # Addons popup
    if attribute_exists(gui_hooks, "addons_dialog_will_show"):
        def on_addons_dialog_will_show(dialog: AddonsDialog):
            logger.debug(dialog)
            set_dark_titlebar_qt(dialog)
            dialog.setStyleSheet(open(css_files_dir['QAddonsDialog'], encoding='utf-8').read())
        gui_hooks.addons_dialog_will_show.append(on_addons_dialog_will_show)
    # Browser
    if attribute_exists(gui_hooks, "browser_will_show"):
        def on_browser_will_show(browser: Browser):
            logger.debug(browser)
            set_dark_titlebar_qt(browser)
            browser.setStyleSheet(open(css_files_dir['QBrowser'], encoding='utf-8').read())
        gui_hooks.browser_will_show.append(on_browser_will_show)

"""
TBA
from aqt.qt import QMainWindow, QDialog
keys = ["about","addcards","addfield","addmodel","addonconf","addons","browser","browserdisp","browseropts","changemap","changemodel","clayout_top","customstudy","dconf","debug","filtered_deck","editaddon","editcurrent","edithtml","emptycards","exporting","fields","finddupes","findreplace","getaddons","importing","main","modelopts","models","preferences","preview","profiles","progress","reposition","setgroup","setlang","stats","studydeck","synclog","taglimit","template"]

for key in keys:
    module = "aqt.forms."+key
    if module_exists(module):
        mod = __import__(module, fromlist=['Ui_Dialog'])
        if hasattr(mod,"Ui_Dialog"):
            try:
                Ui_Dialog = getattr(mod, 'Ui_Dialog')
                Ui_Dialog = Ui_Dialog()
                ui_old = Ui_Dialog.setupUi
                logger.debug(Ui_Dialog)
            except:
                pass
        # about
        elif hasattr(mod,"Ui_About"):
            pass
        # changemap
        elif hasattr(mod,"Ui_ChangeMap"):
            pass
        # clayout_top, preview, template
        elif hasattr(mod,"Ui_Form"):
            pass
        # exporting
        elif hasattr(mod,"Ui_ExportDialog"):
            pass
        # importing
        elif hasattr(mod,"Ui_ImportDialog"):
            pass
        # preferences
        elif hasattr(mod,"Ui_Preferences"):
            pass
        # profiles
        elif hasattr(mod,"Ui_MainWindow"):
            pass

from aqt.forms.browser import Ui_Dialog
ui_old = Ui_Dialog.setupUi
def Ui_Dialog_new(self: Ui_Dialog, Dialog, *args, **kwargs) -> None:
    logger.debug(self)
    logger.debug(Dialog)
    return ui_old(self, Dialog, *args, *kwargs)
Ui_Dialog.setupUi = Ui_Dialog_new

QMainWindow_show_old = None
def QMainWindow_show_new(self: QMainWindow, *args, **kwargs) -> None:
    set_dark_titlebar_qt(self, False)
    logger.debug(self.windowTitle())
    logger.debug(self.form)
    logger.debug(self)
    return QMainWindow_show_old(self, *args, *kwargs)
QMainWindow_show_old = QMainWindow.show
QMainWindow.show = QMainWindow_show_new

QDialog_show_old = None
def QDialog_show_new(self: QDialog, *args, **kwargs) -> None:
    set_dark_titlebar_qt(self, False)
    logger.debug(self.windowTitle())
    logger.debug(self.form)
    logger.debug(self)
    #set_dark_titlebar_qt(self)
    return QDialog_show_old(self, *args, **kwargs)
QDialog_show_old = QDialog.show
QDialog.show = QDialog_show_new
"""