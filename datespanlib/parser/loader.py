# DateSpanLib - Copyright (c)2024, Thomas Zeutschler, MIT license
# ------------------------------------------------------------------------------------------------
# Provides methods to load language specific parsers
# ------------------------------------------------------------------------------------------------
# Language parsers need to be located in respective subfolders of the "datespanlib/parser" folder,
# e.g. "datespanlib/parser/en" for English language parser. Within this folder, the parser class
# named "DateTextParser" needs to be declared in the respective __init__.py file.
# Please refer the "en" parser implementation for further details

import sys
import pathlib


language_parsers = {}  # available language parsers

def load_language_parsers():
    # Loads all available language parsers.
    for language in get_installed_languages():
        language_parsers[language] = load_language(language)

def get_installed_languages() -> list[str]:
    # Returns a list of the installed/available languages for parsing date, time or date span texts.
    parser_folder = pathlib.Path(__file__).parent.resolve()
    languages = []
    if parser_folder.exists():
        for item in parser_folder.iterdir():
            if item.is_dir():
                # check for folders like "en" or "en_US"
                if len(item.name) == 2 or (len(item.name) == 5 and item.name[2] == "_"):
                    languages.append(item.name)
    return languages

def load_language(language: str):
    # Loads the parser instance for the given language.
    modul_path = f'datespanlib.parser.{language}.DateTextParser'
    modul_name = f'datespanlib.parser.{language}'
    class_name = 'DateTextParser'

    if modul_name in sys.modules:
        module = sys.modules[modul_name]
        if hasattr(module, class_name):
            return getattr(module, class_name)() # create class instance
        else:
            raise ImportError(f"Failed to load parser class '{class_name}' from module '{modul_name}'.")

    components = modul_path.split('.')
    mod = __import__(".".join(components[:-1]))
    for comp in components[1:]:
        mod = getattr(mod, comp)
    if callable(mod):
        return mod() # create class instance
