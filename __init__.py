import os
from typing import Any, Optional
from dataclasses import dataclass
# import the main window object (mw) from aqt
from aqt import mw
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



### Adding menu items
# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
def testFunction() -> None:
    # get the number of cards in the current collection, which is stored in
    # the main window
    cardCount = mw.col.cardCount()
    # show a message box
    showInfo("Card count: %d" % cardCount)

# create a new menu item, "test"
action = QAction("test", mw)
# set it to call testFunction when it's clicked
qconnect(action.triggered, testFunction)
# and add it to the tools menu
mw.form.menuTools.addAction(action)

customFont = "default"

@dataclass
class DeckBrowserContent:
    """Stores sections of HTML content that the deck browser will be
    populated with.
    Attributes:
        tree {str} -- HTML of the deck tree section
        stats {str} -- HTML of the stats section
    """

    tree: str
    stats: str
def __renderPage(self, offset: int) -> None:
        content = DeckBrowserContent(
            tree=self._renderDeckTree(self._dueTree),
            stats=self._renderStats(),
        )
        gui_hooks.deck_browser_will_render_content(self, content)
        self.web.stdHtml(
            self._v1_upgrade_message() + self._body % content.__dict__,
            css=["css/deckbrowser.css", "css/testing.css"],
            js=[
                "js/vendor/jquery.min.js",
                "js/vendor/jquery-ui.min.js",
                "js/deckbrowser.js",
            ],
            context=self,
        )
        print(self)
        self._drawButtons()
        if offset is not None:
            self._scrollToOffset(offset)
        gui_hooks.deck_browser_did_render(self)
DeckBrowser.__renderPage = __renderPage

mw.addonManager.setWebExports(__name__, r"files/.*\.(css|svg|gif|png)")
addon_package = mw.addonManager.addonFromModule(__name__)
def on_webview_will_set_content(web_content: aqt.webview.WebContent, context: Optional[Any]) -> None:
    if isinstance(context, DeckBrowser):
        web_content.css.append(f"/_addons/{addon_package}/files/test.css")
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

def deckbrowserRenderStats(self, _old):
    add = """<br><img class="peko" src='/_addons/{}/files/test.gif'>""".format(addon_package)
    return _old(self) + add
DeckBrowser._renderStats = wrap(DeckBrowser._renderStats, deckbrowserRenderStats, "around")