"""Session 0 smoke test: the scaffold imports cleanly."""

import importlib


def test_scaffold_imports():
    for name in [
        "resolver.models",
        "resolver.calc",
        "resolver.codes",
        "resolver.retrieve",
        "resolver.rules",
        "resolver.audit",
        "resolver.model",
        "resolver.pipeline",
    ]:
        importlib.import_module(name)
