import json
from aqt import mw, gui_hooks, appVersion
from aqt.qt import *
from .modules import *
from .translation import get_texts
from ..config import config, write_config, get_config
from aqt.utils import showInfo
from aqt.webview import AnkiWebView
from .logger import logger
from aqt.theme import theme_manager, colors
from ..injections.toolbar import redraw_toolbar, redraw_toolbar_legacy
from .themes import system_themes, themes, write_theme, get_theme, sync_theme, clone_theme, delete_theme
if module_has_attribute("anki.lang", "current_lang"):
    from anki.lang import current_lang, lang_to_disk_lang, compatMap
else:
    from anki.lang import currentLang as current_lang, lang_to_disk_lang, compatMap
from .dark_title_bar import set_dark_titlebar_qt, dwmapi
anki_version = tuple(int(segment) for segment in appVersion.split("."))

theme = config['theme']
themes_parsed = get_theme(theme)
color_mode = 3 if theme_manager.get_night_mode() else 2  # 1 = light and 2 = dark

def get_anki_lang():
    lang = lang_to_disk_lang(current_lang)
    if lang in compatMap:
        lang = compatMap[lang]
    lang = lang.replace("-", "_")
    return lang

class AnkiRedesignThemeEditor(QDialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent=parent or mw, *args, **kwargs)
        self.config_editor = parent
        self.texts = get_texts(get_anki_lang())
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(self.texts["theme_editor_window_title"])
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
            button = QPushButton(self.texts["cancel_button"])
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            qconnect(button.clicked, self.accept)
            return button

        def save():
            button = QPushButton(self.texts["save_button"])
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
        self.texts = get_texts(get_anki_lang())
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(self.texts["configuration_window_title"])
        self.setSizePolicy(self.make_size_policy())
        self.setMinimumSize(420, 580)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        set_dark_titlebar_qt(self, dwmapi, fix=False)

        # Color/theme
        # Loads theme color
        self.theme_colors = themes_parsed.get("colors")
        self.updates = []
        self.theme_general = ["TEXT_FG", "WINDOW_BG", "FRAME_BG", "BUTTON_BG", "BUTTON_FOCUS_BG", "TOOLTIP_BG", "BORDER", "MEDIUM_BORDER", "FAINT_BORDER", "HIGHLIGHT_BG", "HIGHLIGHT_FG" , "LINK", "DISABLED", "SLIGHTLY_GREY_TEXT", "FOCUS_SHADOW"]
        self.theme_decks = ["CURRENT_DECK", "NEW_COUNT", "LEARN_COUNT", "REVIEW_COUNT", "ZERO_COUNT"]
        self.theme_browse = ["BURIED_FG", "SUSPENDED_FG", "MARKED_BG", "FLAG1_BG", "FLAG1_FG", "FLAG2_BG", "FLAG2_FG", "FLAG3_BG", "FLAG3_FG", "FLAG4_BG", "FLAG4_FG", "FLAG5_BG", "FLAG5_FG", "FLAG6_BG", "FLAG6_FG", "FLAG7_BG", "FLAG7_FG"]
        self.theme_extra = []
        if anki_version >= (2, 1, 56):
            self.theme_general = ['FG', 'FG_DISABLED', 'FG_FAINT', 'FG_LINK', 'FG_SUBTLE'] + ['CANVAS', 'CANVAS_CODE', 'CANVAS_ELEVATED', 'CANVAS_INSET', 'CANVAS_OVERLAY']
            self.theme_decks = ['BORDER', 'BORDER_FOCUS', 'BORDER_STRONG', 'BORDER_SUBTLE'] + ['BUTTON_BG', 'BUTTON_DISABLED', 'BUTTON_GRADIENT_END', 'BUTTON_GRADIENT_START', 'BUTTON_HOVER_BORDER', 'BUTTON_PRIMARY_BG', 'BUTTON_PRIMARY_DISABLED', 'BUTTON_PRIMARY_GRADIENT_END', 'BUTTON_PRIMARY_GRADIENT_START']
            self.theme_browse = ['ACCENT_CARD', 'ACCENT_DANGER', 'ACCENT_NOTE'] + ['STATE_BURIED', 'STATE_LEARN', 'STATE_MARKED', 'STATE_NEW', 'STATE_REVIEW', 'STATE_SUSPENDED'] + ['FLAG_1', 'FLAG_2', 'FLAG_3', 'FLAG_4', 'FLAG_5', 'FLAG_6', 'FLAG_7']
            self.theme_extra = ['SCROLLBAR_BG', 'SCROLLBAR_BG_ACTIVE', 'SCROLLBAR_BG_HOVER'] + ['HIGHLIGHT_BG', 'HIGHLIGHT_FG'] + ['SELECTED_BG', 'SELECTED_FG'] + ['SHADOW', 'SHADOW_FOCUS', 'SHADOW_INSET', 'SHADOW_SUBTLE']

        # Root layout
        self.root_layout = QVBoxLayout(self)
        # Main layout
        self.layout = QVBoxLayout()
        # Initialize tab screen
        self.tabs = QTabWidget(objectName="tabs")
        self.tabs.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.tab_general = QWidget(objectName="general")
        self.tab_general.setLayout(
            self.create_color_picker_layout(self.theme_general))
        self.tab_decks = QWidget(objectName="decks")
        self.tab_decks.setLayout(
            self.create_color_picker_layout(self.theme_decks))
        self.tab_browse = QWidget(objectName="browse")
        self.tab_browse.setLayout(
            self.create_color_picker_layout(self.theme_browse))
        self.tab_extra = QWidget(objectName="extra")
        self.tab_extra.setLayout(
            self.create_color_picker_layout(self.theme_extra))

        self.tab_settings = QWidget(objectName="settings")
        self.settings_layout = QFormLayout()
        self.theme_label = QLabel(self.texts["theme_label"])
        self.theme_label.setStyleSheet(
            'QLabel { font-size: 14px; font-weight: bold }')
        self.settings_layout.addRow(self.theme_label)
        for key in themes:
            self.radio = self.theme_button(key, not key in system_themes)
            self.settings_layout.addRow(key, self.radio)
        self.settings_layout.addRow(QLabel())

        self.font_label = QLabel(self.texts["font_label"])
        self.font_label.setStyleSheet(
            'QLabel { font-size: 14px; font-weight: bold }')
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

        self.fix_label = QLabel(self.texts["addon_compatibility_fix_label"])
        self.fix_label.setStyleSheet(
            'QLabel { font-size: 14px; font-weight: bold }')
        self.settings_layout.addRow(self.fix_label)
        self.addon_more_overview_stats_check = self.checkbox(
            "addon_more_overview_stats")
        self.settings_layout.addRow(
            "More Overview Stats 21", self.addon_more_overview_stats_check)
        self.addon_advanced_review_bottom_bar_check = self.checkbox(
            "addon_advanced_review_bottom_bar")
        self.settings_layout.addRow(
            "Advanced Review Bottom Bar", self.addon_advanced_review_bottom_bar_check)
        self.addon_no_distractions_full_screen_check = self.checkbox(
            "addon_no_distractions_full_screen")
        self.settings_layout.addRow(
            "No Distractions Full Screen", self.addon_no_distractions_full_screen_check)

        self.tab_settings.setLayout(self.settings_layout)

        # Add tabs
        self.tabs.resize(300, 200)
        self.tabs.addTab(self.tab_settings, self.texts["settings_tab"])
        self.tabs.addTab(self.tab_general, self.texts["general_tab"])
        self.tabs.addTab(self.tab_decks, self.texts["decks_tab"])
        self.tabs.addTab(self.tab_browse, self.texts["browse_tab"])
        self.tabs.addTab(self.tab_extra, "Extra")
        # Add tabs to widget
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

    def theme_button(self, key: str, custom=False):
        layout = QGridLayout()
        radio = self.radio_button(key)
        clone_button = QPushButton(self.texts["clone_button"])
        clone_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clone_button.clicked.connect(lambda _: self.clone_theme(key))
        layout.addWidget(radio, 0, 0)
        if custom:
            delete_button = QPushButton(self.texts["delete_button"])
            delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            delete_button.clicked.connect(lambda _: self.delete_theme(key))
            layout.addWidget(delete_button, 0, 1)
        else:
            sync_button = QPushButton(self.texts["sync_button"])
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
        popup.setText(self.texts["clone_message"] % key)
        popup.setWindowTitle(self.texts["clone_window_title"] % key)
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if popup.exec() == QMessageBox.Yes:
            showInfo(_(self.texts["clone_success_message"] % key))
            themes = clone_theme(key, themes)
            self.restart()

    def delete_theme(self, key):
        global themes
        logger.debug("Delete: " + key)
        popup = QMessageBox()
        popup.setIcon(QMessageBox.Information)
        popup.setText(self.texts["delete_message"] % key)
        popup.setWindowTitle(self.texts["delete_window_title"] % key)
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if popup.exec() == QMessageBox.Yes:
            showInfo(_(self.texts["delete_success_message"] % key))
            themes = delete_theme(key, themes)
            self.restart()

    def sync_theme(self, key):
        global themes
        logger.debug("Sync: " + key)
        popup = QMessageBox()
        popup.setIcon(QMessageBox.Information)
        popup.setText(self.texts["sync_message"] % key)
        popup.setWindowTitle(self.texts["sync_window_title"] % key)
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if popup.exec() == QMessageBox.Yes:
            showInfo(_(self.texts["sync_success_message"] % key))
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
        button.setToolTip(self.theme_colors.get(key)[1])

        color_dialog = QColorDialog(self)

        def set_color(rgb: str) -> None:
            # Check for valid color
            color = QColor()
            color.setNamedColor(rgb)
            if not color.isValid():
                return
            # Update color
            color_dialog.setCurrentColor(color)
            button.setStyleSheet(
                'QPushButton{ background-color: "%s"; border: none; border-radius: 2px}' % rgb)

        def update() -> None:
            # TODO: fix this
            try:
                rgb = self.theme_colors.get(key)[color_mode]
            except:
                rgb = "#ff0000"
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
            layout.addRow(self.theme_colors.get(key)[0], self.color_input(key))
        return layout

    def theme_file_editor(self) -> None:
        diag = AnkiRedesignThemeEditor(self)
        diag.show()

    def make_button_box(self) -> QWidget:
        def advanced():
            button = QPushButton(self.texts["advanced_button"])
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            qconnect(button.clicked, self.theme_file_editor)
            return button

        def cancel():
            button = QPushButton(self.texts["cancel_button"])
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            qconnect(button.clicked, self.accept)
            return button

        def save():
            button = QPushButton(self.texts["save_button"])
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
        config['addon_no_distractions_full_screen'] = self.addon_no_distractions_full_screen_check.isChecked()
        config["theme"] = theme
        write_config(config)
        config = get_config()
        logger.debug(config)

        # Write and update theme
        color_mode = 3 if theme_manager.get_night_mode() else 2  # 2 = light and 3 = dark
        themes_parsed["colors"] = self.theme_colors
        write_theme(themes[theme], themes_parsed)
        update_theme()

        # ShowInfo for both new and legacy support
        showInfo(_(self.texts["changes_message"]))
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
        gui_hooks.top_toolbar_did_init_links.append(lambda a, b: [redraw_toolbar_legacy(a, b), gui_hooks.top_toolbar_did_init_links.remove(print)])

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
    light = 2
    dark = 3
    color_mode = dark if theme_manager.get_night_mode() else light
    # Apply theme on colors
    ncolors = {}
    # Legacy color check
    # logger.debug(dir(colors))
    legacy = check_legacy_colors()
    for color_name in theme_colors:
        c = theme_colors.get(color_name)
        ncolors[color_name] = c[color_mode]
        if legacy:
            colors[f"day{c[3].replace('--','-')}"] = c[light]
            colors[f"night{c[3].replace('--','-')}"] = c[dark]
        else:
            if getattr(colors, color_name, False):
                if anki_version >= (2, 1, 56):
                    setattr(colors, color_name, {"light": c[light], "dark": c[dark]})
                else:
                    setattr(colors, color_name, (c[light], c[dark]))
    # Apply theme on palette
    apply_theme(ncolors)
    gui_hooks.debug_console_will_show(mw)
    refresh_all_windows()


