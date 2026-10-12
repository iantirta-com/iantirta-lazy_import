import sys
from pathlib import Path

import pytest

from iantirta.lazy_import.import_structure import (
    create_import_structure_from_path,
    define_import_structure,
    fetch__all__,
)
from iantirta.lazy_import.lazy_module import LazyModule


def test_fetch_all_single_line_list():
    content = '__all__ = ["Foo", "Bar"]'
    assert fetch__all__(content) == ["Foo", "Bar"]


def test_fetch_all_single_line_list_with_comment():
    content = '__all__ = ["Foo", "Bar"]  # type: ignore'
    assert fetch__all__(content) == ["Foo", "Bar"]


def test_fetch_all_multi_line_tuple():
    content = """
    __all__ = (
        "ClassA",
        'ClassB',
        "HelperFunc",
    )
    """
    assert fetch__all__(content) == ["ClassA", "ClassB", "HelperFunc"]


def test_fetch_all_multi_line_tuple_with_comment():
    content = """
    __all__ = (  # type: ignore
        "ClassA",
        'ClassB',  # type: ignore
        "HelperFunc",
    )  # type: ignore
    """
    assert fetch__all__(content) == ["ClassA", "ClassB", "HelperFunc"]


def test_fetch_all_missing():
    content = "x = 10\ny = 20"
    assert fetch__all__(content) == []


def test_create_import_structure(tmp_path: Path):
    # Setup mock file structure
    # tmp_path/
    #   ├── model_a.py (has __all__)
    #   ├── model_b.py (has multi-line __all__)
    #   ├── ignore_me.py (no __all__)
    #   └── sub_folder/
    #       └── model_c.py (has __all__)
    
    (tmp_path / "model_a.py").write_text('__all__ = ["ItemA"]')
    (tmp_path / "model_b.py").write_text('__all__ = (\n    "ItemB1",\n    "ItemB2"\n)')
    (tmp_path / "ignore_me.py").write_text('X = 99')
    
    sub = tmp_path / "sub_folder"
    sub.mkdir()
    (sub / "model_c.py").write_text('__all__ = ["ItemC"]')

    structure = create_import_structure_from_path(str(tmp_path))

    # Verify nested and flat structure mapping
    assert "model_a" in structure
    assert structure["model_a"] == {"ItemA"}
    assert structure["model_b"] == {"ItemB1", "ItemB2"}
    assert "ignore_me" not in structure
    assert "sub_folder" in structure
    assert structure["sub_folder"]["model_c"] == {"ItemC"}


def test_define_import_structure_with_prefix(tmp_path: Path):
    (tmp_path / "mod.py").write_text('__all__ = ["Obj1"]')
    
    struct = define_import_structure(str(tmp_path), prefix="iantirta.models")
    assert "iantirta.models.mod" in struct


def test_lazy_module_behavior(tmp_path: Path):
    # Create an actual importable package structure in temp path for LazyModule testing
    pkg_dir = tmp_path / "testpkg"
    pkg_dir.mkdir()
    
    # Init file for package
    (pkg_dir / "__init__.py").write_text("")
    
    # Submodule with export
    (pkg_dir / "core.py").write_text('__all__ = ["CoolClass"]\nclass CoolClass: pass')

    # Add temp path to sys.path so importlib can resolve testpkg
    sys.path.insert(0, str(tmp_path))

    try:
        import_structure = define_import_structure(str(pkg_dir))
        
        # Instantiate LazyModule
        lazy_mod = LazyModule(
            name="testpkg",
            module_file=str(pkg_dir / "__init__.py"),
            import_structure=import_structure
        )

        # 1. Test __dir__ autocompletion inclusion
        dir_listing = dir(lazy_mod)
        assert "core" in dir_listing
        assert "CoolClass" in dir_listing

        # 2. Test attribute lookup triggering lazy import
        obj = lazy_mod.CoolClass
        assert obj.__name__ == "CoolClass"

        # 3. Test caching behavior (subsequent calls hit instance __dict__ directly)
        assert "CoolClass" in lazy_mod.__dict__

        # 4. Test invalid attribute raises AttributeError
        with pytest.raises(AttributeError):
            _ = lazy_mod.NonExistentAttribute

    finally:
        sys.path.pop(0)
