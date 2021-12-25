import os
from typing import Any, Optional
# import the main window object (mw) from aqt
from aqt import mw
from aqt.toolbar import TopToolbar
# import the "show info" tool from utils.py
from aqt.utils import showInfo, qconnect
# import all of the Qt GUI library
from aqt.qt import QAction
# Deckbrowser
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar
from aqt.overview import Overview, OverviewBottomBar, OverviewContent
from aqt import gui_hooks
from anki.hooks import wrap
import aqt
import logging

from aqt.webview import AnkiWebView
config = mw.addonManager.getConfig(__name__)
print("var is", config['myvar'])

### Adding menu items
# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
def countCards() -> None:
    # get the number of cards in the current collection, which is stored in
    # the main window
    cardCount = mw.col.cardCount()
    # show a message box
    showInfo("Card count: %d" % cardCount)

# create a new menu item, "test"
action = QAction("Count total cards", mw)
# set it to call testFunction when it's clicked
qconnect(action.triggered, countCards)
# and add it to the tools menu
mw.form.menuTools.addAction(action)

### LOGGER
filename =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_files", "test.log")
logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
    datefmt='%Y%m%d-%H:%M:%S',
    filename=filename, 
    level=logging.DEBUG)
# init logger
logger = logging.getLogger('anki-redesign')
logger.setLevel(logging.DEBUG)
logger.debug("Initialized anki")

# Adds styling on the different contents, before the content is set
mw.addonManager.setWebExports(__name__, r"files/.*\.(css|svg|gif|png)")
addon_package = mw.addonManager.addonFromModule(__name__)
def on_webview_will_set_content(web_content: aqt.webview.WebContent, context: Optional[Any]) -> None:
    logger.debug(context) # Logs content being loaded, find out the instance
    if isinstance(context, DeckBrowser):
        web_content.css.append(f"/_addons/{addon_package}/files/DeckBrowser.css")
    elif isinstance(context, TopToolbar):
        web_content.css.append(f"/_addons/{addon_package}/files/TopToolbar.css")
    elif isinstance(context, DeckBrowserBottomBar) or isinstance(context, OverviewBottomBar):
        web_content.css.append(f"/_addons/{addon_package}/files/BottomBar.css")
    elif isinstance(context, Overview):
        web_content.css.append(f"/_addons/{addon_package}/files/Overview.css")
        mw.overview.web.eval(f"""
            const link = document.createElement("link");
            link.rel = 'stylesheet';
            link.href = {"/_addons/"+addon_package+"/files/Overview.css"};
            document.body.appendChild(link);
        """)
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

def on_overview_will_render_content(overview, content):
    content.table += "\n<div>my html</div>"
    logger.debug(content)
gui_hooks.overview_will_render_content.append(on_overview_will_render_content)
# TopToolbar height change by adding <br> tag
def redrawToolbar() -> None:
    # Reload the webview content with added body
    mw.toolbar.web.setFixedHeight(60)
    mw.toolbar.web.stdHtml(
        mw.toolbar._body % mw.toolbar._centerLinks()+"<br>",
        css=["css/toolbar.css"],
        js=["js/webview.js", "js/vendor/jquery.min.js", "js/toolbar.js"],
        context=TopToolbar(mw.toolbar),
    )
    mw.toolbar.web.set_bridge_command(mw.toolbar._linkHandler, TopToolbar(mw.toolbar))
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw() # Redraw the toolbar
gui_hooks.main_window_did_init.append(redrawToolbar)

### Monkey patching
## Adds overview css
#def appendOverviewCss(self, _old):
#    add = f"<link href='/_addons/{addon_package}/files/Overview.css'>"
#    return _old(self) + add
#Overview._renderPage = wrap(Overview._renderPage, renderPage, "around")
## Adds peko gif
def deckbrowserRenderStats(self, _old):
    add = f"<br><img class='peko' src='/_addons/{addon_package}/files/test.gif'>"
    return _old(self) + add
DeckBrowser._renderStats = wrap(DeckBrowser._renderStats, deckbrowserRenderStats, "around")
