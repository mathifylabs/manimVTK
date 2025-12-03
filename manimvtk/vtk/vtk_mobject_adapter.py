"""VTK Mobject Adapter - Convert Manim mobjects to VTK data structures.

This module provides functions to convert various Manim mobject types
to VTK PolyData objects for export and visualization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from manimvtk.mobject.mobject import Mobject
    from manimvtk.mobject.three_d.three_dimensions import Surface
    from manimvtk.mobject.types.vectorized_mobject import VMobject

__all__ = [
    "vmobject_to_vtk_polydata",
    "surface_to_vtk_polydata",
    "mobject_to_vtk_polydata",
    "add_scalar_field",
    "add_vector_field",
]


def _get_vtk():
    """Lazy import of VTK to avoid import errors when VTK is not installed."""
    try:
        import vtk

        return vtk
    except ImportError as e:
        raise ImportError(
            "VTK is required for the VTK renderer. "
            "Install it with: pip install vtk"
        ) from e


def vmobject_to_vtk_polydata(mobj: VMobject) -> Any:
    """Convert a VMobject (2D shape) to VTK PolyData.

    Parameters
    ----------
    mobj : VMobject
        The VMobject to convert.

    Returns
    -------
    vtkPolyData
        A VTK PolyData object containing the mobject geometry.
    """
    vtk = _get_vtk()

    points = vtk.vtkPoints()
    polys = vtk.vtkCellArray()
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(4)
    colors.SetName("Colors")

    # Get points from the mobject
    pts = mobj.points  # Shape: (N, 3)

    # If the mobject has no direct points but has submobjects (like VGroup),
    # collect geometry from all child mobjects with points
    submobjects = getattr(mobj, "submobjects", [])
    if len(pts) == 0 and len(submobjects) > 0:
        return _vgroup_to_vtk_polydata(mobj)

    if len(pts) == 0:
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        return polydata

    # Add points to vtkPoints
    for p in pts:
        points.InsertNextPoint(float(p[0]), float(p[1]), float(p[2]))

    # Try to get triangulation if available
    try:
        triangulation = mobj.get_triangulation()
        if triangulation is not None and len(triangulation) > 0:
            # Use triangulation indices
            for i in range(0, len(triangulation), 3):
                if i + 2 < len(triangulation):
                    triangle = vtk.vtkTriangle()
                    triangle.GetPointIds().SetId(0, int(triangulation[i]))
                    triangle.GetPointIds().SetId(1, int(triangulation[i + 1]))
                    triangle.GetPointIds().SetId(2, int(triangulation[i + 2]))
                    polys.InsertNextCell(triangle)
        else:
            # Fallback: create polygon from points
            _create_polygon_from_points(vtk, polys, len(pts))
    except (AttributeError, TypeError):
        # No triangulation available, create simple polygon
        _create_polygon_from_points(vtk, polys, len(pts))

    # Get color information
    try:
        color = mobj.get_color()
        rgba = color.to_rgba() if hasattr(color, "to_rgba") else [1.0, 1.0, 1.0, 1.0]
        rgba_int = [int(c * 255) for c in rgba[:3]] + [
            int(mobj.get_fill_opacity() * 255 if hasattr(mobj, "get_fill_opacity") else 255)
        ]
    except Exception:
        rgba_int = [255, 255, 255, 255]

    # Add colors for each point
    for _ in range(len(pts)):
        colors.InsertNextTuple4(*rgba_int)

    # Create PolyData
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(polys)
    polydata.GetPointData().SetScalars(colors)

    return polydata


def _create_polygon_from_points(vtk: Any, polys: Any, num_points: int) -> None:
    """Create a polygon cell from sequential points."""
    if num_points < 3:
        return

    polygon = vtk.vtkPolygon()
    polygon.GetPointIds().SetNumberOfIds(num_points)
    for i in range(num_points):
        polygon.GetPointIds().SetId(i, i)
    polys.InsertNextCell(polygon)


def _vgroup_to_vtk_polydata(mobj: VMobject) -> Any:
    """Convert a VGroup (container of VMobjects) to VTK PolyData.

    This function handles VGroups by recursively collecting geometry from
    all child mobjects that have points, and combining them into a single
    PolyData using vtkAppendPolyData.

    Parameters
    ----------
    mobj : VMobject
        The VGroup or container mobject to convert.

    Returns
    -------
    vtkPolyData
        A VTK PolyData object containing the combined geometry of all children.
    """
    vtk = _get_vtk()

    # Use family_members_with_points to get all leaf mobjects with actual geometry
    members_with_points = mobj.family_members_with_points()

    if not members_with_points:
        # No geometry found, return empty PolyData
        return vtk.vtkPolyData()

    # Use vtkAppendPolyData to combine all child geometries
    append_filter = vtk.vtkAppendPolyData()

    for child in members_with_points:
        # Recursively convert each child to PolyData
        child_polydata = vmobject_to_vtk_polydata(child)
        if child_polydata.GetNumberOfPoints() > 0:
            append_filter.AddInputData(child_polydata)

    if append_filter.GetNumberOfInputConnections(0) == 0:
        # No valid geometry was added
        return vtk.vtkPolyData()

    append_filter.Update()
    return append_filter.GetOutput()


def surface_to_vtk_polydata(
    surface: Surface,
    u_range: tuple[float, float] | None = None,
    v_range: tuple[float, float] | None = None,
    resolution: tuple[int, int] = (50, 50),
) -> Any:
    """Convert a Surface mobject to VTK PolyData.

    Parameters
    ----------
    surface : Surface
        The Surface mobject to convert.
    u_range : tuple[float, float], optional
        The range of the u parameter. If None, uses surface's default.
    v_range : tuple[float, float], optional
        The range of the v parameter. If None, uses surface's default.
    resolution : tuple[int, int]
        The number of points in (u, v) directions.

    Returns
    -------
    vtkPolyData
        A VTK PolyData object containing the surface mesh.
    """
    vtk = _get_vtk()

    # Manim's Surface is a VGroup of patches - collect all points from submobjects
    all_points = []
    for mobject in surface.get_family():
        if hasattr(mobject, "points") and len(mobject.points) > 0:
            all_points.extend(mobject.points)

    if not all_points:
        # Return empty polydata if no points found
        polydata = vtk.vtkPolyData()
        return polydata

    all_points = np.array(all_points)

    # Create VTK points
    points = vtk.vtkPoints()
    for p in all_points:
        points.InsertNextPoint(float(p[0]), float(p[1]), float(p[2]))

    # Get color
    try:
        color = surface.get_color()
        rgba = color.to_rgba() if hasattr(color, "to_rgba") else [1.0, 1.0, 1.0, 1.0]
        rgba_int = [int(c * 255) for c in rgba[:3]] + [255]
    except Exception:
        rgba_int = [255, 255, 255, 255]

    # Add colors for each point
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(4)
    colors.SetName("Colors")
    for _ in range(len(all_points)):
        colors.InsertNextTuple4(*rgba_int)

    # Create polygons from bezier patches
    polys = vtk.vtkCellArray()

    # Manim's 3D surfaces are composed of cubic bezier patches.
    # Each patch uses 16 control points arranged in a 4x4 grid:
    #
    #   0   1   2   3     (row 0)
    #   4   5   6   7     (row 1)
    #   8   9  10  11     (row 2)
    #  12  13  14  15     (row 3)
    #
    # For VTK export, we approximate each bezier patch as two triangles
    # using the four corner control points.
    bezier_patch_size = 4  # 4x4 grid
    num_control_points_per_patch = bezier_patch_size * bezier_patch_size  # 16 points

    # Corner indices within a 4x4 bezier patch (row-major order):
    # Top-left (0,0) = 0, Top-right (0,3) = 3
    # Bottom-left (3,0) = 12, Bottom-right (3,3) = 15
    corner_top_left = 0
    corner_top_right = bezier_patch_size - 1  # 3
    corner_bottom_left = (bezier_patch_size - 1) * bezier_patch_size  # 12
    corner_bottom_right = num_control_points_per_patch - 1  # 15

    num_points = len(all_points)

    for patch_start in range(0, num_points, num_control_points_per_patch):
        if patch_start + num_control_points_per_patch > num_points:
            break

        # Get corner indices for this patch
        corners = [
            patch_start + corner_top_left,
            patch_start + corner_top_right,
            patch_start + corner_bottom_left,
            patch_start + corner_bottom_right,
        ]

        # Triangle 1: top-left, top-right, bottom-left
        tri1 = vtk.vtkTriangle()
        tri1.GetPointIds().SetId(0, corners[0])
        tri1.GetPointIds().SetId(1, corners[1])
        tri1.GetPointIds().SetId(2, corners[2])
        polys.InsertNextCell(tri1)

        # Triangle 2: top-right, bottom-right, bottom-left
        tri2 = vtk.vtkTriangle()
        tri2.GetPointIds().SetId(0, corners[1])
        tri2.GetPointIds().SetId(1, corners[3])
        tri2.GetPointIds().SetId(2, corners[2])
        polys.InsertNextCell(tri2)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(polys)
    polydata.GetPointData().SetScalars(colors)

    return polydata


def mobject_to_vtk_polydata(mobj: Mobject) -> Any:
    """Convert any Mobject to VTK PolyData.

    This is a dispatcher that selects the appropriate conversion
    function based on the mobject type.

    Parameters
    ----------
    mobj : Mobject
        The mobject to convert.

    Returns
    -------
    vtkPolyData
        A VTK PolyData object containing the mobject geometry.
    """
    vtk = _get_vtk()

    # Try to import types for checking
    try:
        from manimvtk.mobject.three_d.three_dimensions import Surface

        if isinstance(mobj, Surface):
            return surface_to_vtk_polydata(mobj)
    except ImportError:
        pass

    try:
        from manimvtk.mobject.types.vectorized_mobject import VMobject

        if isinstance(mobj, VMobject):
            return vmobject_to_vtk_polydata(mobj)
    except ImportError:
        pass

    # Generic fallback: just use points
    points = vtk.vtkPoints()
    pts = mobj.points if hasattr(mobj, "points") else []

    for p in pts:
        points.InsertNextPoint(float(p[0]), float(p[1]), float(p[2]))

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)

    return polydata


def add_scalar_field(polydata: Any, name: str, values: np.ndarray) -> None:
    """Add a scalar field to VTK PolyData for visualization.

    Parameters
    ----------
    polydata : vtkPolyData
        The VTK PolyData to add the scalar field to.
    name : str
        The name of the scalar field (e.g., "pressure", "temperature").
    values : np.ndarray
        Array of scalar values, one per point.
    """
    vtk = _get_vtk()

    arr = vtk.vtkFloatArray()
    arr.SetName(name)
    arr.SetNumberOfComponents(1)

    for val in values:
        arr.InsertNextValue(float(val))

    polydata.GetPointData().AddArray(arr)


def add_vector_field(polydata: Any, name: str, vectors: np.ndarray) -> None:
    """Add a vector field to VTK PolyData for visualization.

    Parameters
    ----------
    polydata : vtkPolyData
        The VTK PolyData to add the vector field to.
    name : str
        The name of the vector field (e.g., "velocity").
    vectors : np.ndarray
        Array of vectors with shape (N, 3), one per point.
    """
    vtk = _get_vtk()

    arr = vtk.vtkFloatArray()
    arr.SetName(name)
    arr.SetNumberOfComponents(3)

    for vec in vectors:
        arr.InsertNextTuple3(float(vec[0]), float(vec[1]), float(vec[2]))

    polydata.GetPointData().SetVectors(arr)
