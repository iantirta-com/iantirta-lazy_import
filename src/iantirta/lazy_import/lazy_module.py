
import importlib
import importlib.machinery
import logging
import os
from itertools import chain
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .import_structure import IMPORT_STRUCTURE_T


__all__ = [
    "LazyModule",
]


logger = logging.getLogger(__name__)


class LazyModule(ModuleType):
    # Very heavily inspired by optuna.integration._IntegrationModule
    # https://github.com/optuna/optuna/blob/master/optuna/integration/__init__.py
    def __init__(
        self,
        name: str,
        module_file: str,
        import_structure: "IMPORT_STRUCTURE_T",
        module_spec: importlib.machinery.ModuleSpec | None = None,
        extra_objects: dict[str, object] | None = None,
        explicit_import_shortcut: dict[str, list[str]] | None = None,
    ):
        super().__init__(name)

        self._explicit_import_shortcut = explicit_import_shortcut if explicit_import_shortcut else {}

        self._modules = set(import_structure.keys())

        self._class_to_module = {}
        for key, values in import_structure.items():
            for value in values:
                self._class_to_module[value] = key

        self.__all__ = list(import_structure.keys()) + list(chain(*import_structure.values()))
        self.__file__ = module_file
        self.__spec__ = module_spec
        self.__path__ = [os.path.dirname(module_file)]
        self._objects = {} if extra_objects is None else extra_objects
        self._name = name
        self._import_structure = import_structure

    # Needed for autocompletion in an IDE
    def __dir__(self):
        result = list(super().__dir__())
        # The elements of self.__all__ that are submodules may or may not be in the dir already, depending on whether
        # they have been accessed or not. So we only add the elements of self.__all__ that are not already in the dir.
        for attr in self.__all__:
            if attr not in result:
                result.append(attr)
        return result
    
    def __getattr__(self, name: str) -> Any:
        if name in self._objects:
            return self._objects[name]

        import_error_message = (
            f"Could not import module '{name}'. Are this object's requirements defined correctly? "
            "Set the logging verbosity to DEBUG for the original import error."
        )
        if name in self._class_to_module:
            try:
                module = self._get_module(self._class_to_module[name])
                value = getattr(module, name)
            except (ModuleNotFoundError, RuntimeError, AttributeError) as e:
                logger.debug(f"Original import error for '{name}': {e}")
                raise ModuleNotFoundError(import_error_message) from e
        elif name in self._modules:
            try:
                value = self._get_module(name)
            except (ModuleNotFoundError, RuntimeError) as e:
                logger.debug(f"Original import error for '{name}': {e}")
                raise ModuleNotFoundError(import_error_message) from e
        else:
            value = None

            if value is None:
                for key, values in self._explicit_import_shortcut.items():
                    if name in values:
                        value = self._get_module(key)
                        break

            if value is None:
                raise AttributeError(f"module {self.__name__} has no attribute {name}")

        setattr(self, name, value)
        return value

    def _get_module(self, module_name: str):
        try:
            return importlib.import_module("." + module_name, self.__name__)
        except Exception as e:
            print(
                f"\n!! FAILED IMPORT"
                f"\n   package: {self.__name__}"
                f"\n   module:  {module_name}"
                f"\n   error:   {type(e).__name__}: {e}\n"
            )
            raise

    def __reduce__(self):
        return (self.__class__, (self._name, self.__file__, self._import_structure))
