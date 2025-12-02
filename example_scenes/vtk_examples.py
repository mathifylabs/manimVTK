#!/usr/bin/env python
"""VTK Example Scenes for Manim-VTK.

This file contains example scenes that demonstrate VTK functionality.
Run these examples to verify VTK integration is working correctly.

Usage:
    # Render with Cairo (default) and export VTK files
    manim -pql vtk_examples.py Circle2DExample --vtk-export

    # Render with VTK renderer
    manim -pql vtk_examples.py Circle2DExample --renderer vtk --vtk-export

    # Export time series for ParaView
    manim -pql vtk_examples.py AnimatedCircle --renderer vtk --vtk-time-series

Examples are organized by complexity:
1. Basic 2D shapes
2. Basic 3D shapes
3. Animated scenes
4. Scientific visualization examples
"""

from manim import *

# =============================================================================
# Basic 2D Shape Examples
# =============================================================================


class Circle2DExample(Scene):
    """Basic example: A simple circle.

    This demonstrates the most basic VTK export - a single 2D shape.
    """

    def construct(self):
        circle = Circle(radius=2, color=BLUE, fill_opacity=0.5)
        self.add(circle)
        self.wait()


class Square2DExample(Scene):
    """Basic example: A square with fill.

    Tests VMobject to VTK conversion with fill.
    """

    def construct(self):
        square = Square(side_length=3, color=RED, fill_opacity=0.7)
        self.add(square)
        self.wait()


class MultipleShapes2D(Scene):
    """Multiple 2D shapes for MultiBlock export.

    When exporting multiple mobjects, VTK uses MultiBlock format (.vtm).
    """

    def construct(self):
        circle = Circle(radius=1, color=BLUE).shift(LEFT * 2)
        square = Square(side_length=2, color=RED).shift(RIGHT * 2)
        triangle = Triangle(color=GREEN).shift(UP * 2)

        self.add(circle, square, triangle)
        self.wait()


class PolygonExample(Scene):
    """Custom polygon shapes.

    Tests polygon conversion to VTK PolyData.
    """

    def construct(self):
        # Hexagon
        hexagon = RegularPolygon(n=6, color=PURPLE, fill_opacity=0.6)
        hexagon.scale(2)

        # Pentagon
        pentagon = RegularPolygon(n=5, color=ORANGE, fill_opacity=0.6)
        pentagon.scale(1.5).shift(DOWN)

        self.add(hexagon, pentagon)
        self.wait()


class TextAndShapes(Scene):
    """Text combined with shapes.

    Note: Text rendering may have limited VTK support.
    """

    def construct(self):
        text = Text("Manim-VTK", font_size=48)
        text.shift(UP * 2)

        circle = Circle(radius=1, color=BLUE, fill_opacity=0.5)

        self.add(text, circle)
        self.wait()


# =============================================================================
# Basic 3D Shape Examples
# =============================================================================


class Sphere3DExample(ThreeDScene):
    """Basic 3D example: A sphere.

    Demonstrates 3D mobject to VTK conversion.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        sphere = Sphere(radius=2, resolution=(32, 32))
        sphere.set_color(BLUE)

        self.add(sphere)
        self.wait()


class Cube3DExample(ThreeDScene):
    """Basic 3D example: A cube.

    Tests 3D primitive conversion.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        cube = Cube(side_length=2, fill_opacity=0.8, fill_color=RED)

        self.add(cube)
        self.wait()


class Multiple3DShapes(ThreeDScene):
    """Multiple 3D shapes.

    Tests MultiBlock export with 3D objects.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        sphere = Sphere(radius=1).shift(LEFT * 2 + UP)
        cube = Cube(side_length=1.5, fill_color=RED).shift(RIGHT * 2)
        cylinder = Cylinder(radius=0.5, height=2, fill_color=GREEN).shift(DOWN * 2)

        self.add(sphere, cube, cylinder)
        self.wait()


class ParametricSurfaceExample(ThreeDScene):
    """Parametric surface example.

    This is important for scientific visualization.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        surface = Surface(
            lambda u, v: np.array([u, v, np.sin(u) * np.cos(v)]),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(32, 32),
            fill_color=BLUE,
            fill_opacity=0.8,
        )

        self.add(surface)
        self.wait()


class SaddleSurface(ThreeDScene):
    """Saddle surface (hyperbolic paraboloid).

    A classic mathematical surface for visualization.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        surface = Surface(
            lambda u, v: np.array([u, v, u**2 - v**2]),
            u_range=[-2, 2],
            v_range=[-2, 2],
            resolution=(24, 24),
            fill_color=YELLOW,
            fill_opacity=0.8,
        )

        self.add(surface)
        self.wait()


class TorusSurface(ThreeDScene):
    """Torus (donut shape).

    Tests more complex 3D surface conversion.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        torus = Torus(major_radius=2, minor_radius=0.5)
        torus.set_color(ORANGE)

        self.add(torus)
        self.wait()


