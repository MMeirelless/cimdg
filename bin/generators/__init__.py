"""
CIM data model generators for synthetic event creation.

Auto-discovers and imports all generator modules in this package,
registering them with the GeneratorFactory via @register_generator.
"""

import importlib
import os
import pkgutil

_pkg_dir = os.path.dirname(__file__)
_skip = {"base", "correlation"}

for _importer, _modname, _ispkg in pkgutil.iter_modules([_pkg_dir]):
    if _modname not in _skip:
        importlib.import_module(f".{_modname}", __package__)
