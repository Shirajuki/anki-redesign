import os
import json
from aqt import mw

this_script_dir = os.path.join(os.path.dirname(__file__), "..")
themes_dir = os.path.join(this_script_dir, 'themes')
themes = {}

# Replace pathing for theme files (ReColor compatible)
for file in os.listdir(themes_dir):
  file = file.replace(".json", "")
  if themes.get(file, "") == "":
    themes[file] = os.path.join(themes_dir, file+'.json')

def write_theme(file, theme_content):
    with open(file) as f:
        json.dump(theme_content, f, indent=2, sort_keys=True)
