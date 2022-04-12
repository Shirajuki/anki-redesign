from enum import Enum
from typing import NamedTuple, Iterable, Tuple
from aqt.qt import *
from ..config import config, write_config

class ShowOptions(Enum):
    always = "Always"
    menus = "Toolbar and menus"
    drag_and_drop = "On drag and drop"
    never = "Never"

    def __eq__(self, other: str):
        return self.name == other

    @classmethod
    def index_of(cls, name):
        for index, item in enumerate(cls):
            if name == item.name:
                return index
        return 0

class SettingsDialog(QDialog):
    """Dialog shown on bulk-convert."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sliderRow = QVBoxLayout()
        self.sliders = {
            
        }

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(ADDON_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)

        self.setLayout(self.create_main_layout())
        self.populate_slider_row()
        self.setup_tool_tips()
        self.setup_logic()
        self.set_initial_values()

    def create_main_layout(self):
        layout = QVBoxLayout()
        layout.addLayout(self.sliderRow)
        layout.addStretch()
        layout.addWidget(self.button_box)
        return layout

    def setup_logic(self):
        qconnect(self.button_box.accepted, self.on_accept)
        qconnect(self.button_box.rejected, self.reject)


    def on_accept(self):
        write_config()
        self.accept()


class ImageDimensions(NamedTuple):
    width: int
    height: int

class SettingsMenuDialog(SettingsDialog):
    """Settings dialog available from the main menu."""

    __checkboxes = {
        'drag_and_drop': 'Convert images on drag and drop',
        'copy_paste': 'Convert images on copy-paste',
        'avoid_upscaling': 'Avoid upscaling',
        'preserve_original_filenames': 'Preserve original filenames, if available',
    }

    def __init__(self, *args, **kwargs):
        self.when_show_dialog_combo_box = self.create_when_show_dialog_combo_box()
        self.filename_pattern_combo_box = self.create_filename_pattern_combo_box()
        self.checkboxes = {key: QCheckBox(text) for key, text in self.__checkboxes.items()}
        super().__init__(*args, **kwargs)

    @staticmethod
    def create_when_show_dialog_combo_box() -> QComboBox:
        combobox = QComboBox()
        for option in ShowOptions:
            combobox.addItem(option.value, option.name)
        return combobox

    def create_additional_settings_group_box(self):
        def create_inner_vbox():
            vbox = QVBoxLayout()
            vbox.addLayout(self.create_combo_boxes_layout())
            for widget in self.checkboxes.values():
                vbox.addWidget(widget)
            return vbox

        gbox = QGroupBox("Behavior")
        gbox.setLayout(create_inner_vbox())
        return gbox

    def set_initial_values(self):
        super().set_initial_values()
        self.when_show_dialog_combo_box.setCurrentIndex(ShowOptions.index_of(config.get("show_settings")))

        for key, widget in self.checkboxes.items():
            widget.setChecked(config[key])

    def create_combo_boxes_layout(self):
        layout = QFormLayout()
        layout.addRow("Show this dialog", self.when_show_dialog_combo_box)
        layout.addRow("Filename pattern", self.filename_pattern_combo_box)
        return layout

    def on_accept(self):
        config['show_settings'] = self.when_show_dialog_combo_box.currentData()
        config['filename_pattern_num'] = self.filename_pattern_combo_box.currentIndex()

        for key, widget in self.checkboxes.items():
            config[key] = widget.isChecked()
        super().on_accept()