# =============================================================================
# Animated Scene Examples
# =============================================================================


class AnimatedCircle(Scene):
    """Animated circle for time series export.

    Use with --vtk-time-series to export frame-by-frame VTK files.
    """

    def construct(self):
        circle = Circle(radius=1, color=BLUE, fill_opacity=0.5)

        self.add(circle)
        self.play(circle.animate.shift(RIGHT * 2), run_time=1)
        self.play(circle.animate.scale(2), run_time=1)
        self.play(circle.animate.set_color(RED), run_time=1)
        self.wait()


class SquareToCircleVTK(Scene):
    """Classic square to circle transformation.

    Demonstrates morphing shapes with VTK export.
    """

    def construct(self):
        square = Square(side_length=2, color=BLUE, fill_opacity=0.5)
        circle = Circle(radius=1, color=RED, fill_opacity=0.5)

        self.add(square)
        self.play(Transform(square, circle), run_time=2)
        self.wait()


class Rotating3DObject(ThreeDScene):
    """Rotating 3D object.

    Time series export will capture the rotation.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=0)

        cube = Cube(side_length=2, fill_color=BLUE, fill_opacity=0.8)
        self.add(cube)

        self.play(Rotate(cube, angle=2 * PI, axis=UP), run_time=3)
        self.wait()


class GrowingSurface(ThreeDScene):
    """Surface that grows over time.

    Good for testing time series surface export.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        surface = Surface(
            lambda u, v: np.array([u, v, 0.1 * np.sin(u) * np.cos(v)]),
            u_range=[-2, 2],
            v_range=[-2, 2],
            resolution=(16, 16),
            fill_color=BLUE,
            fill_opacity=0.8,
        )

        self.add(surface)
        self.play(surface.animate.scale(2), run_time=2)
        self.wait()


# =============================================================================
# Scientific Visualization Examples
# =============================================================================


class WaveSurface(ThreeDScene):
    """Animated wave surface.

    Simulates a wave propagation - useful for physics visualization.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        # Create initial surface
        surface = Surface(
            lambda u, v: np.array([u, v, np.sin(np.sqrt(u**2 + v**2))]),
            u_range=[-4, 4],
            v_range=[-4, 4],
            resolution=(32, 32),
            fill_color=BLUE,
            fill_opacity=0.8,
        )

        self.add(surface)
        self.wait(2)


class PressureFieldVisualization(ThreeDScene):
    """Pressure field on a surface.

    Demonstrates colorscale visualization for CFD applications.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        axes = ThreeDAxes(x_range=[-3, 3], y_range=[-3, 3], z_range=[-2, 2])

        # Surface representing pressure field
        surface = Surface(
            lambda u, v: axes.c2p(u, v, np.sin(u) * np.cos(v)),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(24, 24),
        )

        # Color by z-value (pressure)
        surface.set_fill_by_value(
            axes=axes, colorscale=[BLUE, GREEN, YELLOW, ORANGE, RED], axis=2
        )

        self.add(axes, surface)
        self.wait(2)


class VelocityFieldArrows(ThreeDScene):
    """Velocity field visualization with arrows.

    Shows vector field representation.
    """

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        # Create a grid of arrows representing velocity
        arrows = VGroup()

        for x in np.arange(-2, 2.5, 0.5):
            for y in np.arange(-2, 2.5, 0.5):
                # Velocity field: circular flow
                vx = -y * 0.3
                vy = x * 0.3
                vz = 0

                start = np.array([x, y, 0])
                end = start + np.array([vx, vy, vz])

                arrow = Arrow3D(start, end, resolution=8)
                arrow.set_color(BLUE)
                arrows.add(arrow)

        self.add(arrows)
        self.wait(2)


class ContourPlotExample(ThreeDScene):
    """Contour lines on a surface.

    Shows how contour visualization works with VTK export.
    """

    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=30 * DEGREES)

        axes = ThreeDAxes(x_range=[-3, 3], y_range=[-3, 3], z_range=[-1, 1])

        # Base surface
        surface = Surface(
            lambda u, v: axes.c2p(u, v, np.sin(u) * np.cos(v) * 0.5),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(24, 24),
            fill_color=BLUE,
            fill_opacity=0.6,
        )

        self.add(axes, surface)
        self.wait(2)


# =============================================================================
# Axes and Coordinate Systems
# =============================================================================


class Axes2DExample(Scene):
    """2D axes with plotted function."""

    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 2, 1],
            x_length=8,
            y_length=5,
        )

        graph = axes.plot(lambda x: np.sin(x), color=BLUE)

        self.add(axes, graph)
        self.wait()


