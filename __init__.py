import os
from .utils import *
from typing import Any, List, Optional
from PyQt5.QtWidgets import QWidget
# import the main window object (mw) from aqt
from aqt import DialogManager, mw
from aqt import gui_hooks
from aqt.addcards import AddCards
# Browser import legacy check (2.1.22)
if module_exists("aqt.browser.browser"):
    from aqt.browser.browser import Browser
else:
    from aqt.browser import Browser
# QT page views
from aqt.toolbar import Toolbar, TopToolbar
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar
from aqt.overview import Overview, OverviewBottomBar
from aqt.editor import Editor
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.webview import AnkiWebView, WebContent
import logging

### Load config data here
config = mw.addonManager.getConfig(__name__)
## Addon compatibility fixes
# More Overview Stats 2.1 addon compatibility fix
addon_more_overview_stats_fix = config['addon_more_overview_stats'].lower()
## Customization
primary_color = config['primary_color']
custom_style = """
    <style>
        :root,
        :root .isMac,
        :root .isWin,
        :root .isLin {
            --primary-color: %s;
        }
    </style>
    """ % (primary_color)

### Init script/file path
this_script_dir = os.path.dirname(__file__)
files_dir = os.path.join(this_script_dir, 'files')
addcards_css_path = os.path.join(files_dir, 'AddCards.css')

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


## Adds styling on the different webview contents, before the content is set
mw.addonManager.setWebExports(__name__, r"files/.*\.(css|svg|gif|png)")
addon_package = mw.addonManager.addonFromModule(__name__)
def on_webview_will_set_content(web_content: WebContent, context: Optional[Any]) -> None:
    logger.debug(context) # Logs content being loaded, find out the instance
    # Global css
    web_content.css.append(f"/_addons/{addon_package}/files/global.css")
    web_content.head += custom_style
    # Deckbrowser
    if isinstance(context, DeckBrowser):
        web_content.css.append(f"/_addons/{addon_package}/files/DeckBrowser.css")
    # TopToolbar
    elif isinstance(context, TopToolbar):
        web_content.css.append(f"/_addons/{addon_package}/files/TopToolbar.css")
    # BottomToolbar (Buttons)
    elif isinstance(context, DeckBrowserBottomBar) or isinstance(context, OverviewBottomBar):
        web_content.css.append(f"/_addons/{addon_package}/files/BottomBar.css")
    # Overview
    elif isinstance(context, Overview):
        if addon_more_overview_stats_fix == "true":
            web_content.head += "<style>center > table tr:first-of-type {display: table-row; flex-direction: unset;}</style>"
        web_content.css.append(f"/_addons/{addon_package}/files/Overview.css")
    # Editor
    elif isinstance(context, Editor):
        web_content.css.append(f"/_addons/{addon_package}/files/Editor.css")
    # Reviewer
    elif isinstance(context, Reviewer):
        web_content.css.append(f"/_addons/{addon_package}/files/Reviewer.css")
    elif isinstance(context, ReviewerBottomBar):
        web_content.css.append(f"/_addons/{addon_package}/files/BottomBar.css")
        web_content.css.append(f"/_addons/{addon_package}/files/ReviewerBottomBar.css")
        # Button padding bottom
        web_content.body += "<div style='height: 9px; opacity: 0; pointer-events: none;'></div>"
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

# TopToolbar height change by adding <br> tag
def redrawToolbar() -> None:
    # Reload the webview content with added <br/> tag, making the bar larger in height
    mw.toolbar.web.setFixedHeight(60)
    mw.toolbar.web.eval("""
        const br = document.createElement("br");
        document.body.appendChild(br);
    """)
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw() # Redraw the toolbar
def redrawToolbarLegacy(links: List[str], _: Toolbar) -> None:
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
# TODO: Add CSS styling to different dialog windows
def on_dialog_manager_did_open_dialog(dialog_manager: DialogManager, dialog_name: str, dialog_instance: QWidget):
    logger.debug(dialog_name)
    # AddCards
    if dialog_name == "AddCards":
        #context: AddCards = dialog_manager._dialogs[dialog_name][1]
        #logger.debug(context)
        #logger.debug(context.styleSheet())
        #context.setStyleSheet(open(addcards_css_path, encoding='utf-8').read())
        pass
    # Addons popup
    elif dialog_name == "AddonsDialog":
        pass
    # Browser
    elif dialog_name == "Browser":
        pass
    # EditCurrent
    elif dialog_name == "EditCurrent":
        pass
    # FilteredDeckConfigDialog
    elif dialog_name == "FilteredDeckConfigDialog":
        pass
    # DeckStats
    elif dialog_name == "DeckStats":
        pass
    # Statistics / NewDeckStats
    elif dialog_name == "NewDeckStats":
        pass
    # About
    elif dialog_name == "About":
        pass
    # Preferences
    elif dialog_name == "Preferences":
        pass
    # sync_log
    elif dialog_name == "sync_log":
        pass
if attribute_exists(gui_hooks, "dialog_manager_did_open_dialog"):
    gui_hooks.dialog_manager_did_open_dialog.append(on_dialog_manager_did_open_dialog)

# TODO: Add legacy hooks *_will_show for each legacy Dialog windows
# Browser
#def on_browser_will_show(browser: Browser):
#    logger.debug(browser)
#gui_hooks.browser_will_show.append(on_browser_will_show)