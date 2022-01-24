# Anki-redesign

> A new lightweight look for Anki compatible with most (if not all) versions of Anki 2.1.X running QT5. - Specifically tested on Anki 2.1.49

Note: This add-on doesn't overwrite the original Anki code views that much, meaning that most add-ons should properly work with Anki-redesign enabled. However, if there is any add-on found to not be working properly, feel free to make an [issue](https://github.com/Shirajuki/anki-redesign/issues) and I'll try to add support for it!
(List of tested addons and manual fixes for them to work can be seen on the [project github wiki](https://github.com/Shirajuki/anki-redesign/wiki/Compatible-Add-ons-for-Anki-2.1).)

Note2: **This addon also works as a theming addon**, as it enables the possibility of user customization on almost all Anki views/windows through the injection of CSS and QT CSS on the different components.

Note3: If the addon is not updating try open anki while holding shift to turn off all addons, then update and restart. :)

**Manually tested on the following Anki versions:**
- 2.1.49
- 2.1.26
- 2.1.22

**Planned updates / todos (since 20.01.2022):**
- [x] Minor design fixes for a cleaner design (v0.0.2)
- [x] Fix light-mode design and better contrasts (v0.0.2)
- [x] Adds a primary color of choice and more lightweight user defined customizations through config file (v0.0.3)
- [x] Fix bug where deck timer appears on top of the show answer button (v0.0.3)
- [x] Addon said not be working on Anki version 2.1.22, manually fix this (v0.0.3)
- [x] Fix problem with darkmode Mac Computers (v0.0.3)
- [x] Removes unfinished styling on dialog windows - AddCards (v0.0.4)
- [x] Adds user customization on all styling views through the user_files folder (user custom CSS injection) (v0.0.5)
- [ ] Adds more lightweight modern styling for other views / dialogs
- [ ] Manually test for backwards compatibility on older Anki versions. (v2.1.22 tested)

<br/>
<div><img src="./screenshots/ui-half.png"></div>
<br/>

**Credits:**

The concept of this add-on was inspired by the following add-on and designs:

- [Developer Nick's Redesign Add-on](https://github.com/nickdvlpr/Redesign)
- [Yanyi Yoong's Anki Reimagine](https://www.behance.net/gallery/50253077/Anki-Reimagine)
- [Beatify Anki Add-on](https://github.com/ShoroukAziz/Beautify-Anki)

**Changelog:**
- 24-01-2022: Add full user customization styling through the folder user_files. User theming is now possible! (v0.0.5)
- 21-01-2022: Adds a very small update, removes unfinished styling on AddCard window (v0.0.4)
- 20-01-2022: Adds styling edits, timer and styling bugfixes, add-on now compatible with legacy versions (v0.0.3)
- 14-01-2022: Adds second update, more styling fixes (v0.0.2)
- 07-01-2022: Styling on Overview and DeckBrowser update (v0.0.1)
- 04-01-2022: Initial Release