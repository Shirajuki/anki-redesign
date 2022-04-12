import os
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
from .config import config, write_config

## Addon compatibility fixes
# More Overview Stats 2.1 addon compatibility fix
addon_more_overview_stats_fix = config['addon_more_overview_stats']
# ReColor addon compatibility fix
addon_recolor_fix = config['addon_recolor']

## Customization
primary_color = config['primary_color']
link_color = config['link_color']
font = config['font']
font_size = config['font_size']
theme = config['theme']

### Init script/file path
from .utils.css_files import css_files_dir
from .utils.themes import themes, write_theme
logger.debug(css_files_dir)
logger.debug(themes)
themes_parsed = json.loads(open(themes[theme], encoding='utf-8').read())

dwmapi = None
## Darkmode windows titlebar thanks to miere43
# https://stackoverflow.com/questions/57124243/winforms-dark-title-bar-on-windows-10
# https://github.com/miere43/anki-dark-titlebar/blob/main/__init__.py
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
    color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark
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
        --primary-color: %s;
        --link-color: %s;
        %s
    }
    html {
        font-family: %s;
        font-size: %spx;
    }
</style>
    """ % (primary_color, link_color, theme_colors, font, font_size)
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
def redraw_toolbar() -> None:
    # Reload the webview content with added <br/> tag, making the bar larger in height
    mw.toolbar.web.setFixedHeight(60)
    mw.toolbar.web.eval("""
        var br = document.createElement("br");
        document.body.appendChild(br);
    """)
    # Auto adjust the height, then redraw the toolbar
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw()

def redraw_toolbar_legacy(links: List[str], _: Toolbar) -> None:
    # Utilizing the link hook, we inject <br/> tag through javascript
    inject_br = """
        <script>
            var br = document.createElement("br");
            document.body.appendChild(br);
        </script>
    """
    mw.toolbar.web.setFixedHeight(60)
    links.append(inject_br)

if attribute_exists(gui_hooks, "main_window_did_init"):
    gui_hooks.main_window_did_init.append(redraw_toolbar)
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
    # Sad monkey patch, instead of hooks :c
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
        ## Haven't found a solution for preferences yet
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
"""
## CONFIG
from typing import List, Tuple

from aqt import mw, gui_hooks
from aqt.editor import EditorWebView

from aqt.qt import *
from .config import config
from aqt.utils import openLink
from aqt.webview import AnkiWebView

