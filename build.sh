#!/bin/bash
rm -f anki-redesign.ankiaddon
zip -r anki-redesign.ankiaddon files/ user_files/ __init__.py config.json config.md manifest.json utils.py