def apply_theme(colors) -> None:
    # Reset style and palette
    logger.debug(colors)
    if getattr(theme_manager, "_default_style", False):
        mw.app.setStyle(QStyleFactory.create(theme_manager._default_style))
        if getattr(theme_manager, "default_palette", False):
            mw.app.setPalette(theme_manager.default_palette)
        else:
            theme_manager._apply_palette(mw.app)
    # Load and apply palette
    palette = QPalette()
    # Update palette
    if anki_version >= (2, 1, 56):
        text = QColor(colors["FG"])
        palette.setColor(QPalette.ColorRole.WindowText, text)
        palette.setColor(QPalette.ColorRole.ToolTipText, text)
        palette.setColor(QPalette.ColorRole.Text, text)
        palette.setColor(QPalette.ColorRole.ButtonText, text)

        hlbg = QColor(colors["HIGHLIGHT_BG"])
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["HIGHLIGHT_FG"]))
        palette.setColor(QPalette.ColorRole.Highlight, hlbg)

        canvas = QColor(colors["CANVAS"])
        palette.setColor(QPalette.ColorRole.Window, canvas)
        palette.setColor(QPalette.ColorRole.AlternateBase, canvas)

        palette.setColor(QPalette.ColorRole.Button, QColor(colors["BUTTON_BG"]))

        input_base = QColor(colors["CANVAS_CODE"])
        palette.setColor(QPalette.ColorRole.Base, input_base)
        palette.setColor(QPalette.ColorRole.ToolTipBase, input_base)

        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors["FG_SUBTLE"]))

        disabled_color = QColor(colors["FG_DISABLED"])
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, disabled_color)
        palette.setColor(QPalette.ColorRole.Link, QColor(colors["FG_LINK"]))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)

        # Update webview background
        AnkiWebView._getWindowColor = lambda *args: QColor(colors["CANVAS"])
        AnkiWebView.get_window_bg_color = lambda *args: QColor(colors["CANVAS"])

        theme_manager._apply_palette(mw.app)  # Update palette theme_manager
        mw.app.setPalette(palette)  # Overwrite palette
        theme_manager._apply_style(mw.app)  # Update stylesheet theme_manager
    else:
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

        # Update webview background
        AnkiWebView._getWindowColor = lambda *args: QColor(colors["WINDOW_BG"])
        AnkiWebView.get_window_bg_color = lambda *args: QColor(colors["WINDOW_BG"])

        theme_manager._apply_palette(mw.app)  # Update palette theme_manager
        mw.app.setPalette(palette)  # Overwrite palette
        theme_manager._apply_style(mw.app)  # Update stylesheet theme_manager


def create_menu_action(parent: QWidget, dialog_class: QDialog, dialog_name: str) -> QAction:
    def open_dialog():
        dialog = dialog_class(mw)
        return dialog.exec()

    action = QAction(dialog_name, parent)
    action.triggered.connect(open_dialog)
    return action


# Load in the Anki-redesign menu
if not hasattr(mw, 'anki_redesign'):
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
    color_mode = 3 if theme_manager.get_night_mode() else 2  # 2 = light and 3 = dark
    logger.debug("Theme changed")
    mw.reset()
    update_theme()


if attribute_exists(gui_hooks, "theme_did_change"):
    gui_hooks.theme_did_change.append(on_theme_did_change)
