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
    """ % (theme_colors_light, theme_colors_dark, config["font"], config["font_size"])
    return custom_style

def load_custom_style_wrapper():
    custom_style = f"""
    var style = document.createElement("style");
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
        while (document.body.querySelectorAll("br.toolbarFix").length > 1)
            document.body.querySelectorAll("br.toolbarFix")[0].remove();
        var br = document.createElement("br");
        br.className = "toolbarFix";
        document.body.appendChild(br);
    """)

    if 'Qt6' in QPalette.ColorRole.__module__:
        mw.toolbar.web.eval("""
            while (document.body.querySelectorAll("div.toolbarFix").length > 1)
                document.body.querySelectorAll("div.toolbarFix")[0].remove();
            var div = document.createElement("div");
            div.style.width = "5px";
            div.style.height = "10px";
            div.className = "toolbarFix";
            document.body.appendChild(div);
        """)
    # Auto adjust the height, then redraw the toolbar
    mw.toolbar.web.adjustHeightToFit()
    mw.toolbar.redraw()

def redraw_toolbar_legacy(links: List[str], _: Toolbar) -> None:
    # Utilizing the link hook, we inject <br/> tag through javascript
    inject_br = """
        <script>
            while (document.body.querySelectorAll("br.toolbarFix").length > 1)
                document.body.querySelectorAll("br.toolbarFix")[0].remove();
            var br = document.createElement("br");
            br.className = "toolbarFix";
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
            dialog.form.web.eval(load_custom_style_wrapper())
            dialog.setStyleSheet(open(css_files_dir['QAddonsDialog'], encoding='utf-8').read())
        gui_hooks.addons_dialog_will_show.append(on_addons_dialog_will_show)
    # Browser
    if attribute_exists(gui_hooks, "browser_will_show"):
        def on_browser_will_show(browser: Browser) -> None:
            logger.debug(browser)
            set_dark_titlebar_qt(browser, dwmapi)
            browser.form.web.eval(load_custom_style_wrapper())
            browser.setStyleSheet(open(css_files_dir['QBrowser'], encoding='utf-8').read())
        gui_hooks.browser_will_show.append(on_browser_will_show)

## CONFIG DIALOG
from aqt import mw, gui_hooks
from aqt.qt import *
from .config import config
from aqt.utils import showInfo
from aqt.webview import AnkiWebView

class AnkiRedesignThemeEditor(QDialog):
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

class AnkiRedesignConfigDialog(QDialog):
    def __init__(self, parent: QWidget, *args, **kwargs):
        super().__init__(parent=parent or mw, *args, **kwargs)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(f'Anki-redesign configuration')
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

        self.fix_label = QLabel("Addon-compatibility fixes: ")
        self.fix_label.setStyleSheet('QLabel { font-size: 14px; font-weight: bold }')
        self.settings_layout.addRow(self.fix_label)
        self.addon_more_overview_stats_check = self.checkbox("addon_more_overview_stats")
        self.settings_layout.addRow("More Overview Stats 21", self.addon_more_overview_stats_check)
        self.addon_advanced_review_bottom_bar_check = self.checkbox("addon_advanced_review_bottom_bar")
        self.settings_layout.addRow("Advanced Review Bottom Bar", self.addon_advanced_review_bottom_bar_check)

        self.tab_settings.setLayout(self.settings_layout)

        ## Add tabs
        self.tabs.resize(300,200)
        self.tabs.addTab(self.tab_settings,"Settings")
        self.tabs.addTab(self.tab_general,"General")
        self.tabs.addTab(self.tab_decks,"Decks")
        self.tabs.addTab(self.tab_browse,"Browse")
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
        diag = AnkiRedesignThemeEditor(self)
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
        global config, color_mode
        config["font"] = self.interface_font.currentFont().family()
        config["font_size"] = self.font_size.value()
        config['addon_more_overview_stats'] = self.addon_more_overview_stats_check.isChecked()
        config['addon_advanced_review_bottom_bar'] = self.addon_advanced_review_bottom_bar_check.isChecked()
        config["theme"] = theme
        write_config(config)
        config = get_config()

        # Write and update theme
        color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark
        themes_parsed["colors"] = self.theme_colors
        write_theme(themes[theme], themes_parsed)
        update_theme()

        # ShowInfo for both new and legacy support
        showInfo(_("Some changes will take effect when you restart Anki."))
        self.accept()

