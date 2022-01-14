import os
from typing import Any, Optional
# import the main window object (mw) from aqt
from aqt import mw
from aqt import gui_hooks
# QT page views
from aqt.toolbar import TopToolbar
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar
from aqt.overview import Overview, OverviewBottomBar
from aqt.editor import Editor
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.webview import WebContent
import logging

### Load config data here
config = mw.addonManager.getConfig(__name__)

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


## Adds styling on the different contents, before the content is set
mw.addonManager.setWebExports(__name__, r"files/.*\.(css|svg|gif|png)")
addon_package = mw.addonManager.addonFromModule(__name__)
def on_webview_will_set_content(web_content: WebContent, context: Optional[Any]) -> None:
    logger.debug(context) # Logs content being loaded, find out the instance
    # Global css
    web_content.css.append(f"/_addons/{addon_package}/files/global.css")
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
    
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

# TopToolbar height change by adding <br> tag
def redrawToolbar() -> None:
    # Reload the webview content with added <br/> tag, making the bar larger in height
    mw.toolbar.web.setFixedHeight(60)
    mw.toolbar.web.eval(f"""
        const br = document.createElement("br");
        document.body.appendChild(br);
    """)
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw() # Redraw the toolbar
gui_hooks.main_window_did_init.append(redrawToolbar)