class Axes3DExample(ThreeDScene):
    """3D axes example."""

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-2, 2, 1],
        )

        self.add(axes)
        self.wait()


class NumberPlaneExample(Scene):
    """Number plane with grid."""

    def construct(self):
        plane = NumberPlane()
        self.add(plane)

        # Add some shapes on the plane
        dot = Dot(point=[2, 1, 0], color=RED)
        circle = Circle(radius=0.5, color=BLUE).move_to([1, 2, 0])

        self.add(dot, circle)
        self.wait()


# =============================================================================
# VGroup and Complex Mobjects
# =============================================================================


class VGroupExample(Scene):
    """VGroup of multiple shapes.

    Tests grouped mobject export to VTK MultiBlock.
    """

    def construct(self):
        shapes = VGroup()

        for i in range(5):
            circle = Circle(radius=0.5, color=BLUE)
            circle.shift(RIGHT * i - RIGHT * 2)
            shapes.add(circle)

        self.add(shapes)
        self.wait()


class NestedVGroupExample(Scene):
    """Nested VGroups.

    Tests hierarchical mobject structure export.
    """

    def construct(self):
        group1 = VGroup(
            Circle(radius=0.5, color=BLUE).shift(LEFT),
            Square(side_length=1, color=RED).shift(RIGHT),
        )

        group2 = VGroup(
            Triangle(color=GREEN).shift(UP * 2),
            RegularPolygon(n=5, color=YELLOW).shift(DOWN * 2),
        )

        all_shapes = VGroup(group1, group2)
        self.add(all_shapes)
        self.wait()


# =============================================================================
# Edge Cases and Stress Tests
# =============================================================================


class EmptyScene(Scene):
    """Empty scene for edge case testing."""

    def construct(self):
        self.wait(0.1)


class ManyShapes(Scene):
    """Scene with many shapes.

    Stress test for VTK export performance.
    """

    def construct(self):
        shapes = VGroup()

        for i in range(10):
            for j in range(10):
                circle = Circle(radius=0.2, color=BLUE, fill_opacity=0.5)
                circle.move_to([i - 5, j - 5, 0])
                shapes.add(circle)

        self.add(shapes)
        self.wait()


class TinyMobject(Scene):
    """Very small mobjects."""

    def construct(self):
        dot = Dot(point=[0, 0, 0], radius=0.01)
        self.add(dot)
        self.wait()


class LargeMobject(Scene):
    """Very large mobject."""

    def construct(self):
        circle = Circle(radius=10, color=BLUE, fill_opacity=0.5)
        self.add(circle)
        self.wait()


# =============================================================================
# Combined Examples
# =============================================================================


class FullDemo(ThreeDScene):
    """Comprehensive demo combining multiple features.

    This scene demonstrates multiple VTK capabilities:
    - 2D and 3D shapes
    - Animations
    - Multiple mobjects
    - Camera movement
    """

    def construct(self):
        # Start with 2D
        circle = Circle(radius=1, color=BLUE, fill_opacity=0.5)
        self.add(circle)
        self.wait(0.5)

        # Transform to 3D view
        self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES)

        # Add 3D shapes
        sphere = Sphere(radius=0.5).shift(UP * 2)
        cube = Cube(side_length=1, fill_color=RED).shift(DOWN * 2)

        self.add(sphere, cube)
        self.wait(0.5)

        # Animate
        self.play(sphere.animate.shift(RIGHT * 2), run_time=1)
        self.play(Rotate(cube, angle=PI / 2, axis=UP), run_time=1)
        self.wait()


# List of all example scenes for easy access
EXAMPLE_SCENES = [
    # Basic 2D
    Circle2DExample,
    Square2DExample,
    MultipleShapes2D,
    PolygonExample,
    TextAndShapes,
    # Basic 3D
    Sphere3DExample,
    Cube3DExample,
    Multiple3DShapes,
    ParametricSurfaceExample,
    SaddleSurface,
    TorusSurface,
    # Animated
    AnimatedCircle,
    SquareToCircleVTK,
    Rotating3DObject,
    GrowingSurface,
    # Scientific
    WaveSurface,
    PressureFieldVisualization,
    VelocityFieldArrows,
    ContourPlotExample,
    # Axes
    Axes2DExample,
    Axes3DExample,
    NumberPlaneExample,
    # Complex
    VGroupExample,
    NestedVGroupExample,
    # Edge cases
    EmptyScene,
    ManyShapes,
    TinyMobject,
    LargeMobject,
    # Full demo
    FullDemo,
]


if __name__ == "__main__":
    print("VTK Example Scenes available:")
    print("=" * 50)
    for scene in EXAMPLE_SCENES:
        print(f"  - {scene.__name__}")
    print()
    print("Run with: manim -pql vtk_examples.py <SceneName> --vtk-export")
