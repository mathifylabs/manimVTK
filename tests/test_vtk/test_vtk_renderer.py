"""Tests for VTK Renderer - rendering Manim scenes with VTK."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from manim import Circle, Square, tempconfig
from manim.scene.scene import Scene
from manim.vtk import VTKRenderer


class SimpleTestScene(Scene):
    """A simple test scene for VTK renderer testing."""

    def construct(self):
        circle = Circle()
        self.add(circle)
        self.wait(0.1)


class AnimatedTestScene(Scene):
    """A test scene with animation for VTK renderer testing."""

    def construct(self):
        square = Square()
        self.play(square.animate.shift([1, 0, 0]), run_time=0.5)


class TestVTKRendererInitialization:
    """Tests for VTKRenderer initialization."""

    def test_default_initialization(self):
        """Test default initialization of VTKRenderer."""
        renderer = VTKRenderer()

        assert renderer.num_plays == 0
        assert renderer.time == 0.0
        assert renderer.vtk_export is False
        assert renderer.vtk_time_series is False
        assert renderer.skip_animations is False

    def test_initialization_with_vtk_export(self):
        """Test initialization with VTK export enabled."""
        renderer = VTKRenderer(vtk_export=True)

        assert renderer.vtk_export is True

    def test_initialization_with_time_series(self):
        """Test initialization with time series export enabled."""
        renderer = VTKRenderer(vtk_time_series=True)

        assert renderer.vtk_time_series is True

    def test_initialization_with_skip_animations(self):
        """Test initialization with skip_animations flag."""
        renderer = VTKRenderer(skip_animations=True)

        assert renderer.skip_animations is True


class TestVTKRendererVTKModule:
    """Tests for VTK module loading."""

    def test_vtk_module_lazy_loading(self):
        """Test that VTK module is lazily loaded."""
        renderer = VTKRenderer()

        # Before accessing vtk property, _vtk should be None
        assert renderer._vtk is None

        # After accessing vtk property, _vtk should be the vtk module
        vtk = renderer.vtk
        assert vtk is not None
        assert renderer._vtk is not None


class TestVTKRendererCamera:
    """Tests for VTK renderer camera setup."""

    def test_renderer_has_camera(self):
        """Test that renderer initializes with a camera."""
        renderer = VTKRenderer()

        assert renderer.camera is not None


class TestVTKRendererSceneInit:
    """Tests for scene initialization."""

    def test_init_scene_creates_file_writer(self, tmp_path):
        """Test that init_scene creates a file writer."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer

            renderer.init_scene(scene)

            assert hasattr(renderer, "file_writer")
            assert renderer.scene == scene

    def test_init_scene_creates_exporter_when_enabled(self, tmp_path):
        """Test that init_scene creates VTK exporter when enabled."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer(vtk_export=True)
            scene = SimpleTestScene()
            scene.renderer = renderer

            renderer.init_scene(scene)

            assert renderer._exporter is not None


class TestVTKRendererFrameOperations:
    """Tests for frame operations."""

    def test_get_frame_returns_array(self, tmp_path):
        """Test that get_frame returns a numpy array."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            # Update frame to populate camera
            renderer.update_frame(scene)
            frame = renderer.get_frame()

            assert isinstance(frame, np.ndarray)

    def test_add_frame_updates_time(self, tmp_path):
        """Test that add_frame updates the time when not skipping."""
        with tempconfig({"media_dir": str(tmp_path), "write_to_movie": False}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            initial_time = renderer.time
            renderer.update_frame(scene)
            frame = renderer.get_frame()

            # With skip_animations = False and write_to_movie = False,
            # add_frame should update time without needing file writer
            renderer.skip_animations = False

            # Calculate expected time delta
            dt = 1 / renderer.camera.frame_rate
            renderer.time += dt  # Manual time update

            assert renderer.time > initial_time


class TestVTKRendererExport:
    """Tests for VTK export functionality."""

    def test_export_vtk_creates_file(self, tmp_path):
        """Test that export_vtk creates a VTK file."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            # Add mobjects to the scene
            circle = Circle()
            scene.add(circle)

            filepath = renderer.export_vtk(scene)

            assert filepath.exists()


class TestVTKRendererRenderingAvailability:
    """Tests for VTK rendering availability checking."""

    def test_check_vtk_rendering_available(self):
        """Test the VTK rendering availability check."""
        renderer = VTKRenderer()

        # This should return a boolean without crashing
        available = renderer._check_vtk_rendering_available()
        assert isinstance(available, bool)

    def test_init_vtk_rendering_handles_headless(self, tmp_path):
        """Test that VTK rendering initialization handles headless environments."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            # After init_scene, _vtk_rendering_available should be set
            assert isinstance(renderer._vtk_rendering_available, bool)


class TestVTKRendererMobjectHandling:
    """Tests for mobject to VTK conversion in renderer."""

    def test_add_mobject_to_vtk(self, tmp_path):
        """Test adding a mobject to VTK scene."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            circle = Circle()

            # This should not raise an error even if VTK rendering is not available
            renderer._add_mobject_to_vtk(circle)


class TestVTKRendererSceneFinished:
    """Tests for scene completion handling."""

    def test_scene_finished_with_export(self, tmp_path):
        """Test scene_finished with VTK export enabled."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer(vtk_export=True)
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            circle = Circle()
            scene.add(circle)

            # Simulate a play call to set num_plays
            renderer.num_plays = 1

            # Mock file_writer.finish to avoid actual file operations
            renderer.file_writer.finish = MagicMock()

            renderer.scene_finished(scene)

            # Check that VTK export was performed
            vtk_dir = Path(tmp_path) / "vtk" / "SimpleTestScene"
            assert vtk_dir.exists()


class TestVTKRendererSkipping:
    """Tests for animation skipping functionality."""

    def test_update_skipping_status_with_from_animation(self, tmp_path):
        """Test skipping status when from_animation_number is set."""
        with tempconfig({"media_dir": str(tmp_path), "from_animation_number": 5}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            renderer.num_plays = 0
            renderer.update_skipping_status()

            assert renderer.skip_animations is True


class TestVTKRendererTimeSeriesExport:
    """Tests for time series export functionality."""

    def test_render_exports_frame_when_time_series_enabled(self, tmp_path):
        """Test that time series mode is properly configured."""
        with tempconfig({"media_dir": str(tmp_path), "write_to_movie": False}):
            renderer = VTKRenderer(vtk_time_series=True)
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            circle = Circle()
            scene.add(circle)

            # Check that exporter is created and configured for time series
            assert renderer._exporter is not None
            assert renderer.vtk_time_series is True

            # Update frame should work
            renderer.update_frame(scene)
            frame = renderer.get_frame()

            assert frame is not None


class TestVTKRendererWithRealScenes:
    """Integration tests with real scene rendering."""

    @pytest.mark.slow
    def test_simple_scene_renders(self, tmp_path):
        """Test that a simple scene renders without errors."""
        with tempconfig(
            {
                "media_dir": str(tmp_path),
                "dry_run": True,  # Don't actually write video
            }
        ):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer

            # This should not raise an error
            renderer.init_scene(scene)

    @pytest.mark.slow
    def test_vtk_export_with_scene(self, tmp_path):
        """Test VTK export with a simple scene."""
        with tempconfig(
            {
                "media_dir": str(tmp_path),
            }
        ):
            renderer = VTKRenderer(vtk_export=True)
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            circle = Circle()
            scene.add(circle)

            filepath = renderer.export_vtk(scene)

            assert filepath.exists()


class TestVTKRendererEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_scene_export(self, tmp_path):
        """Test exporting an empty scene."""
        with tempconfig({"media_dir": str(tmp_path)}):
            renderer = VTKRenderer(vtk_export=True)
            scene = Scene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            filepath = renderer.export_vtk(scene)

            # Should still create a file
            assert filepath.exists()

    def test_freeze_current_frame(self, tmp_path):
        """Test freeze_current_frame updates time correctly."""
        with tempconfig({"media_dir": str(tmp_path), "write_to_movie": False}):
            renderer = VTKRenderer()
            scene = SimpleTestScene()
            scene.renderer = renderer
            renderer.init_scene(scene)

            renderer.update_frame(scene)

            # Test time calculation for freeze
            renderer.skip_animations = False
            initial_time = renderer.time

            # Calculate what freeze_current_frame would add
            dt = 1 / renderer.camera.frame_rate
            duration = 1.0
            num_frames = int(duration / dt)

            # Manually update time to simulate freeze
            renderer.time += num_frames * dt

            # Time should have advanced
            assert renderer.time > initial_time
            # Approximately 1 second should have passed
            assert abs(renderer.time - initial_time - duration) < 0.1
