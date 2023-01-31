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
                    themes_parsed = json.loads(
                        open(themes[file], encoding='utf-8').read())
                    write_theme(os.path.join(user_themes_dir,
                                file+".json"), themes_parsed)
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

    # OLD
    # NEW
    ['CANVAS', 'CANVAS_CODE', 'CANVAS_ELEVATED', 'CANVAS_INSET', 'CANVAS_OVERLAY'] # XXX
    ['FG', 'FG_DISABLED', 'FG_FAINT', 'FG_LINK', 'FG_SUBTLE'] # XXX

    ['BORDER', 'BORDER_FOCUS', 'BORDER_STRONG', 'BORDER_SUBTLE'] # XXX
    ['BUTTON_BG', 'BUTTON_DISABLED', 'BUTTON_GRADIENT_END', 'BUTTON_GRADIENT_START', 'BUTTON_HOVER_BORDER', 'BUTTON_PRIMARY_BG', 'BUTTON_PRIMARY_DISABLED', 'BUTTON_PRIMARY_GRADIENT_END', 'BUTTON_PRIMARY_GRADIENT_START'] # XXX

    ['SCROLLBAR_BG', 'SCROLLBAR_BG_ACTIVE', 'SCROLLBAR_BG_HOVER'] # XXX
    ['HIGHLIGHT_BG', 'HIGHLIGHT_FG'] # XXX
    ['SELECTED_BG', 'SELECTED_FG'] # XXX
    ['SHADOW', 'SHADOW_FOCUS', 'SHADOW_INSET', 'SHADOW_SUBTLE'] # XXX

    ['ACCENT_CARD', 'ACCENT_DANGER', 'ACCENT_NOTE'] # XXX
    ['STATE_BURIED', 'STATE_LEARN', 'STATE_MARKED', 'STATE_NEW', 'STATE_REVIEW', 'STATE_SUSPENDED'] # XXX
    ['FLAG_1', 'FLAG_2', 'FLAG_3', 'FLAG_4', 'FLAG_5', 'FLAG_6', 'FLAG_7'] # XXX


    theme_fixes = [
        # Extra
        {"key": "BUTTON_FOCUS_BG", "name": "Button Focus Background", "comment": "", "data": ["Button Focus Background", "#0093d0", "#0093d0", "--button-focus-bg"]},
        {"key": "FOCUS_SHADOW", "name": "Focus Shadow", "comment": "", "data": ["Focus Shadow","#ff93d0", "#0093d0", "--focus-shadow-color"]},
        # New Accent (Browser)
        {"key": "ACCENT_CARD", "name": "Accent Card", "comment": "Accent color for cards", "data": theme_colors["FLAG1_BG"][:-1] + ["--accent-card"]},
        {"key": "ACCENT_DANGER", "name": "Accent Danger", "comment": "Saturated accent color to grab attention", "data": theme_colors["FLAG2_BG"][:-1] + ["--accent-danger"]},
        {"key": "ACCENT_NOTE", "name": "Accent Note", "comment": "Accent color for notes", "data": theme_colors["FLAG3_BG"][:-1] + ["--accent-note"]},
        # New Border
        {"key": "BORDER", "name": "Border", "comment": "Border color with medium contrast against window background", "data": theme_colors["BORDER"][:-1] + ["--border"]},
        {"key": "BORDER_FOCUS", "name": "Border Focus", "comment": "Border color of focused input elements", "data": theme_colors["MEDIUM_BORDER"][:-1] + ["--border-focus"]},
        {"key": "BORDER_STRONG", "name": "Border Strong", "comment": "Border color with high contrast against window background", "data": theme_colors["MEDIUM_BORDER"][:-1] + ["--border-strong"]},
        {"key": "BORDER_SUBTLE", "name": "Border Subtle", "comment": "Border color with low contrast against window background", "data": theme_colors["FAINT_BORDER"][:-1] + ["--border-subtle"]},
        # New Canvas
        {"key": "CANVAS", "name": "Canvas", "comment": "Window background", "data": theme_colors["WINDOW_BG"][:-1] + ["--canvas"]},
        {"key": "CANVAS_CODE", "name": "Canvas code", "comment": "Background of code editors", "data": theme_colors["FRAME_BG"][:-1] + ["--canvas-code"]},
        {"key": "CANVAS_ELEVATED", "name": "Canvas Elevated", "comment": "Background of containers", "data": theme_colors["FRAME_BG"][:-1] + ["--canvas-elevated"]},
        {"key": "CANVAS_INSET", "name": "Canvas Inset", "comment": "Background of inputs inside containers", "data": theme_colors["FRAME_BG"][:-1] + ["--canvas-inset"]},
        {"key": "CANVAS_OVERLAY", "name": "Canvas Overlay", "comment": "Background of floating elements (menus, tooltips)", "data": theme_colors["TOOLTIP_BG"][:-1] + ["--canvas-overlay"]},
        # New Button
        {"key": "BUTTON_BG", "name": "Button Background", "comment": "Background color of buttons", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-bg"]},
        {"key": "BUTTON_DISABLED", "name": "Button Disabled", "comment": "Background color of disabled button", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-disabled"]},
        {"key": "BUTTON_GRADIENT_END", "name": "Button Gradient End", "comment": "End value of default button gradient", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-grandient-end"]},
        {"key": "BUTTON_GRADIENT_START", "name": "Button Gradient Start", "comment": "Start value of default button gradient", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-gradient-start"]},
        {"key": "BUTTON_HOVER_BORDER", "name": "Button Hover Border", "comment": "Border color of default button in hover state", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-hover-border"]},
        {"key": "BUTTON_PRIMARY_BG", "name": "Button Primary Background", "comment": "Background color of primary button", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-primary-bg"]},
        {"key": "BUTTON_PRIMARY_DISABLED", "name": "Button Primary Disabled", "comment": "Background color of primary button in disabled state", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-primary-disabled"]},
        {"key": "BUTTON_PRIMARY_GRADIENT_END", "name": "Button Primary Gradient End", "comment": "End value of primary button gradient", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-primary-gradient-end"]},
        {"key": "BUTTON_PRIMARY_GRADIENT_START", "name": "Button Primary Gradient Start", "comment": "Start value of primary button gradient", "data": theme_colors["BUTTON_BG"][:-1] + ["--button-primary-gradient-start"]},
        # New Foreground
        {"key": "FG", "name": "Foreground", "comment": "Default text/icon color", "data": theme_colors["TEXT_FG"][:-1] + ["--fg"]},
        {"key": "FG_DISABLED", "name": "Foreground Disabled", "comment": "Foreground color of disabled UI elements", "data": theme_colors["DISABLED"][:-1] + ["--fg-disabled"]},
        {"key": "FG_FAINT", "name": "Foreground Faint", "comment": "Foreground color that barely stands out against canvas", "data": theme_colors["DISABLED"][:-1] + ["--fg-faint"]},
        {"key": "FG_LINK", "name": "Foreground Link", "comment": "Hyperlink foreground color", "data": theme_colors["LINK"][:-1] + ["--fg-link"]},
        {"key": "FG_SUBTLE", "name": "Foreground Subtle", "comment": "Placeholder text, icons in idle state", "data": theme_colors["DISABLED"][:-1] + ["--fg-subtle"]},
        # New Flags (Browser)
        {"key": "FLAG_1", "name": "Flag 1 (red)", "comment": "", "data": theme_colors["FLAG1_FG"][:-1] + ["--flag-1"]},
        {"key": "FLAG_2", "name": "Flag 2 (orange)", "comment": "", "data": theme_colors["FLAG2_FG"][:-1] + ["--flag-2"]},
        {"key": "FLAG_3", "name": "Flag 3 (green)", "comment": "", "data": theme_colors["FLAG3_FG"][:-1] + ["--flag-3"]},
        {"key": "FLAG_4", "name": "Flag 4 (blue)", "comment": "", "data": theme_colors["FLAG4_FG"][:-1] + ["--flag-4"]},
        {"key": "FLAG_5", "name": "Flag 5 (pink)", "comment": "", "data": theme_colors["FLAG5_FG"][:-1] + ["--flag-5"]},
        {"key": "FLAG_6", "name": "Flag 6 (turquoise)", "comment": "", "data": theme_colors["FLAG6_FG"][:-1] + ["--flag-6"]},
        {"key": "FLAG_7", "name": "Flag 7 (purple)", "comment": "", "data": theme_colors["FLAG7_FG"][:-1] + ["--flag-7"]},
        # New Highlight
        {"key": "HIGHLIGHT_BG", "name": "Highlight Background", "comment": "Background color of highlighted items", "data": theme_colors["HIGHLIGHT_BG"][:-1] + ["--selected-bg"]},
        {"key": "HIGHLIGHT_FG", "name": "Highlight Foreground", "comment": "Foreground color of highlighted items", "data": theme_colors["HIGHLIGHT_FG"][:-1] + ["--selected-fg"]},
        # New Scrollbar
        {"key": "SCROLLBAR_BG", "name": "Scrollbar Background", "comment": "Background of scrollbar in idle state (Win/Lin only)", "data": theme_colors["FRAME_BG"][:-1] + ["--scrollbar-bg"]},
        {"key": "SCROLLBAR_BG_ACTIVE", "name": "Scrollbar Background Active", "comment": "Background of scrollbar in pressed state (Win/Lin only)", "data": theme_colors["TOOLTIP_BG"][:-1] + ["--scrollbar-bg-active"]},
        {"key": "SCROLLBAR_BG_HOVER", "name": "Scrollbar Background Hover", "comment": "Background of scrollbar in hover state (Win/Lin only)", "data": theme_colors["BORDER"][:-1] + ["--scrollbar-bg-hover"]},
        # New Selected
        {"key": "SELECTED_BG", "name": "Selected Background", "comment": "Background color of selected text", "data": theme_colors["HIGHLIGHT_BG"][:-1] + ["--selected-bg"]},
        {"key": "SELECTED_FG", "name": "Selected Foreground", "comment": "Foreground color of selected text", "data": theme_colors["HIGHLIGHT_FG"][:-1] + ["--selected-fg"]},
        # New Shadow
        {"key": "SHADOW", "name": "Shadow", "comment": "Default box-shadow color", "data": theme_colors["FOCUS_SHADOW"][:-1] + ["--shadow"]},
        {"key": "SHADOW_FOCUS", "name": "Shadow Focus", "comment": "Box-shadow color for elements in focused state", "data": theme_colors["FOCUS_SHADOW"][:-1] + ["--shadow-focus"]},
        {"key": "SHADOW_INSET", "name": "Shadow Inset", "comment": "Inset box-shadow color", "data": theme_colors["FOCUS_SHADOW"][:-1] + ["--shadow-inset"]},
        {"key": "SHADOW_SUBTLE", "name": "Shadow Subtle", "comment": "Box-shadow color with lower contrast against window background", "data": theme_colors["FOCUS_SHADOW"][:-1] + ["--shadow-subtle"]},
        # New States (Browser)
        {"key": "STATE_BURIED", "name": "State Buried", "comment": "Accent color for buried cards", "data": theme_colors["BURIED_FG"][:-1] + ["--state-buried"]},
        {"key": "STATE_LEARN", "name": "State Learn", "comment": "Accent color for cards in learning state", "data": theme_colors["LEARN_COUNT"][:-1] + ["--state-learn"]},
        {"key": "STATE_MARKED", "name": "State Marked", "comment": "Accent color for marked cards", "data": theme_colors["MARKED_BG"][:-1] + ["--state-marked"]},
        {"key": "STATE_NEW", "name": "State New", "comment": "Accent color for new cards", "data": theme_colors["NEW_COUNT"][:-1] + ["--state-new"]},
        {"key": "STATE_REVIEW", "name": "State Review", "comment": "Accent color for cards in review state", "data": theme_colors["REVIEW_COUNT"][:-1] + ["--state-review"]},
        {"key": "STATE_SUSPENDED", "name": "State Suspended", "comment": "Accent color for suspended cards", "data": theme_colors["SUSPENDED_FG"][:-1] + ["--state-suspended"]},

    ]

    # Add extra color_keys on theme files if not exist, fixing legacy themes pre 2.1.56
    for theme_keys in theme_fixes:
        if not theme_colors.get(theme_keys["key"], False):
            temp_data = theme_keys["data"]
            theme_colors[theme_keys["key"]] = [theme_keys["name"], theme_keys["comment"], temp_data[-3], temp_data[-2], temp_data[-1]]

    for colors in theme_colors:
        if len(theme_colors[colors]) == 4:
            temp_data = theme_colors[colors]
            theme_colors[colors] = [temp_data[0], "", temp_data[-3], temp_data[-2], temp_data[-1]]

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
        themes_parsed = json.loads(
            open(os.path.join(themes_dir, theme+".json"), encoding='utf-8').read())
        write_theme(themes[theme], themes_parsed)
    _, themes = get_themes_dict()
    return themes
