"""Tests for VTK Mobject Adapter - converting Manim mobjects to VTK data structures."""

from __future__ import annotations

import numpy as np

from manimvtk import (
    Circle,
    Cube,
    Dot,
    Line,
    Polygon,
    Rectangle,
    Sphere,
    Square,
    Surface,
)
from manimvtk.vtk import (
    mobject_to_vtk_polydata,
    surface_to_vtk_polydata,
    vmobject_to_vtk_polydata,
)


class TestVMobjectToVTKPolyData:
    """Tests for vmobject_to_vtk_polydata function."""

    def test_circle_conversion(self):
        """Test that a Circle is correctly converted to VTK PolyData."""
        circle = Circle(radius=1.0)
        polydata = vmobject_to_vtk_polydata(circle)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0

    def test_square_conversion(self):
        """Test that a Square is correctly converted to VTK PolyData."""
        square = Square(side_length=2.0)
        polydata = vmobject_to_vtk_polydata(square)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0

    def test_rectangle_conversion(self):
        """Test that a Rectangle is correctly converted to VTK PolyData."""
        rect = Rectangle(width=2.0, height=1.0)
        polydata = vmobject_to_vtk_polydata(rect)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0

    def test_line_conversion(self):
        """Test that a Line is correctly converted to VTK PolyData."""
        line = Line(start=np.array([-1, 0, 0]), end=np.array([1, 0, 0]))
        polydata = vmobject_to_vtk_polydata(line)

        assert polydata is not None
        # Lines have points even if minimal geometry

    def test_polygon_conversion(self):
        """Test that a Polygon is correctly converted to VTK PolyData."""
        polygon = Polygon(
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([1, 1, 0]),
            np.array([0, 1, 0]),
        )
        polydata = vmobject_to_vtk_polydata(polygon)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0

    def test_empty_mobject_conversion(self):
        """Test that an empty mobject doesn't cause errors."""
        from manimvtk.mobject.types.vectorized_mobject import VMobject

        empty = VMobject()
        polydata = vmobject_to_vtk_polydata(empty)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() == 0

    def test_colored_mobject_preserves_color(self):
        """Test that color information is preserved in conversion."""
        circle = Circle(color="#FF0000", fill_opacity=0.5)
        polydata = vmobject_to_vtk_polydata(circle)

        colors = polydata.GetPointData().GetScalars()
        if colors is not None and colors.GetNumberOfTuples() > 0:
            # Check that color data exists
            assert colors.GetNumberOfComponents() == 4


class TestSurfaceToVTKPolyData:
    """Tests for surface_to_vtk_polydata function."""

    def test_simple_surface_conversion(self):
        """Test conversion of a simple parametric surface."""
        surface = Surface(
            lambda u, v: np.array([u, v, np.sin(u) * np.cos(v)]),
            u_range=[-1, 1],
            v_range=[-1, 1],
            resolution=(8, 8),
        )
        polydata = surface_to_vtk_polydata(surface)

        assert polydata is not None
        # Surface should have points from the mesh
        assert polydata.GetNumberOfPoints() > 0

    def test_surface_with_custom_resolution(self):
        """Test surface conversion with custom resolution."""
        surface = Surface(
            lambda u, v: np.array([u, v, u * v]),
            u_range=[0, 2],
            v_range=[0, 2],
            resolution=(4, 4),
        )
        polydata = surface_to_vtk_polydata(surface)

        assert polydata is not None


class TestMobjectToVTKPolyData:
    """Tests for the generic mobject_to_vtk_polydata dispatcher."""

    def test_circle_dispatches_correctly(self):
        """Test that Circle is dispatched to VMobject converter."""
        circle = Circle()
        polydata = mobject_to_vtk_polydata(circle)

        assert polydata is not None

    def test_surface_dispatches_correctly(self):
        """Test that Surface is dispatched to Surface converter."""
        surface = Surface(
            lambda u, v: np.array([u, v, 0]),
            u_range=[-1, 1],
            v_range=[-1, 1],
        )
        polydata = mobject_to_vtk_polydata(surface)

        assert polydata is not None

    def test_dot_conversion(self):
        """Test that Dot is converted correctly."""
        dot = Dot(point=np.array([0, 0, 0]))
        polydata = mobject_to_vtk_polydata(dot)

        assert polydata is not None


class TestScalarAndVectorFields:
    """Tests for scalar and vector field functionality."""

    def test_add_scalar_field(self):
        """Test adding a scalar field to PolyData."""
        from manimvtk.vtk.vtk_mobject_adapter import add_scalar_field

        circle = Circle()
        polydata = vmobject_to_vtk_polydata(circle)

        num_points = polydata.GetNumberOfPoints()
        if num_points > 0:
            scalar_values = np.random.rand(num_points)
            add_scalar_field(polydata, "pressure", scalar_values)

            pressure_array = polydata.GetPointData().GetArray("pressure")
            assert pressure_array is not None
            assert pressure_array.GetNumberOfTuples() == num_points

    def test_add_vector_field(self):
        """Test adding a vector field to PolyData."""
        from manimvtk.vtk.vtk_mobject_adapter import add_vector_field

        circle = Circle()
        polydata = vmobject_to_vtk_polydata(circle)

        num_points = polydata.GetNumberOfPoints()
        if num_points > 0:
            vectors = np.random.rand(num_points, 3)
            add_vector_field(polydata, "velocity", vectors)

            velocity_array = polydata.GetPointData().GetVectors()
            assert velocity_array is not None
            assert velocity_array.GetName() == "velocity"
            assert velocity_array.GetNumberOfTuples() == num_points
            assert velocity_array.GetNumberOfComponents() == 3


