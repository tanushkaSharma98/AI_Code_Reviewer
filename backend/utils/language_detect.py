import os
import json
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound

EXTENSION_LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.md': 'Markdown',
    '.txt': 'Text',
}

def detect_language_by_extension(filename):
    _, ext = os.path.splitext(filename)
    return EXTENSION_LANGUAGE_MAP.get(ext.lower(), None)

def detect_language_by_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        lexer = guess_lexer_for_filename(filepath, code)
        return lexer.name
    except (ClassNotFound, Exception):
        return None

def detect_languages_in_dir(directory):
    file_langs = {}
    for root, _, files in os.walk(directory):
        for fname in files:
            fpath = os.path.join(root, fname)
            lang = detect_language_by_extension(fname)
            if not lang:
                lang = detect_language_by_content(fpath)
            file_langs[os.path.relpath(fpath, directory)] = lang or 'Unknown'
    return file_langs

def save_language_map(directory, lang_map):
    out_path = os.path.join(directory, 'file_languages.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(lang_map, f, indent=2) 