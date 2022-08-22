import json
from aqt import mw, gui_hooks
from aqt.qt import *
from .modules import *
from ..config import config, write_config, get_config
from aqt.utils import showInfo
from aqt.webview import AnkiWebView
from .dark_title_bar import set_dark_titlebar_qt, dwmapi
from .logger import logger
from aqt.theme import theme_manager, colors
from ..injections.toolbar import redraw_toolbar, redraw_toolbar_legacy
from .themes import system_themes, themes, write_theme, get_theme, sync_theme, clone_theme, delete_theme

theme = config['theme']
themes_parsed = get_theme(theme)
color_mode = 2 if theme_manager.get_night_mode() else 1 # 1 = light and 2 = dark

class AnkiRedesignThemeEditor(QDialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent=parent or mw, *args, **kwargs)
        self.config_editor = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(f'Anki-redesign advanced editor')
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
        self.theme_general = ["TEXT_FG", "WINDOW_BG", "FRAME_BG", "BUTTON_BG", "BUTTON_FOCUS_BG", "TOOLTIP_BG", "BORDER", "MEDIUM_BORDER", "FAINT_BORDER", "HIGHLIGHT_BG", "HIGHLIGHT_FG" , "LINK", "DISABLED", "SLIGHTLY_GREY_TEXT", "FOCUS_SHADOW"]
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
            self.radio = self.theme_button(key, not key in system_themes)
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
        self.addon_no_distractions_full_screen_check = self.checkbox("addon_no_distractions_full_screen")
        self.settings_layout.addRow("No Distractions Full Screen", self.addon_no_distractions_full_screen_check)

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

    def theme_button(self, key: str, custom = False):
        layout = QGridLayout()
        radio = self.radio_button(key)
        clone_button = QPushButton('Clone')
        clone_button .setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clone_button .clicked.connect(lambda _: self.clone_theme(key))
        layout.addWidget(radio, 0, 0)
        if custom:
            delete_button= QPushButton('Delete')
            delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            delete_button.clicked.connect(lambda _: self.delete_theme(key))
            layout.addWidget(delete_button, 0, 1)
        else:
            sync_button = QPushButton('Sync')
            sync_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            sync_button.clicked.connect(lambda _: self.sync_theme(key))
            layout.addWidget(sync_button, 0, 1)
        layout.addWidget(clone_button, 0, 2)
        layout.addWidget(QLabel(), 0, 3)
        layout.addWidget(QLabel(), 0, 4)
        return layout

    def clone_theme(self, key):
        global themes
        logger.debug("Clone: " + key)
        popup = QMessageBox()
        popup.setIcon(QMessageBox.Information)
        popup.setText(f"Are you sure you want to clone the selected theme: {key}")
        popup.setWindowTitle(f"Clone theme {key}")
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if popup.exec() == QMessageBox.Yes:
            showInfo(_(f"Successfully cloned theme {key}"))
            themes = clone_theme(key, themes)
            self.restart()

    def delete_theme(self, key):
        global themes
        logger.debug("Delete: " + key)
        popup = QMessageBox()
        popup.setIcon(QMessageBox.Information)
        popup.setText(f"Are you sure you want to delete the selected theme: {key}")
        popup.setWindowTitle(f"Delete theme {key}")
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if popup.exec() == QMessageBox.Yes:
            showInfo(_(f"Successfully deleted theme {key}"))
            themes = delete_theme(key, themes)
            self.restart()

    def sync_theme(self, key):
        global themes
        logger.debug("Sync: " + key)
        popup = QMessageBox()
        popup.setIcon(QMessageBox.Information)
        popup.setText(f"Are you sure you want to sync the selected theme: {key}")
        popup.setWindowTitle(f"Sync theme {key}")
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if popup.exec() == QMessageBox.Yes:
            showInfo(_(f"Successfully synced system theme {key}.\nClick save to apply the changes on current window."))
            themes = sync_theme(key, themes)
            self.restart()

    def restart(self):
        # Close window
        self.accept()
        self.close()
        # Open window again
        mw.anki_redesign_cache = AnkiRedesignConfigDialog(mw)
        mw.anki_redesign_cache.exec()

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
    gui_hooks.debug_console_will_show(mw)
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
    # mw.anki_redesign = QMenu("&Anki-redesign", mw)
    # mw.form.menubar.insertMenu(mw.form.menuHelp.menuAction(), mw.anki_redesign)
    # mw.anki_redesign.addAction(create_menu_action(mw.anki_redesign, AnkiRedesignConfigDialog, "&Config"))
    # mw.anki_redesign.addSeparator()
    mw.form.menuTools.addAction(create_menu_action(mw, AnkiRedesignConfigDialog, "&Anki-redesign"))
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