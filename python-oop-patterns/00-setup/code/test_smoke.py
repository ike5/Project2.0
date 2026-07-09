"""pytest version of the smoke test."""

import importlib.util
import pathlib

import pytest


def test_python_version() -> None:
    import sys
    assert sys.version_info >= (3, 10)


def test_smoke_script_runs() -> None:
    smoke = pathlib.Path(__file__).parent / "smoke_test.py"
    spec = importlib.util.spec_from_file_location("smoke_test", smoke)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main() == 0