class ConfigDialog(QDialog):
    def __init__(self, parent: QWidget, *args, **kwargs):
        super().__init__(parent=parent or mw, *args, **kwargs)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(f'Anki-redesign configuration')
        self.setSizePolicy(self.make_size_policy())
        self.setMinimumSize(420, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        set_dark_titlebar_qt(self, dwmapi, fix=False)

        # Color/theme
        ## Loads theme color
        self.theme_colors = themes_parsed.get("colors")
        self.color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark
        self.updates = []
        self.theme_general = ["TEXT_FG", "WINDOW_BG", "FRAME_BG", "BUTTON_BG", "BORDER", "MEDIUM_BORDER", "FAINT_BORDER", "HIGHLIGHT_BG", "HIGHLIGHT_FG" , "LINK", "DISABLED"]
        self.theme_decks = ["CURRENT_DECK", "NEW_COUNT", "LEARN_COUNT", "REVIEW_COUNT", "ZERO_COUNT"]
        self.theme_browse = ["BURIED_FG", "SUSPENDED_FG", "FLAG1_BG", "FLAG1_FG", "FLAG2_BG", "FLAG2_FG", "FLAG3_BG", "FLAG3_FG", "FLAG4_BG", "FLAG4_FG", "FLAG5_BG", "FLAG5_FG", "FLAG6_BG", "FLAG6_FG", "FLAG7_BG", "FLAG7_FG"]

        # Root layout
        self.root_layout = QVBoxLayout(self)
        # Main layout
        self.layout = QVBoxLayout()
        ## Initialize tab screen
        self.tabs = QTabWidget(objectName="tabs")
        self.tabs.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.tab_general = QWidget(objectName="general")
        self.tab_general.setLayout(self.create_color_picker_layout(self.theme_general))
        self.tab_decks = QWidget(objectName="decks")        
        self.tab_decks.setLayout(self.create_color_picker_layout(self.theme_decks))
        self.tab_browse = QWidget(objectName="browse")        
        self.tab_browse.setLayout(self.create_color_picker_layout(self.theme_browse))
        self.tab_extra = QWidget(objectName="extra")        
        self.tab_extra.setLayout(self.create_color_picker_layout([]))
        
        self.tab_settings = QWidget(objectName="settings")
        self.settings_layout = QFormLayout()
        self.theme_label = QLabel("Theme:")
        self.theme_label.setStyleSheet('QLabel { font-size: 14px; font-weight: bold }')
        self.settings_layout.addRow(self.theme_label)
        for key in themes:
            self.radio = self.radio_button(key)
            self.settings_layout.addRow(key, self.radio)
        self.settings_layout.addRow(QLabel())

        self.font_label = QLabel("Font:")
        self.font_label.setStyleSheet('QLabel { font-size: 14px; font-weight: bold }')
        self.settings_layout.addRow(self.font_label)
        self.interface_font = QFontComboBox()
        self.interface_font.setFixedWidth(200)
        self.interface_font.setCurrentFont(QFont(font))
        self.settings_layout.addRow(self.interface_font)

        self.size_label = QLabel("Font Size: ")
        self.size_label.setFixedWidth(100)
        self.font_size = QSpinBox()
        self.font_size.setFixedWidth(200)
        self.font_size.setValue(font_size)
        self.font_size.setSuffix("px")
        self.settings_layout.addRow(self.font_size)

        self.tab_settings.setLayout(self.settings_layout)

        # Window BG fix
        window_bg = "rgba(0, 0, 0, 47)"
        #window_bg = self.theme_colors.get("WINDOW_BG")[self.color_mode]
        self.tab_settings.setStyleSheet('QWidget#settings { background-color: %s; border: 1px solid %s; }' % (window_bg, window_bg))
        self.tab_general.setStyleSheet('QWidget#general { background-color: %s; border: 1px solid %s; }' % (window_bg, window_bg))
        self.tab_decks.setStyleSheet('QWidget#decks { background-color: %s; border: 1px solid %s; }' % (window_bg, window_bg))
        self.tab_browse.setStyleSheet('QWidget#browse { background-color: %s; border: 1px solid %s; }' % (window_bg, window_bg))
        self.tab_extra.setStyleSheet('QWidget#extra { background-color: %s; border: 1px solid %s; }' % (window_bg, window_bg))
        self.tabs.setStyleSheet('QWidget#tabs { background-color: %s; border: 1px solid %s; }' % (self.theme_colors.get("WINDOW_BG")[self.color_mode], window_bg))

        ## Add tabs
        self.tabs.resize(300,200)
        self.tabs.addTab(self.tab_settings,"Settings")
        self.tabs.addTab(self.tab_general,"General")
        self.tabs.addTab(self.tab_decks,"Decks")
        self.tabs.addTab(self.tab_browse,"Browse")
        self.tabs.addTab(self.tab_extra,"Extra")

        ## Add tabs to widget
        self.layout.addWidget(self.tabs)

        self.root_layout.addLayout(self.layout)
        self.root_layout.addLayout(self.make_button_box())
        self.setLayout(self.root_layout)
        self.show()

    def update(self) -> None:
        global themes_parsed
        themes_parsed = json.loads(open(themes[theme], encoding='utf-8').read())
        self.theme_colors = themes_parsed.get("colors")
        for update in self.updates:
            update()

    def radio_button(self, key: str) -> QRadioButton:
        radio = QRadioButton()

        def update() -> None:
            if theme == key:
                radio.setChecked(True)
            elif radio.isChecked():
                radio.setChecked(False)

        def toggle(checked) -> None:
            global theme
            if checked:
                theme = key
            self.update()
    
        self.updates.append(update)
        radio.toggled.connect(lambda checked: toggle(checked))
        update()
        return radio 

    def color_input(self, key: str) -> QPushButton:
        button = QPushButton()
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setFixedWidth(25)
        button.setFixedHeight(25)

        color_dialog = QColorDialog(self)

        def set_color(rgb: str) -> None:
            # Check for valid color
            color = QColor()
            color.setNamedColor(rgb)
            if not color.isValid():
                raise InvalidConfigValueError(key, "rgb hex color string", rgb)
            # Update color
            color_dialog.setCurrentColor(color)
            button.setStyleSheet('QPushButton{ background-color: "%s"; border: none; border-radius: 2px}' % rgb)

        def update() -> None:
            rgb = self.theme_colors.get(key)[self.color_mode]
            set_color(rgb)

        def save(color: QColor) -> None:
            rgb = color.name(QColor.NameFormat.HexRgb)
            self.theme_colors[key][self.color_mode] = rgb
            set_color(rgb)

        self.updates.append(update)
        color_dialog.colorSelected.connect(lambda color: save(color))
        button.clicked.connect(lambda _: color_dialog.exec())
        return button

    def create_color_picker_layout(self, colors):
        layout = QFormLayout()
        for key in colors:
            self.test = self.color_input(key)
            layout.addRow(self.theme_colors.get(key)[0], self.test)
        return layout

    def make_button_box(self) -> QWidget:
        def cancel():
            button = QPushButton('Cancel')
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            qconnect(button.clicked, self.accept)
            return button
        def save():
            button = QPushButton('Save')
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.setDefault(True)
            button.setShortcut("Ctrl+Return")
            button.clicked.connect(lambda _: self.save())
            return button

        button_box = QHBoxLayout()
        button_box.addStretch()
        button_box.addWidget(cancel())
        button_box.addWidget(save())
        return button_box

    def make_size_policy(self) -> QSizePolicy:
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        return size_policy

    def save(self) -> None:
        # Save font
        global config
        config["font"] = self.interface_font.currentFont().family()
        config["font_size"] = self.font_size.value()
        config["theme"] = theme
        write_config(config)

        # Update theme
        colors = {}
        for color_name in self.theme_colors:
            colors[color_name] = self.theme_colors.get(color_name)[self.color_mode]
        logger.debug(colors)
        #write_theme(themes[theme], self.theme_colors)

        # Apply theme
        self.apply_theme(colors)

        # Refresh all windows
        if mw.state == "review":
            mw.reviewer._initWeb()
            if mw.reviewer.state == "question":
                mw.reviewer._showQuestion()
            else:
                mw.reviewer._showAnswer()
        elif mw.state == "overview":
            mw.overview.refresh()
        elif mw.state == "deckBrowser":
            mw.deckBrowser.refresh()
            mw.reset() 
        self.hide()

    def apply_theme(self, colors) -> None:
        color_map = {
            QPalette.ColorRole.WindowText: "TEXT_FG",
            QPalette.ColorRole.ToolTipText: "TEXT_FG",
            QPalette.ColorRole.Text: "TEXT_FG",
            QPalette.ColorRole.ButtonText: "TEXT_FG",
            QPalette.ColorRole.HighlightedText: "HIGHLIGHT_FG",
            QPalette.ColorRole.Window: "WINDOW_BG",
            QPalette.ColorRole.AlternateBase: "WINDOW_BG",
            QPalette.ColorRole.Button: "BUTTON_BG",
            QPalette.ColorRole.Base: "FRAME_BG",
            QPalette.ColorRole.ToolTipBase: "FRAME_BG",
            QPalette.ColorRole.Link: "LINK",
        }
        disabled_roles = [QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.HighlightedText]

        # Load palette
        palette = QPalette()
        for role in color_map:
            conf_key = color_map[role]
            palette.setColor(role, QColor(colors[conf_key]))

        hlbg = QColor(colors["HIGHLIGHT_BG"])
        if theme_manager.night_mode:
            hlbg.setAlpha(64)
        palette.setColor(QPalette.ColorRole.Highlight, hlbg)

        for role in disabled_roles:
            palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(colors["DISABLED"]))

        if theme_manager.night_mode:
            palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["TEXT_FG"]))

        # Update palette
        mw.app.setPalette(palette)
        theme_manager.default_palette = palette
        theme_manager._apply_style(mw.app)

        # Update webview bg
        AnkiWebView._getWindowColor = lambda *args: QColor(colors["WINDOW_BG"])
        AnkiWebView.get_window_bg_color = lambda *args: QColor(colors["WINDOW_BG"])

# Create menu actions
def create_menu_action(parent: QWidget, dialog_class: QDialog, dialog_name: str) -> QAction:
    def open_dialog():
        dialog = dialog_class(mw)
        return dialog.exec_()

    action = QAction(dialog_name, parent)
    qconnect(action.triggered, open_dialog)
    return action

# Load in the Anki-redesign menu
if not hasattr(mw.form, 'anki_redesign'):
    mw.form.anki_redesign = QMenu("&CAnki-redesignDEV", mw)
    mw.form.menubar.insertMenu(mw.form.menuHelp.menuAction(), mw.form.anki_redesign)

    mw.form.anki_redesign.addAction(create_menu_action(mw.form.anki_redesign, ConfigDialog, "&Config"))
    #mw.form.anki_redesign.addSeparator()
