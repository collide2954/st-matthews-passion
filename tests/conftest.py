"""Settings for the tests.

The tests of the engine (the music language, the notation, the performance)
come from Night Music for Orchestra. They use a large modern orchestra with
percussion, a piano, and instruments that change. That orchestra is in
`tests/data/orchestra.toml`. The tests of this work use `design/orchestra.toml`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ENGINE_TESTS = {
    "test_combine",
    "test_compose",
    "test_cues",
    "test_musicxml",
    "test_notation",
    "test_perform",
    "test_piano",
    "test_stemtone",
}


@pytest.fixture(autouse=True)
def _orchestra_of_the_engine_tests(request, monkeypatch):
    """Give the tests of the engine the large test orchestra."""
    if request.module.__name__.rpartition(".")[2] in ENGINE_TESTS:
        from stmatthew.notation import work

        monkeypatch.setattr(work, "DESIGN_DIR", Path(__file__).parent / "data")
