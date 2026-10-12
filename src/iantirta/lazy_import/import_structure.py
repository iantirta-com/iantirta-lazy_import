# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import os
import re
from functools import lru_cache

__all__ = [
    "define_import_structure"
]


IMPORT_STRUCTURE_T = dict[str, set[str]]


# This looks for: __all__ = [ or ( ...anything... ] or )
__ALL__PATTERN_RE = re.compile(r'__all__\s*=\s*[\[\(](.*?)[\]\)]', re.DOTALL)


def fetch__all__(file_content) -> list[str]:
    """
    Returns the content of the __all__ variable in the file content.
    Returns None if not defined, otherwise returns a list of strings.
    """

    if "__all__" not in file_content:
        return []

    match = __ALL__PATTERN_RE.search(file_content)
    if not match:
        # There is no pattern matching `__all__`
        return []

    # This finds anything surrounded by single or double quotes
    return re.findall(r'["\'](.*?)["\']', match.group(1))


@lru_cache
def create_import_structure_from_path(
    module_path: str
):
    import_structure = {}

    if os.path.isfile(module_path):
        module_path = os.path.dirname(module_path)

    adjacent_modules = []

    with os.scandir(module_path) as entries:
        for entry in entries:
            if entry.name == "__pycache__":
                continue
            if entry.is_dir():
                import_structure[entry.name] = create_import_structure_from_path(entry.path)
            elif entry.name.endswith(".py"):
                adjacent_modules.append(entry.name)

    # We're only taking a look at files different from __init__.py
    # We could theoretically require things directly from the __init__.py
    # files, but this is not supported at this time.
    if "__init__.py" in adjacent_modules:
        adjacent_modules.remove("__init__.py")

    
    all_modules = {}
    for module_name in adjacent_modules:
        # Only modules ending in `.py` are accepted here.
        if not module_name.endswith(".py"):
            continue

        with open(os.path.join(module_path, module_name), encoding="utf-8") as f:
            file_content = f.read()

        # Remove the .py suffix
        module_name = module_name[:-3]

        # All objects that are in __all__ should be exported by default.
        # These objects are exported with the file backends.
        exported_objects = set()
        if "__all__" in file_content:
            for _all_object in fetch__all__(file_content):
                if _all_object not in exported_objects:
                    if module_name not in all_modules:
                        all_modules[module_name] = set()

                    all_modules[module_name].add(_all_object)

    import_structure = {**all_modules, **import_structure}
    return import_structure


def spread_import_structure(nested_import_structure):
    ordered_import_structure = nested_import_structure

    def flatten_dict(_dict, previous_key=None):
        items = []
        for _key, _value in _dict.items():
            _key = f"{previous_key}.{_key}" if previous_key is not None else _key
            if isinstance(_value, dict):
                items.extend(flatten_dict(_value, _key).items())
            else:
                items.append((_key, _value))
        return dict(items)
    
    return flatten_dict(ordered_import_structure.copy())


@lru_cache
def define_import_structure(
    module_path: str,
    prefix: str | None = None
):
    import_structure = create_import_structure_from_path(module_path)
    spread_dict = spread_import_structure(import_structure)

    if prefix is None:
        return spread_dict
    else:
        spread_dict = {f"{prefix}.{k}": v for k,v in spread_dict.items()}
        return spread_dict
