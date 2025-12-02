"""Pytest configuration for VTK tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def vtk_test_dir():
    """Return the path to the VTK tests directory."""
    return Path(__file__).parent


@pytest.fixture
def vtk_example_scenes_path():
    """Return the path to the VTK example scenes file."""
    return Path(__file__).parent.parent.parent / "example_scenes" / "vtk_examples.py"
