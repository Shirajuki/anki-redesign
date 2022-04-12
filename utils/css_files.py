import os
from aqt import mw

mw.addonManager.setWebExports(__name__, r"files/.*\.(css|svg|gif|png)|user_files/.*\.(css|svg|gif|png)")
addon_package = mw.addonManager.addonFromModule(__name__)

this_script_dir = os.path.join(os.path.dirname(__file__), "..")
files_dir = os.path.join(this_script_dir, 'files')
user_files_dir = os.path.join(this_script_dir, 'user_files')
css_files_dir = {
  'BottomBar': f"/_addons/{addon_package}/files/BottomBar.css",
  'CardLayout': f"/_addons/{addon_package}/files/CardLayout.css",
  'DeckBrowser': f"/_addons/{addon_package}/files/DeckBrowser.css",
  'Editor': f"/_addons/{addon_package}/files/Editor.css",
  'global': f"/_addons/{addon_package}/files/global.css",
  'legacy': f"/_addons/{addon_package}/files/legacy.css",
  'Overview': f"/_addons/{addon_package}/files/Overview.css", 
  'QAbout': os.path.join(files_dir, 'QAbout.css'),
  'QAddCards': os.path.join(files_dir, 'QAddCards.css'),
  'QAddonsDialog': os.path.join(files_dir, 'QAddonsDialog.css'),
  'QBrowser': os.path.join(files_dir, 'QBrowser.css'),
  'QFilteredDeckConfigDialog': os.path.join(files_dir, 'QFilteredDeckConfigDialog.css'),
  'QEditCurrent': os.path.join(files_dir, 'QEditCurrent.css'),
  'QNewDeckStats': os.path.join(files_dir, 'QNewDeckStats.css'),
  'QPreferences': os.path.join(files_dir, 'QPreferences.css'),
  'Reviewer': f"/_addons/{addon_package}/files/Reviewer.css",
  'ReviewerBottomBar': f"/_addons/{addon_package}/files/ReviewerBottomBar.css",
  'TopToolbar': f"/_addons/{addon_package}/files/TopToolbar.css",
}
# Replace pathing for user customised styled files
for file in os.listdir(user_files_dir):
  file = file.replace(".css", "")
  if css_files_dir.get(file, "") != "":
    if file.startswith("Q"):
        css_files_dir[file] = os.path.join(user_files_dir, file+'.css')
    else:
        css_files_dir[file] = f"/_addons/{addon_package}/user_files/{file}.css"
