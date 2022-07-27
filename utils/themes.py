from asyncore import write
import os
import json

this_script_dir = os.path.join(os.path.dirname(__file__), "..")
themes_dir = os.path.join(this_script_dir, 'themes')
user_themes_dir = os.path.join(this_script_dir, 'user_files', 'themes')

def get_themes_dict() -> dict:
    # Set and load pathing for theme files (ReColor compatible)
    themes = {}
    system_themes = {}
    # Load themes
    for file in os.listdir(themes_dir):
        if "json" in file:
            file = file.replace(".json", "")
            if themes.get(file, "") == "":
                themes[file] = os.path.join(themes_dir, file+'.json')
                system_themes[file] = True
    # Overwrite themes with user themes
    for file in os.listdir(user_themes_dir):
        if "json" in file:
            file = file.replace(".json", "")
            themes[file] = os.path.join(user_themes_dir, file+'.json')
    return system_themes, themes

def sync_theme(theme):
    # Sync custom theme with system_theme if system_theme exists
    for file in os.listdir(themes_dir):
        if "json" in file:
            file = file.replace(".json", "")
            if themes.get(file, "") == "" and system_themes.get(file, False) and file == theme:
                themes_parsed = json.loads(open(themes[theme], encoding='utf-8').read())
                write_theme(theme, themes_parsed)
                break

def get_theme(theme: str) -> dict:
    # Open theme and parse it as json
    themes_parsed = json.loads(open(themes[theme], encoding='utf-8').read())
    theme_colors = themes_parsed.get("colors")
    # Add extra color_keys on theme files if not exist (ReColor compatible)
    if not theme_colors.get("PRIMARY_COLOR", False):
        theme_colors["PRIMARY_COLOR"] = ["Primary Color", "#0093d0", "#0093d0", "--primary-color"]
    if not theme_colors.get("FOCUS_SHADOW", False):
        theme_colors["FOCUS_SHADOW"] = ["Focus Shadow", "#ff93d0", "#0093d0", "--focus-shadow-color"]
    themes_parsed["colors"] = theme_colors
    return themes_parsed

def write_theme(file, theme_content):
    with open(file, "w") as f:
        json.dump(theme_content, f, indent=2, sort_keys=True)

system_themes, themes = get_themes_dict()
