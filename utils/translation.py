
import os
import json

this_script_dir = os.path.join(os.path.dirname(__file__), "..")
translation_dir = os.path.join(this_script_dir, 'translation')

def get_texts_dict() -> dict:
    texts = {}
    for file in os.listdir(translation_dir):
        if "json" in file:
            file = file.replace(".json", "")
            if texts.get(file, "") == "":
                texts_path = os.path.join(translation_dir, file+'.json')
                texts_parsed = json.loads(open(texts_path, encoding='utf-8').read())
                texts[file] = texts_parsed
    return texts

def get_texts(lang: str) -> dict:
    texts = get_texts_dict()
    return texts.get(lang, texts["en_US"])

texts = get_texts_dict()