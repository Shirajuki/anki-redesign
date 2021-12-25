import os
from typing import Any, Optional
from dataclasses import dataclass
# import the main window object (mw) from aqt
from aqt import mw
from aqt.toolbar import Toolbar, TopToolbar
# import the "show info" tool from utils.py
from aqt.utils import showInfo, qconnect
# import all of the Qt GUI library
from aqt.qt import *
# Deckbrowser
from aqt.deckbrowser import DeckBrowser
from aqt import gui_hooks
from anki.hooks import wrap
from anki.cards import Card
import aqt
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
import logging
filename =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_files", "test.log")
logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
    datefmt='%Y%m%d-%H:%M:%S',
    filename=filename, 
    level=logging.DEBUG)
logger = logging.getLogger('anki-redesign')
logger.setLevel(logging.DEBUG)
logger.debug("Initialized anki")

mw.addonManager.setWebExports(__name__, r"files/.*\.(css|svg|gif|png)")
addon_package = mw.addonManager.addonFromModule(__name__)
def on_webview_will_set_content(web_content: aqt.webview.WebContent, context: Optional[Any]) -> None:
    if isinstance(context, DeckBrowser):
        web_content.css.append(f"/_addons/{addon_package}/files/test.css")
    elif isinstance(context, TopToolbar):
        web_content.css.append(f"/_addons/{addon_package}/files/test.css")
    logger.debug(context)
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

def deckbrowserRenderStats(self, _old):
    add = """<br><img class="peko" src='/_addons/{}/files/test.gif'>""".format(addon_package)
    return _old(self) + add
DeckBrowser._renderStats = wrap(DeckBrowser._renderStats, deckbrowserRenderStats, "around")