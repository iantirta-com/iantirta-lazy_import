# iantirta-lazy_import ⚡
Lazy Import utilities

[![PyPI Version](https://img.shields.io/pypi/v/iantirta-lazy_import.svg)](https://pypi.org/project/iantirta-lazy_import/)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/iantirta-com/iantirta-lazy_import/actions/workflows/test.yml/badge.svg)](https://github.com/iantirta-com/iantirta-lazy_import/actions/workflows/test.yml)
[![Documentation](https://img.shields.io/badge/docs-online-blue.svg)](https://iantirta-com.github.io/iantirta-lazy_import/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](https://github.com/iantirta-com/iantirta-lazy_import/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-iantirta--com-181717?logo=github)](https://github.com/iantirta-com/iantirta-lazy_import)

**`iantirta-lazy_import`** is a zero-dependency, ultra-fast Python utility designed to slash package startup times through intelligent, on-demand lazy module loading. Built for high-performance enterprise and developer ecosystems, it turns heavy initialization sequences into instant sub-millisecond warm starts.

---

## Why Choose `iantirta-lazy_import`?

* **Zero Dependencies:** Built entirely on Python's robust standard library (`importlib`, `re`, `os`). No bloat, no heavy external baggage.
* **Blazing Fast Warm Starts:** Caches directory structures and module maps via `@lru_cache`, reducing initialization overhead to **~0.02 ms**.
* **Smart `__all__` Extraction:** Employs pre-compiled regular expressions that seamlessly parse multi-line lists (`[...]`), tuples (`(...)`), and comment-heavy code blocks.
* **IDE Autocompletion Friendly:** Custom `__dir__` implementation ensures submodules and exported attributes appear cleanly in modern IDE drop-downs before they are loaded into memory.

---

## Installation

Install the package directly from PyPI:

```bash
pip install iantirta-lazy_import
```

For development and testing:

```bash
pip install "iantirta-lazy_import[dev]"
```

## Quick Start
To enable lightning-fast lazy loading for your package, wire it up inside your package's root __init__.py:

```python
from typing import TYPE_CHECKING

from iantirta.lazy_import import define_import_structure, LazyModule

if TYPE_CHECKING:
    # Do something here for typechecking IDE
else:
    import sys

    _file = globals()["__file__"]
    sys.modules[__name__] = LazyModule(
        __name__,
        _file,
        define_import_structure(_file),
        module_spec=__spec__,
        # Optional:
        extra_objects={"__version__": __version__},
    )
```

or You can define the import structure yourself

```python
from typing import TYPE_CHECKING

from iantirta.lazy_import import define_import_structure, LazyModule

_import_structure = {
    "module_name_1": [
        "Class1",
        "method1",
    ],
    "module_name_2": [
        "Class2",
    ],
    "module_name_2.nested": [
        "Class3",
    ]
}

if TYPE_CHECKING:
    # Do something here for typechecking IDE
else:
    import sys

    sys.modules[__name__] = LazyModule(
        __name__,
        globals()["__file__"],
        _import_structure,
        module_spec=__spec__,
    )
```

## The Iantirta Ecosystem
iantirta-lazy_import serves as foundational infrastructure for the Iantirta.com software ecosystem, providing core optimization primitives for enterprise architecture, plugin systems, and modular backends.

## 🛡️ License
Copyright © Iantirta.com. Distributed under the Apache License 2.0. See LICENSE for full details.

Crafted with precision by [https://www.iantirta.com]("https://www.iantirta.com")