"""VTK-based rendering and export for Manim.

This module provides VTK integration for Manim, enabling:
- Export of Manim scenes to VTK file formats (.vtp, .vtm, .pvd)
- Scientific visualization with scalar and vector fields
- Time series animation export for ParaView/PyVista
- Optional offscreen rendering via VTK

Usage::

    manim -pqh MyScene --renderer vtk --vtk-export
"""

from __future__ import annotations

from .vtk_exporter import VTKExporter
from .vtk_mobject_adapter import (
    mobject_to_vtk_polydata,
    surface_to_vtk_polydata,
    vmobject_to_vtk_polydata,
)
from .vtk_renderer import VTKRenderer

__all__ = [
    "VTKRenderer",
    "VTKExporter",
    "vmobject_to_vtk_polydata",
    "surface_to_vtk_polydata",
    "mobject_to_vtk_polydata",
]
