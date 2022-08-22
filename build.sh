#!/bin/bash

# Delete __pycache__
find -name __pycache__ -type d -exec rm -rf {} +

# Delete current add-on package
rm -f anki-redesign.ankiaddon

# Zip add-on (build)
zip -r anki-redesign.ankiaddon files/ injections/ themes/ user_files/ utils/ __init__.py config.json config.md config.py manifest.json