def check_legacy_colors() -> None:
    try:
        _ = colors.items()
    except:
        return False
    return True

def refresh_all_windows() -> None:
    # Redraw top toolbar
    mw.toolbar.draw()
    if attribute_exists(gui_hooks, "top_toolbar_did_init_links"):
        gui_hooks.top_toolbar_did_init_links.append(lambda a,b: [redraw_toolbar_legacy(a,b), gui_hooks.top_toolbar_did_init_links.remove(print)])
    
    # Redraw main body
    if mw.state == "review":
        mw.reviewer._initWeb()
        # Legacy check
        if getattr(mw.reviewer, "_redraw_current_card", False):
            mw.reviewer._redraw_current_card()
            mw.fade_in_webview()
    elif mw.state == "overview":
        mw.overview.refresh()
    elif mw.state == "deckBrowser":
        mw.deckBrowser.show()
    
    # Redraw toolbar
    if attribute_exists(gui_hooks, "top_toolbar_did_init_links"):
        gui_hooks.top_toolbar_did_init_links.remove(redraw_toolbar)

def update_theme() -> None:
    themes_parsed = get_theme(theme)
    theme_colors = themes_parsed.get("colors")
    # Apply theme on colors
    ncolors = {}
    # Legacy color check
    logger.debug(dir(colors))
    legacy = check_legacy_colors()
    for color_name in theme_colors:
        c = theme_colors.get(color_name)
        ncolors[color_name] = c[color_mode]
        if legacy:
            colors[f"day{c[3].replace('--','-')}"] = c[1]
            colors[f"night{c[3].replace('--','-')}"] = c[2]
        else:
            if getattr(colors, color_name, False):
                setattr(colors, color_name, (c[1], c[2]))
    # Apply theme on palette
    apply_theme(ncolors)
    refresh_all_windows()

def apply_theme(colors) -> None:
    # Reset style and palette
    logger.debug(colors)
    if getattr(theme_manager, "_default_style", False):
        mw.app.setStyle(QStyleFactory.create(theme_manager._default_style))
        mw.app.setPalette(theme_manager.default_palette)
    # Load and apply palette
    palette = QPalette()
    # QT mappings
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

    highlight_bg = QColor(colors["HIGHLIGHT_BG"])
    highlight_bg.setAlpha(64)
    palette.setColor(QPalette.ColorRole.Highlight, highlight_bg)

    disabled_color = QColor(colors["DISABLED"])
    palette.setColor(QPalette.ColorRole.PlaceholderText, disabled_color)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, disabled_color)

    # Update palette
    theme_manager._apply_palette(mw.app) # Update palette theme_manager
    mw.app.setPalette(palette) # Overwrite palette
    theme_manager._apply_style(mw.app) # Update stylesheet theme_manager

    # Update webview background
    AnkiWebView._getWindowColor = lambda *args: QColor(colors["WINDOW_BG"])
    AnkiWebView.get_window_bg_color = lambda *args: QColor(colors["WINDOW_BG"])

# Create menu actions
def create_menu_action(parent: QWidget, dialog_class: QDialog, dialog_name: str) -> QAction:
    def open_dialog():
        dialog = dialog_class(mw)
        return dialog.exec()

    action = QAction(dialog_name, parent)
    #qconnect(action.triggered, open_dialog)
    action.triggered.connect(open_dialog)
    return action

# Load in the Anki-redesign menu
if not hasattr(mw, 'anki_redesign'):
    # Create anki-redesign menu
    mw.anki_redesign = QMenu("&Anki-redesign", mw)
    mw.form.menubar.insertMenu(mw.form.menuHelp.menuAction(), mw.anki_redesign)

    mw.anki_redesign.addAction(create_menu_action(mw.anki_redesign, AnkiRedesignConfigDialog, "&Config"))
    mw.anki_redesign.addSeparator()
    # Update and apply theme
    mw.reset()
    update_theme()
    # Rereload view to fix the QT6 header size on startup
    if 'Qt6' in QPalette.ColorRole.__module__:
        logger.debug('QT6 detected...')
        mw.reset()
        update_theme()

def on_theme_did_change() -> None:
    global color_mode
    color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark
    logger.debug("Theme changed")
    mw.reset()
    update_theme()
if attribute_exists(gui_hooks, "theme_did_change"):
    gui_hooks.theme_did_change.append(on_theme_did_change)