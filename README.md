# Anki-redesign

> A new lightweight look for Anki compatible with most (if not all) versions of Anki 2.1.X running QT5. - Specifically tested on Anki 2.1.49

Note: This add-on uses hooks and doesn't overwrite the original Anki code views that much, meaning that most add-ons should properly work with Anki-redesign enabled. However, if there is any add-on found to not be working properly, feel free to make an [issue](https://github.com/Shirajuki/anki-redesign/issues) and I'll try to add support for it!
(List of tested addons and manual fixes for them to work can be seen on the [project github wiki](https://github.com/Shirajuki/anki-redesign/wiki/Compatible-Add-ons-for-Anki-2.1).)

Note2: <b>This addon also works as a theming addon</b> as it enables the possibility of user customization on almost all Anki views/windows through the injection of CSS and QT CSS on the different components. The adding of custom styling can be done by copying over the css files from `./files` to `./user_files` and then editing the styling there. Primary color of button focus, link color, as well as the font, can be changed in the addon config.

Note3: If the addon is not updating try open anki while holding shift to turn off all addons, then update and restart. :)

**Manually tested on the following Anki versions:**

- 2.1.49
- 2.1.26
- 2.1.22

**(Planned) Updates / todos (as of 13.04.2022):**

- [x] Add minor design fixes for a cleaner design (v0.0.2)
- [x] Fix light-mode design and better contrasts (v0.0.2)
- [x] Add a primary color of choice and more lightweight user defined customizations through config file (v0.0.3)
- [x] Fix bug where deck timer appears on top of the show answer button (v0.0.3)
- [x] Addon said not be working on Anki version 2.1.22, manually fix this (v0.0.3)
- [x] Fix problem with darkmode Mac Computers (v0.0.3)
- [x] Removes unfinished styling on dialog windows - AddCards (v0.0.4)
- [x] Add user customization on all styling views through the user_files folder (user custom CSS injection) (v0.0.5)
- [x] Add more lightweight modern styling for other views / qt dialogs (v0.1.0)
- [x] Add dialog window for configuration and user customizations (will replace config.json for a better ease) (v0.1.0)
- [ ] Add styling support for QT6 when it gets released (will do for 2.1.50 beta if requested or the need is there)
- [ ] Manually test for backwards compatibility on older major Anki versions. (2.1.22 &amp; 26 tested)

<br/>
<div><img src="./screenshots/ui-half.png"></div>
<div><img src="./screenshots/dialog.png"></div>
<br/>

**Guide:**

1. Download the Add-on from [AnkiWeb](https://ankiweb.net/shared/info/308574457)
2. there will be an Anki-redesign menu at the top. Click the config submenu to open the Anki-redesign Configuration dialog.
3. Customize Anki as you like, see the [readme image](https://raw.githubusercontent.com/Shirajuki/anki-redesign/main/screenshots/guide.png)
4. The colors will update after clicking "Save", however to make sure everything is updated, do a restart after customizing.

**Credits:**

The concept of this add-on was inspired by the following add-on and designs:

- [Developer Nick's Redesign Add-on](https://github.com/nickdvlpr/Redesign)
- [Yanyi Yoong's Anki Reimagine](https://www.behance.net/gallery/50253077/Anki-Reimagine)
- [Beatify Anki Add-on](https://github.com/ShoroukAziz/Beautify-Anki)
- [miere43's dark titlebar Anki Add-on](https://github.com/miere43/anki-dark-titlebar)
- [AnKingMed's AnkiRecolor Add-on](https://github.com/AnKingMed/AnkiRecolor)

**Changelog:**

- 13-04-2022: Adds major update adding dialog configuration and QT theming as well as some bugfixes and code cleanup (v0.1.0)
- 31-01-2022: Adds minor bugfixes and some code cleanup (v0.0.8)
- 30-01-2022: Adds customized font support, dark titlebar for windows on dark mode, more minor styling fixes (v0.0.7)
- 25-01-2022: Adds typo and error bugfixes, code cleanup update (v0.0.6)
- 24-01-2022: Adds full user customization styling through the folder user_files. User theming is now possible! (v0.0.5)
- 21-01-2022: Adds a very small update, removes unfinished styling on AddCard window (v0.0.4)
- 20-01-2022: Adds styling edits, timer and styling bugfixes, add-on now compatible with legacy versions (v0.0.3)
- 14-01-2022: Adds second update, more styling fixes (v0.0.2)
- 07-01-2022: Styling on Overview and DeckBrowser update (v0.0.1)
- 04-01-2022: Initial Release
