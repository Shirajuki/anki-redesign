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
                # Initial run: if system_theme not found in user themes, copy over
                if not file+".json" in os.listdir(user_themes_dir):
                    themes_parsed = json.loads(open(themes[file], encoding='utf-8').read())
                    write_theme(os.path.join(user_themes_dir, file+".json"), themes_parsed)
    # Overwrite themes with user themes
    for file in os.listdir(user_themes_dir):
        if "json" in file:
            file = file.replace(".json", "")
            themes[file] = os.path.join(user_themes_dir, file+'.json')
    return system_themes, themes 

def get_theme(theme: str) -> dict:
    # Open theme and parse it as json
    _, themes = get_themes_dict()
    themes_parsed = json.loads(open(themes[theme], encoding='utf-8').read())
    theme_colors = themes_parsed.get("colors")
    # Add extra color_keys on theme files if not exist (ReColor compatible)
    if not theme_colors.get("BUTTON_FOCUS_BG", False):
        theme_colors["BUTTON_FOCUS_BG"] = ["Button Focus Background", "#0093d0", "#0093d0", "--button-focus-bg"]
    if not theme_colors.get("FOCUS_SHADOW", False):
        theme_colors["FOCUS_SHADOW"] = ["Focus Shadow", "#ff93d0", "#0093d0", "--focus-shadow-color"]
    if theme_colors.get("BUTTON_BG", False):
        theme_colors["BUTTON_BG"] =  theme_colors["BUTTON_BG"][:-1]+["--button-bg"]
    themes_parsed["colors"] = theme_colors
    return themes_parsed

def write_theme(file, theme_content):
    with open(file, "w") as f:
        json.dump(theme_content, f, indent=2, sort_keys=True)

system_themes, themes = get_themes_dict()

def clone_theme(theme, themes):
    # Clone custom theme
    num = sum([1 for t in themes if theme in t])
    themes_parsed = json.loads(open(themes[theme], encoding='utf-8').read())
    write_theme(themes[theme][:-5] + f" - Copy {num}.json", themes_parsed)
    _, themes = get_themes_dict()
    return themes

def delete_theme(theme, themes):
    if not system_themes.get(theme, False):
        os.remove(themes[theme])
        del themes[theme]
    _, themes = get_themes_dict()
    return themes

def sync_theme(theme, themes):
    # Sync custom theme with system_theme if system_theme exists
    if system_themes.get(theme, False):
        themes_parsed = json.loads(open(os.path.join(themes_dir, theme+".json"), encoding='utf-8').read())
        write_theme(themes[theme], themes_parsed)
    _, themes = get_themes_dict()
    return themes