#!/bin/bash
rm -f anki-redesign.ankiaddon
zip -r anki-redesign.ankiaddon files/ themes/ user_files/ utils/ __init__.py config.json config.md config.py manifest.json
