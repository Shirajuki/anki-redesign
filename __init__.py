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

## CONFIG DIALOG
from aqt import mw, gui_hooks
from aqt.qt import *
from .config import config
from aqt.utils import showInfo
from aqt.webview import AnkiWebView

class ThemeEditor(QDialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent=parent or mw, *args, **kwargs)
        self.config_editor = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(f'Anki-redesign Advanced Editor')
        self.setSizePolicy(self.make_size_policy())
        self.setMinimumSize(420, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        set_dark_titlebar_qt(self, dwmapi, fix=False)
        # Root layout
        self.root_layout = QVBoxLayout(self)
        # Main layout
        self.layout = QVBoxLayout()
        self.textedit = QTextEdit()
        themes_plaintext = open(themes[theme], encoding='utf-8').read()
        self.textedit.setPlainText(themes_plaintext)
        self.layout.addWidget(self.textedit)
        self.root_layout.addLayout(self.layout)
        self.root_layout.addLayout(self.make_button_box())

    def save_edit(self) -> None:
        themes_parsed = json.loads(self.textedit.toPlainText())
        write_theme(themes[theme], themes_parsed)
        self.config_editor.update()
        self.accept()

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
            button.clicked.connect(lambda _: self.save_edit())
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

class ConfigDialog(QDialog):
    def __init__(self, parent: QWidget, *args, **kwargs):
        super().__init__(parent=parent or mw, *args, **kwargs)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(f'Anki-redesign Configuration')
        self.setSizePolicy(self.make_size_policy())
        self.setMinimumSize(420, 580)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        set_dark_titlebar_qt(self, dwmapi, fix=False)

        # Color/theme
        ## Loads theme color
        self.theme_colors = themes_parsed.get("colors")
        self.updates = []
        self.theme_general = ["TEXT_FG", "WINDOW_BG", "FRAME_BG", "BUTTON_BG", "TOOLTIP_BG", "BORDER", "MEDIUM_BORDER", "FAINT_BORDER", "HIGHLIGHT_BG", "HIGHLIGHT_FG" , "LINK", "DISABLED", "SLIGHTLY_GREY_TEXT", "PRIMARY_COLOR"]
        self.theme_decks = ["CURRENT_DECK", "NEW_COUNT", "LEARN_COUNT", "REVIEW_COUNT", "ZERO_COUNT"]
        self.theme_browse = ["BURIED_FG", "SUSPENDED_FG", "MARKED_BG", "FLAG1_BG", "FLAG1_FG", "FLAG2_BG", "FLAG2_FG", "FLAG3_BG", "FLAG3_FG", "FLAG4_BG", "FLAG4_FG", "FLAG5_BG", "FLAG5_FG", "FLAG6_BG", "FLAG6_FG", "FLAG7_BG", "FLAG7_FG"]
        self.theme_extra = []

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
        self.tab_extra.setLayout(self.create_color_picker_layout(self.theme_extra))
        
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
        self.interface_font.setCurrentFont(QFont(config["font"]))
        self.settings_layout.addRow(self.interface_font)

        self.font_size = QSpinBox()
        self.font_size.setFixedWidth(200)
        self.font_size.setValue(config["font_size"])
        self.font_size.setSuffix("px")
        self.settings_layout.addRow(self.font_size)

        self.settings_layout.addRow(QLabel())

        self.fix_label = QLabel("Addon-Compatibility Fixes: ")
        self.fix_label.setStyleSheet('QLabel { font-size: 14px; font-weight: bold }')
        self.settings_layout.addRow(self.fix_label)
        self.addon_more_overview_stats_check = self.checkbox("addon_more_overview_stats")
        self.settings_layout.addRow("More Overview Stats 21", self.addon_more_overview_stats_check)

        self.tab_settings.setLayout(self.settings_layout)

        ## Add tabs
        self.tabs.resize(300,200)
        self.tabs.addTab(self.tab_settings,"Settings")
        self.tabs.addTab(self.tab_general,"General")
        self.tabs.addTab(self.tab_decks,"Decks")
        self.tabs.addTab(self.tab_browse,"Browse")
        #self.tabs.addTab(self.tab_extra,"Extra")

        ## Add tabs to widget
        self.layout.addWidget(self.tabs)

        self.root_layout.addLayout(self.layout)
        self.root_layout.addLayout(self.make_button_box())
        self.setLayout(self.root_layout)
        self.show()

    def update(self) -> None:
        global themes_parsed
        themes_parsed = get_theme(theme)
        self.theme_colors = themes_parsed.get("colors")
        for update in self.updates:
            update()

    def checkbox(self, key: str) -> QCheckBox:
        checkbox = QCheckBox()

        def update() -> None:
            value = config[key]
            checkbox.setChecked(value)

        self.updates.append(update)
        update()
        return checkbox

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
                return
            # Update color
            color_dialog.setCurrentColor(color)
            button.setStyleSheet('QPushButton{ background-color: "%s"; border: none; border-radius: 2px}' % rgb)

        def update() -> None:
            rgb = self.theme_colors.get(key)[color_mode]
            set_color(rgb)

        def save(color: QColor) -> None:
            rgb = color.name(QColor.NameFormat.HexRgb)
            self.theme_colors[key][color_mode] = rgb
            set_color(rgb)

        self.updates.append(update)
        color_dialog.colorSelected.connect(lambda color: save(color))
        button.clicked.connect(lambda _: color_dialog.exec())
        return button

    def create_color_picker_layout(self, colors) -> None:
        layout = QFormLayout()
        for key in colors:
            self.test = self.color_input(key)
            layout.addRow(self.theme_colors.get(key)[0], self.test)
        return layout
    
    def theme_file_editor(self) -> None:   
        diag = ThemeEditor(self)
        diag.show()

    def make_button_box(self) -> QWidget:
        def advanced():
            button = QPushButton('Advanced')
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            qconnect(button.clicked, self.theme_file_editor)
            return button
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
        button_box.addWidget(advanced())
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
        # Save settings and update config
        global config
        config["font"] = self.interface_font.currentFont().family()
        config["font_size"] = self.font_size.value()
        config['addon_more_overview_stats'] = self.addon_more_overview_stats_check.isChecked()
        config["theme"] = theme
        write_config(config)
        config = get_config()

        # Write and update theme
        themes_parsed["colors"] = self.theme_colors
        write_theme(themes[theme], themes_parsed)
        update_theme()

        # Reload view, show info and hide dialog
        mw.reset()
        # ShowInfo for both new and legacy support
        showInfo(_("Changes will take effect when you restart Anki."))
        #showInfo(tr.preferences_changes_will_take_effect_when_you())
        self.accept()

def check_legacy_colors() -> None:
    try:
        _ = colors.items()
    except:
        return False
    return True

def update_theme() -> None:
        themes_parsed = get_theme(theme)
        theme_colors = themes_parsed.get("colors")
        # Apply theme on colors
        
        # 2.1.22 & 2.1.26
        # dict_items([('day-text-fg', 'black'), ('day-window-bg', '#ececec'), ('day-frame-bg', 'white'), ('day-border', '#aaa'), ('day-faint-border', '#e7e7e7'), ('day-link', '#00a'), ('day-review-count', '#0a0'), ('day-new-count', '#00a'), ('day-learn-count', '#C35617'), ('day-zero-count', '#ddd'), ('day-slightly-grey-text', '#333'), ('day-highlight-bg', '#77ccff'), ('day-highlight-fg', 'black'), ('day-disabled', '#777'), ('day-flag1-bg', '#ffaaaa'), ('day-flag2-bg', '#ffb347'), ('day-flag3-bg', '#82E0AA'), ('day-flag4-bg', '#85C1E9'), ('day-suspended-bg', '#FFFFB2'), ('day-marked-bg', '#cce'), ('night-text-fg', 'white'), ('night-window-bg', '#2f2f31'), ('night-frame-bg', '#3a3a3a'), ('night-border', '#777'), ('night-faint-border', '#29292B'), ('night-link', '#77ccff'), ('night-review-count', '#5CcC00'), ('night-new-count', '#77ccff'), ('night-learn-count', '#FF935B'), ('night-zero-count', '#444'), ('night-slightly-grey-text', '#ccc'), ('night-highlight-bg', '#77ccff'), ('night-highlight-fg', 'white'), ('night-disabled', '#777'), ('night-flag1-bg', '#aa5555'), ('night-flag2-bg', '#aa6337'), ('night-flag3-bg', '#33a055'), ('night-flag4-bg', '#3581a9'), ('night-suspended-bg', '#aaaa33'), ('night-marked-bg', '#77c'), ('fusion-button-gradient-start', '#555555'), ('fusion-button-gradient-end', '#656565'), ('fusion-button-outline', '#222222'), ('fusion-button-hover-bg', '#656565'), ('fusion-button-border', '#646464'), ('fusion-button-base-bg', '#454545')])
        # 2.1.49
        # {'__name__': 'aqt.colors', '__doc__': None, '__package__': 'aqt', '__loader__': <pyimod03_importers.FrozenImporter object at 0x00000287A7CDF160>, '__spec__': ModuleSpec(name='aqt.colors', loader=<pyimod03_importers.FrozenImporter object at 0x00000287A7CDF160>, origin='C:\\Program Files\\Anki\\aqt\\colors.pyc'), '__file__': 'C:\\Program Files\\Anki\\aqt\\colors.pyc', '__cached__': 'C:\\Program Files\\Anki\\aqt\\colors.pyc', '__builtins__': {'__name__': 'builtins', '__doc__': "Built-in functions, exceptions, and other objects.\n\nNoteworthy: None is the `nil' object; Ellipsis represents `...' in slices.", '__package__': '', '__loader__': <class '_frozen_importlib.BuiltinImporter'>, '__spec__': ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>), '__build_class__': <built-in function __build_class__>, '__import__': <built-in function __import__>, 'abs': <built-in function abs>, 'all': <built-in function all>, 'any': <built-in function any>, 'ascii': <built-in function ascii>, 'bin': <built-in function bin>, 'breakpoint': <built-in function breakpoint>, 'callable': <built-in function callable>, 'chr': <built-in function chr>, 'compile': <built-in function compile>, 'delattr': <built-in function delattr>, 'dir': <built-in function dir>, 'divmod': <built-in function divmod>, 'eval': <built-in function eval>, 'exec': <built-in function exec>, 'format': <built-in function format>, 'getattr': <built-in function getattr>, 'globals': <built-in function globals>, 'hasattr': <built-in function hasattr>, 'hash': <built-in function hash>, 'hex': <built-in function hex>, 'id': <built-in function id>, 'input': <built-in function input>, 'isinstance': <built-in function isinstance>, 'issubclass': <built-in function issubclass>, 'iter': <built-in function iter>, 'len': <built-in function len>, 'locals': <built-in function locals>, 'max': <built-in function max>, 'min': <built-in function min>, 'next': <built-in function next>, 'oct': <built-in function oct>, 'ord': <built-in function ord>, 'pow': <built-in function pow>, 'print': <built-in function print>, 'repr': <built-in function repr>, 'round': <built-in function round>, 'setattr': <built-in function setattr>, 'sorted': <built-in function sorted>, 'sum': <built-in function sum>, 'vars': <built-in function vars>, 'None': None, 'Ellipsis': Ellipsis, 'NotImplemented': NotImplemented, 'False': False, 'True': True, 'bool': <class 'bool'>, 'memoryview': <class 'memoryview'>, 'bytearray': <class 'bytearray'>, 'bytes': <class 'bytes'>, 'classmethod': <class 'classmethod'>, 'complex': <class 'complex'>, 'dict': <class 'dict'>, 'enumerate': <class 'enumerate'>, 'filter': <class 'filter'>, 'float': <class 'float'>, 'frozenset': <class 'frozenset'>, 'property': <class 'property'>, 'int': <class 'int'>, 'list': <class 'list'>, 'map': <class 'map'>, 'object': <class 'object'>, 'range': <class 'range'>, 'reversed': <class 'reversed'>, 'set': <class 'set'>, 'slice': <class 'slice'>, 'staticmethod': <class 'staticmethod'>, 'str': <class 'str'>, 'super': <class 'super'>, 'tuple': <class 'tuple'>, 'type': <class 'type'>, 'zip': <class 'zip'>, '__debug__': True, 'BaseException': <class 'BaseException'>, 'Exception': <class 'Exception'>, 'TypeError': <class 'TypeError'>, 'StopAsyncIteration': <class 'StopAsyncIteration'>, 'StopIteration': <class 'StopIteration'>, 'GeneratorExit': <class 'GeneratorExit'>, 'SystemExit': <class 'SystemExit'>, 'KeyboardInterrupt': <class 'KeyboardInterrupt'>, 'ImportError': <class 'ImportError'>, 'ModuleNotFoundError': <class 'ModuleNotFoundError'>, 'OSError': <class 'OSError'>, 'EnvironmentError': <class 'OSError'>, 'IOError': <class 'OSError'>, 'WindowsError': <class 'OSError'>, 'EOFError': <class 'EOFError'>, 'RuntimeError': <class 'RuntimeError'>, 'RecursionError': <class 'RecursionError'>, 'NotImplementedError': <class 'NotImplementedError'>, 'NameError': <class 'NameError'>, 'UnboundLocalError': <class 'UnboundLocalError'>, 'AttributeError': <class 'AttributeError'>, 'SyntaxError': <class 'SyntaxError'>, 'IndentationError': <class 'IndentationError'>, 'TabError': <class 'TabError'>, 'LookupError': <class 'LookupError'>, 'IndexError': <class 'IndexError'>, 'KeyError': <class 'KeyError'>, 'ValueError': <class 'ValueError'>, 'UnicodeError': <class 'UnicodeError'>, 'UnicodeEncodeError': <class 'UnicodeEncodeError'>, 'UnicodeDecodeError': <class 'UnicodeDecodeError'>, 'UnicodeTranslateError': <class 'UnicodeTranslateError'>, 'AssertionError': <class 'AssertionError'>, 'ArithmeticError': <class 'ArithmeticError'>, 'FloatingPointError': <class 'FloatingPointError'>, 'OverflowError': <class 'OverflowError'>, 'ZeroDivisionError': <class 'ZeroDivisionError'>, 'SystemError': <class 'SystemError'>, 'ReferenceError': <class 'ReferenceError'>, 'MemoryError': <class 'MemoryError'>, 'BufferError': <class 'BufferError'>, 'Warning': <class 'Warning'>, 'UserWarning': <class 'UserWarning'>, 'DeprecationWarning': <class 'DeprecationWarning'>, 'PendingDeprecationWarning': <class 'PendingDeprecationWarning'>, 'SyntaxWarning': <class 'SyntaxWarning'>, 'RuntimeWarning': <class 'RuntimeWarning'>, 'FutureWarning': <class 'FutureWarning'>, 'ImportWarning': <class 'ImportWarning'>, 'UnicodeWarning': <class 'UnicodeWarning'>, 'BytesWarning': <class 'BytesWarning'>, 'ResourceWarning': <class 'ResourceWarning'>, 'ConnectionError': <class 'ConnectionError'>, 'BlockingIOError': <class 'BlockingIOError'>, 'BrokenPipeError': <class 'BrokenPipeError'>, 'ChildProcessError': <class 'ChildProcessError'>, 'ConnectionAbortedError': <class 'ConnectionAbortedError'>, 'ConnectionRefusedError': <class 'ConnectionRefusedError'>, 'ConnectionResetError': <class 'ConnectionResetError'>, 'FileExistsError': <class 'FileExistsError'>, 'FileNotFoundError': <class 'FileNotFoundError'>, 'IsADirectoryError': <class 'IsADirectoryError'>, 'NotADirectoryError': <class 'NotADirectoryError'>, 'InterruptedError': <class 'InterruptedError'>, 'PermissionError': <class 'PermissionError'>, 'ProcessLookupError': <class 'ProcessLookupError'>, 'TimeoutError': <class 'TimeoutError'>, 'open': <built-in function open>, '_': <function setupLangAndBackend.<locals>.fn__ at 0x00000287AC3633A0>, 'ngettext': <function setupLangAndBackend.<locals>.fn_ngettext at 0x00000287AC363430>}, 'TEXT_FG': ('black', 'white'), 'WINDOW_BG': ('#ececec', '#2f2f31'), 'FRAME_BG': ('white', '#3a3a3a'), 'BORDER': ('#aaa', '#777'), 'MEDIUM_BORDER': ('#b6b6b6', '#444'), 'FAINT_BORDER': ('#e7e7e7', '#29292b'), 'LINK': ('#00a', '#77ccff'), 'REVIEW_COUNT': ('#0a0', '#5ccc00'), 'NEW_COUNT': ('#00a', '#77ccff'), 'LEARN_COUNT': ('#c35617', '#ff935b'), 'ZERO_COUNT': ('#ddd', '#444'), 'SLIGHTLY_GREY_TEXT': ('#333', '#ccc'), 'HIGHLIGHT_BG': ('#77ccff', '#77ccff'), 'HIGHLIGHT_FG': ('black', 'white'), 'DISABLED': ('#777', '#777'), 'FLAG1_FG': ('#e25252', '#ff7b7b'), 'FLAG2_FG': ('#ffb347', '#f5aa41'), 'FLAG3_FG': ('#54c414', '#86ce5d'), 'FLAG4_FG': ('#578cff', '#6f9dff'), 'FLAG5_FG': ('#ff82ee', '#f097e4'), 'FLAG6_FG': ('#00d1b5', '#5ccfca'), 'FLAG7_FG': ('#9649dd', '#9f63d3'), 'FLAG1_BG': ('#ff9b9b', '#aa5555'), 'FLAG2_BG': ('#ffb347', '#ac653a'), 'FLAG3_BG': ('#93e066', '#559238'), 'FLAG4_BG': ('#9dbcff', '#506aa3'), 'FLAG5_BG': ('#f5a8eb', '#975d8f'), 'FLAG6_BG': ('#7edbd7', '#399185'), 'FLAG7_BG': ('#cca3f1', '#624b77'), 'BURIED_FG': ('#aaaa33', '#777733'), 'SUSPENDED_FG': ('#dd0', '#ffffb2'), 'SUSPENDED_BG': ('#ffffb2', '#aaaa33'), 'MARKED_BG': ('#cce', '#77c'), 'TOOLTIP_BG': ('#fcfcfc', '#272727')}
        # 2.1.50
        # {'__name__': 'aqt.colors', '__doc__': None, '__package__': 'aqt', '__loader__': <pyimod03_importers.FrozenImporter object at 0x00000287A7CDF160>, '__spec__': ModuleSpec(name='aqt.colors', loader=<pyimod03_importers.FrozenImporter object at 0x00000287A7CDF160>, origin='C:\\Program Files\\Anki\\aqt\\colors.pyc'), '__file__': 'C:\\Program Files\\Anki\\aqt\\colors.pyc', '__cached__': 'C:\\Program Files\\Anki\\aqt\\colors.pyc', '__builtins__': {'__name__': 'builtins', '__doc__': "Built-in functions, exceptions, and other objects.\n\nNoteworthy: None is the `nil' object; Ellipsis represents `...' in slices.", '__package__': '', '__loader__': <class '_frozen_importlib.BuiltinImporter'>, '__spec__': ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>), '__build_class__': <built-in function __build_class__>, '__import__': <built-in function __import__>, 'abs': <built-in function abs>, 'all': <built-in function all>, 'any': <built-in function any>, 'ascii': <built-in function ascii>, 'bin': <built-in function bin>, 'breakpoint': <built-in function breakpoint>, 'callable': <built-in function callable>, 'chr': <built-in function chr>, 'compile': <built-in function compile>, 'delattr': <built-in function delattr>, 'dir': <built-in function dir>, 'divmod': <built-in function divmod>, 'eval': <built-in function eval>, 'exec': <built-in function exec>, 'format': <built-in function format>, 'getattr': <built-in function getattr>, 'globals': <built-in function globals>, 'hasattr': <built-in function hasattr>, 'hash': <built-in function hash>, 'hex': <built-in function hex>, 'id': <built-in function id>, 'input': <built-in function input>, 'isinstance': <built-in function isinstance>, 'issubclass': <built-in function issubclass>, 'iter': <built-in function iter>, 'len': <built-in function len>, 'locals': <built-in function locals>, 'max': <built-in function max>, 'min': <built-in function min>, 'next': <built-in function next>, 'oct': <built-in function oct>, 'ord': <built-in function ord>, 'pow': <built-in function pow>, 'print': <built-in function print>, 'repr': <built-in function repr>, 'round': <built-in function round>, 'setattr': <built-in function setattr>, 'sorted': <built-in function sorted>, 'sum': <built-in function sum>, 'vars': <built-in function vars>, 'None': None, 'Ellipsis': Ellipsis, 'NotImplemented': NotImplemented, 'False': False, 'True': True, 'bool': <class 'bool'>, 'memoryview': <class 'memoryview'>, 'bytearray': <class 'bytearray'>, 'bytes': <class 'bytes'>, 'classmethod': <class 'classmethod'>, 'complex': <class 'complex'>, 'dict': <class 'dict'>, 'enumerate': <class 'enumerate'>, 'filter': <class 'filter'>, 'float': <class 'float'>, 'frozenset': <class 'frozenset'>, 'property': <class 'property'>, 'int': <class 'int'>, 'list': <class 'list'>, 'map': <class 'map'>, 'object': <class 'object'>, 'range': <class 'range'>, 'reversed': <class 'reversed'>, 'set': <class 'set'>, 'slice': <class 'slice'>, 'staticmethod': <class 'staticmethod'>, 'str': <class 'str'>, 'super': <class 'super'>, 'tuple': <class 'tuple'>, 'type': <class 'type'>, 'zip': <class 'zip'>, '__debug__': True, 'BaseException': <class 'BaseException'>, 'Exception': <class 'Exception'>, 'TypeError': <class 'TypeError'>, 'StopAsyncIteration': <class 'StopAsyncIteration'>, 'StopIteration': <class 'StopIteration'>, 'GeneratorExit': <class 'GeneratorExit'>, 'SystemExit': <class 'SystemExit'>, 'KeyboardInterrupt': <class 'KeyboardInterrupt'>, 'ImportError': <class 'ImportError'>, 'ModuleNotFoundError': <class 'ModuleNotFoundError'>, 'OSError': <class 'OSError'>, 'EnvironmentError': <class 'OSError'>, 'IOError': <class 'OSError'>, 'WindowsError': <class 'OSError'>, 'EOFError': <class 'EOFError'>, 'RuntimeError': <class 'RuntimeError'>, 'RecursionError': <class 'RecursionError'>, 'NotImplementedError': <class 'NotImplementedError'>, 'NameError': <class 'NameError'>, 'UnboundLocalError': <class 'UnboundLocalError'>, 'AttributeError': <class 'AttributeError'>, 'SyntaxError': <class 'SyntaxError'>, 'IndentationError': <class 'IndentationError'>, 'TabError': <class 'TabError'>, 'LookupError': <class 'LookupError'>, 'IndexError': <class 'IndexError'>, 'KeyError': <class 'KeyError'>, 'ValueError': <class 'ValueError'>, 'UnicodeError': <class 'UnicodeError'>, 'UnicodeEncodeError': <class 'UnicodeEncodeError'>, 'UnicodeDecodeError': <class 'UnicodeDecodeError'>, 'UnicodeTranslateError': <class 'UnicodeTranslateError'>, 'AssertionError': <class 'AssertionError'>, 'ArithmeticError': <class 'ArithmeticError'>, 'FloatingPointError': <class 'FloatingPointError'>, 'OverflowError': <class 'OverflowError'>, 'ZeroDivisionError': <class 'ZeroDivisionError'>, 'SystemError': <class 'SystemError'>, 'ReferenceError': <class 'ReferenceError'>, 'MemoryError': <class 'MemoryError'>, 'BufferError': <class 'BufferError'>, 'Warning': <class 'Warning'>, 'UserWarning': <class 'UserWarning'>, 'DeprecationWarning': <class 'DeprecationWarning'>, 'PendingDeprecationWarning': <class 'PendingDeprecationWarning'>, 'SyntaxWarning': <class 'SyntaxWarning'>, 'RuntimeWarning': <class 'RuntimeWarning'>, 'FutureWarning': <class 'FutureWarning'>, 'ImportWarning': <class 'ImportWarning'>, 'UnicodeWarning': <class 'UnicodeWarning'>, 'BytesWarning': <class 'BytesWarning'>, 'ResourceWarning': <class 'ResourceWarning'>, 'ConnectionError': <class 'ConnectionError'>, 'BlockingIOError': <class 'BlockingIOError'>, 'BrokenPipeError': <class 'BrokenPipeError'>, 'ChildProcessError': <class 'ChildProcessError'>, 'ConnectionAbortedError': <class 'ConnectionAbortedError'>, 'ConnectionRefusedError': <class 'ConnectionRefusedError'>, 'ConnectionResetError': <class 'ConnectionResetError'>, 'FileExistsError': <class 'FileExistsError'>, 'FileNotFoundError': <class 'FileNotFoundError'>, 'IsADirectoryError': <class 'IsADirectoryError'>, 'NotADirectoryError': <class 'NotADirectoryError'>, 'InterruptedError': <class 'InterruptedError'>, 'PermissionError': <class 'PermissionError'>, 'ProcessLookupError': <class 'ProcessLookupError'>, 'TimeoutError': <class 'TimeoutError'>, 'open': <built-in function open>, '_': <function setupLangAndBackend.<locals>.fn__ at 0x00000287AC3633A0>, 'ngettext': <function setupLangAndBackend.<locals>.fn_ngettext at 0x00000287AC363430>}, 'TEXT_FG': ('black', 'white'), 'WINDOW_BG': ('#ececec', '#2f2f31'), 'FRAME_BG': ('white', '#3a3a3a'), 'BORDER': ('#aaa', '#777'), 'MEDIUM_BORDER': ('#b6b6b6', '#444'), 'FAINT_BORDER': ('#e7e7e7', '#29292b'), 'LINK': ('#00a', '#77ccff'), 'REVIEW_COUNT': ('#0a0', '#5ccc00'), 'NEW_COUNT': ('#00a', '#77ccff'), 'LEARN_COUNT': ('#c35617', '#ff935b'), 'ZERO_COUNT': ('#ddd', '#444'), 'SLIGHTLY_GREY_TEXT': ('#333', '#ccc'), 'HIGHLIGHT_BG': ('#77ccff', '#77ccff'), 'HIGHLIGHT_FG': ('black', 'white'), 'DISABLED': ('#777', '#777'), 'FLAG1_FG': ('#e25252', '#ff7b7b'), 'FLAG2_FG': ('#ffb347', '#f5aa41'), 'FLAG3_FG': ('#54c414', '#86ce5d'), 'FLAG4_FG': ('#578cff', '#6f9dff'), 'FLAG5_FG': ('#ff82ee', '#f097e4'), 'FLAG6_FG': ('#00d1b5', '#5ccfca'), 'FLAG7_FG': ('#9649dd', '#9f63d3'), 'FLAG1_BG': ('#ff9b9b', '#aa5555'), 'FLAG2_BG': ('#ffb347', '#ac653a'), 'FLAG3_BG': ('#93e066', '#559238'), 'FLAG4_BG': ('#9dbcff', '#506aa3'), 'FLAG5_BG': ('#f5a8eb', '#975d8f'), 'FLAG6_BG': ('#7edbd7', '#399185'), 'FLAG7_BG': ('#cca3f1', '#624b77'), 'BURIED_FG': ('#aaaa33', '#777733'), 'SUSPENDED_FG': ('#dd0', '#ffffb2'), 'SUSPENDED_BG': ('#ffffb2', '#aaaa33'), 'MARKED_BG': ('#cce', '#77c'), 'TOOLTIP_BG': ('#fcfcfc', '#272727')}
        ncolors = {}
        # Legacy color check
        legacy = check_legacy_colors()
        for color_name in theme_colors:
            c = theme_colors.get(color_name)
            ncolors[color_name] = c[color_mode]
            if legacy:
               colors[f"day{c[3].replace('--','-')}"] = c[1]
               colors[f"night{c[3].replace('--','-')}"] = c[2]
               # Potentially add fusion fixes too?
            else:
                if getattr(colors, color_name, False):
                    setattr(colors, color_name, (c[1], c[2]))
        # Apply theme on palette
        apply_theme(ncolors)

def apply_theme(colors) -> None:
    # Load palette
    palette = QPalette()
    # QT mappings
    logger.debug(QPalette.ColorRole.__dict__)
    # {'_generate_next_value_': <function Enum._generate_next_value_ at 0x0000022B73C25F70>, '__doc__': 'An enumeration.', '__module__': 'PyQt6.QtGui', '_member_names_': ['WindowText', 'Button', 'Light', 'Midlight', 'Dark', 'Mid', 'Text', 'BrightText', 'ButtonText', 'Base', 'Window', 'Shadow', 'Highlight', 'HighlightedText', 'Link', 'LinkVisited', 'AlternateBase', 'ToolTipBase', 'ToolTipText', 'PlaceholderText', 'NoRole', 'NColorRoles'], '_member_map_': {'WindowText': <ColorRole.WindowText: 0>, 'Button': <ColorRole.Button: 1>, 'Light': <ColorRole.Light: 2>, 'Midlight': <ColorRole.Midlight: 3>, 'Dark': <ColorRole.Dark: 4>, 'Mid': <ColorRole.Mid: 5>, 'Text': <ColorRole.Text: 6>, 'BrightText': <ColorRole.BrightText: 7>, 'ButtonText': <ColorRole.ButtonText: 8>, 'Base': <ColorRole.Base: 9>, 'Window': <ColorRole.Window: 10>, 'Shadow': <ColorRole.Shadow: 11>, 'Highlight': <ColorRole.Highlight: 12>, 'HighlightedText': <ColorRole.HighlightedText: 13>, 'Link': <ColorRole.Link: 14>, 'LinkVisited': <ColorRole.LinkVisited: 15>, 'AlternateBase': <ColorRole.AlternateBase: 16>, 'ToolTipBase': <ColorRole.ToolTipBase: 18>, 'ToolTipText': <ColorRole.ToolTipText: 19>, 'PlaceholderText': <ColorRole.PlaceholderText: 20>, 'NoRole': <ColorRole.NoRole: 17>, 'NColorRoles': <ColorRole.NColorRoles: 21>}, '_member_type_': <class 'object'>, '_value2member_map_': {0: <ColorRole.WindowText: 0>, 1: <ColorRole.Button: 1>, 2: <ColorRole.Light: 2>, 3: <ColorRole.Midlight: 3>, 4: <ColorRole.Dark: 4>, 5: <ColorRole.Mid: 5>, 6: <ColorRole.Text: 6>, 7: <ColorRole.BrightText: 7>, 8: <ColorRole.ButtonText: 8>, 9: <ColorRole.Base: 9>, 10: <ColorRole.Window: 10>, 11: <ColorRole.Shadow: 11>, 12: <ColorRole.Highlight: 12>, 13: <ColorRole.HighlightedText: 13>, 14: <ColorRole.Link: 14>, 15: <ColorRole.LinkVisited: 15>, 16: <ColorRole.AlternateBase: 16>, 18: <ColorRole.ToolTipBase: 18>, 19: <ColorRole.ToolTipText: 19>, 20: <ColorRole.PlaceholderText: 20>, 17: <ColorRole.NoRole: 17>, 21: <ColorRole.NColorRoles: 21>}, 'WindowText': <ColorRole.WindowText: 0>, 'Button': <ColorRole.Button: 1>, 'Light': <ColorRole.Light: 2>, 'Midlight': <ColorRole.Midlight: 3>, 'Dark': <ColorRole.Dark: 4>, 'Mid': <ColorRole.Mid: 5>, 'Text': <ColorRole.Text: 6>, 'BrightText': <ColorRole.BrightText: 7>, 'ButtonText': <ColorRole.ButtonText: 8>, 'Base': <ColorRole.Base: 9>, 'Window': <ColorRole.Window: 10>, 'Shadow': <ColorRole.Shadow: 11>, 'Highlight': <ColorRole.Highlight: 12>, 'HighlightedText': <ColorRole.HighlightedText: 13>, 'Link': <ColorRole.Link: 14>, 'LinkVisited': <ColorRole.LinkVisited: 15>, 'AlternateBase': <ColorRole.AlternateBase: 16>, 'ToolTipBase': <ColorRole.ToolTipBase: 18>, 'ToolTipText': <ColorRole.ToolTipText: 19>, 'PlaceholderText': <ColorRole.PlaceholderText: 20>, 'NoRole': <ColorRole.NoRole: 17>, 'NColorRoles': <ColorRole.NColorRoles: 21>, '__new__': <function Enum.__new__ at 0x0000022B73C25EE0>, '__sip__': <capsule object NULL at 0x0000022B75407210>}
    color_map = {
        QPalette.ColorRole.Window: "WINDOW_BG",
        QPalette.ColorRole.WindowText: "TEXT_FG",
        QPalette.ColorRole.Base: "FRAME_BG",
        QPalette.ColorRole.AlternateBase: "WINDOW_BG",
        QPalette.ColorRole.ToolTipBase: "TOOLTIP_BG",
        QPalette.ColorRole.ToolTipText: "TEXT_FG",
        QPalette.ColorRole.Text: "TEXT_FG",
        QPalette.ColorRole.Button: "BUTTON_BG",
        QPalette.ColorRole.ButtonText: "TEXT_FG",
        QPalette.ColorRole.BrightText: "HIGHLIGHT_FG",
        QPalette.ColorRole.HighlightedText: "HIGHLIGHT_FG",
        QPalette.ColorRole.Link: "LINK",
        QPalette.ColorRole.NoRole: "WINDOW_BG",
    }
    for color_role in color_map:
        palette.setColor(color_role, QColor(colors[color_map[color_role]]))

    placeholder_text = QColor(colors["TEXT_FG"])
    placeholder_text.setAlpha(200)
    palette.setColor(QPalette.ColorRole.PlaceholderText, placeholder_text)

    highlight_bg = QColor(colors["HIGHLIGHT_BG"])
    if theme_manager.night_mode:
        highlight_bg.setAlpha(70)
        palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["TEXT_FG"]))
    palette.setColor(QPalette.ColorRole.Highlight, highlight_bg)

    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colors["DISABLED"]))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(colors["DISABLED"]))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(colors["DISABLED"]))

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
    mw.form.anki_redesign = QMenu("&Anki-redesign", mw)
    mw.form.menubar.insertMenu(mw.form.menuHelp.menuAction(), mw.form.anki_redesign)

    mw.form.anki_redesign.addAction(create_menu_action(mw.form.anki_redesign, ConfigDialog, "&Config"))
    update_theme()
    #mw.form.anki_redesign.addSeparator()