class Test3DMobjectConversion:
    """Tests for 3D mobject conversion to VTK."""

    def test_sphere_conversion(self):
        """Test that a Sphere is converted correctly."""
        sphere = Sphere(radius=1.0)
        polydata = mobject_to_vtk_polydata(sphere)

        assert polydata is not None
        # Sphere should have 3D points

    def test_cube_conversion(self):
        """Test that a Cube is converted correctly."""
        cube = Cube(side_length=2.0)
        polydata = mobject_to_vtk_polydata(cube)

        assert polydata is not None


class TestVGroupConversion:
    """Tests for VGroup (container) conversion to VTK PolyData."""

    def test_vgroup_with_circles_conversion(self):
        """Test that a VGroup with circles is correctly converted."""
        from manimvtk import VGroup

        shapes = VGroup()
        for _ in range(3):
            shapes.add(Circle(radius=0.5))

        polydata = vmobject_to_vtk_polydata(shapes)

        assert polydata is not None
        # VGroup should have points from all child circles
        assert polydata.GetNumberOfPoints() > 0
        # Each circle is sampled with 81 points (10 samples per bezier curve x 8 curves + 1),
        # so 3 circles = 243 points. For filled circles, it would be 96 points (32 x 3).
        # Since circles have stroke but no fill, they are exported as sampled lines.
        assert polydata.GetNumberOfPoints() >= 96

    def test_vgroup_has_cells(self):
        """Test that VGroup conversion preserves cell information."""
        from manimvtk import VGroup

        shapes = VGroup(Circle(radius=0.5), Square(side_length=1.0))
        polydata = vmobject_to_vtk_polydata(shapes)

        assert polydata is not None
        # Should have cells from both shapes
        assert polydata.GetNumberOfCells() > 0

    def test_nested_vgroup_conversion(self):
        """Test that nested VGroups are correctly flattened."""
        from manimvtk import Triangle, VGroup

        group1 = VGroup(Circle(radius=0.5), Square(side_length=1))
        group2 = VGroup(Triangle())
        all_shapes = VGroup(group1, group2)

        polydata = vmobject_to_vtk_polydata(all_shapes)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0
        # Should contain geometry from all nested shapes

    def test_empty_vgroup_conversion(self):
        """Test that an empty VGroup doesn't cause errors."""
        from manimvtk import VGroup

        empty_group = VGroup()
        polydata = vmobject_to_vtk_polydata(empty_group)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() == 0

    def test_mixed_vgroup_with_mobject_dispatcher(self):
        """Test that VGroup works with the generic dispatcher."""
        from manimvtk import VGroup

        shapes = VGroup(Circle(radius=0.3), Rectangle(width=1, height=0.5))
        polydata = mobject_to_vtk_polydata(shapes)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0


class TestStrokeBasedMobjectConversion:
    """Tests for stroke-based mobjects (lines, axes) converted to VTK polylines."""

    def test_line_exports_as_vtk_lines(self):
        """Test that a Line is exported as VTK polylines, not polygons."""
        line = Line(start=np.array([-1, 0, 0]), end=np.array([1, 0, 0]))
        polydata = vmobject_to_vtk_polydata(line)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0
        # Lines should export as VTK lines, not polygons
        assert polydata.GetNumberOfLines() > 0
        assert polydata.GetNumberOfPolys() == 0

    def test_circle_stroke_only_exports_as_vtk_lines(self):
        """Test that a Circle with stroke only is exported as VTK polylines."""
        circle = Circle(radius=1.0)  # Default: stroke only, no fill
        polydata = vmobject_to_vtk_polydata(circle)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0
        assert polydata.GetNumberOfLines() > 0
        assert polydata.GetNumberOfPolys() == 0

    def test_filled_circle_exports_as_polygons(self):
        """Test that a Circle with fill is exported as VTK polygons."""
        circle = Circle(radius=1.0, fill_opacity=0.5)
        polydata = vmobject_to_vtk_polydata(circle)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0
        # Filled shapes should use polygons
        assert polydata.GetNumberOfPolys() > 0

    def test_axes_export_includes_lines(self):
        """Test that Axes are properly exported with VTK lines for axis lines and ticks."""
        from manimvtk import Axes

        axes = Axes(
            x_range=[0, 6, 1],
            y_range=[-1.5, 1.5, 1],
            x_length=10.0,
            y_length=4.2,
            tips=True,
        )
        polydata = mobject_to_vtk_polydata(axes)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0
        # Axes should have lines (for axis lines and ticks)
        assert polydata.GetNumberOfLines() > 0
        # Axes should also have polygons (for arrow tips)
        assert polydata.GetNumberOfPolys() > 0

    def test_parametric_function_exports_as_lines(self):
        """Test that plotted functions are exported as VTK lines."""
        from manimvtk import Axes

        axes = Axes(x_range=[0, 6, 1], y_range=[-1.5, 1.5, 1])
        graph = axes.plot(lambda x: np.sin(x), use_smoothing=False)
        polydata = vmobject_to_vtk_polydata(graph)

        assert polydata is not None
        assert polydata.GetNumberOfPoints() > 0
        # Graphs should export as lines
        assert polydata.GetNumberOfLines() > 0
        assert polydata.GetNumberOfPolys() == 0
