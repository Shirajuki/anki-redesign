import os
import json
from aqt import mw
from .logger import logger

this_script_dir = os.path.join(os.path.dirname(__file__), "..")
themes_dir = os.path.join(this_script_dir, 'themes')

def get_themes_dict() -> dict:
    # Replace pathing for theme files (ReColor compatible)
    themes = {}
    for file in os.listdir(themes_dir):
        if "json" in file:
            file = file.replace(".json", "")
            if themes.get(file, "") == "":
                themes[file] = os.path.join(themes_dir, file+'.json')
    return themes
    # "link_color": "#77ccff",
    # "primary_color": "#0093d0",

def get_theme(theme: str) -> dict:
    themes_parsed = json.loads(open(themes[theme], encoding='utf-8').read())
    theme_colors = themes_parsed.get("colors")
    # Add extra color_keys on theme files if not exist (ReColor compatible)
    if not theme_colors.get("PRIMARY_COLOR", False):
        theme_colors["PRIMARY_COLOR"] = ["Primary Color", "#0093d0", "#0093d0", "--primary-color"]
    themes_parsed["colors"] = theme_colors
    return themes_parsed

def write_theme(file, theme_content):
    with open(file, "w") as f:
        json.dump(theme_content, f, indent=2, sort_keys=True)

themes = get_themes_dict()
