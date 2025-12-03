"""VTK-based renderer for Manim.

This renderer uses VTK for:
- Offscreen rendering to produce video frames
- Exporting scene geometry to VTK file formats
- Scientific visualization with high-quality shaded surfaces

Usage::

    from manimvtk import config
    config.renderer = "vtk"

    # Or via CLI:
    manim -pqh MyScene --renderer vtk
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from .. import config, logger
from ..camera.camera import Camera
from ..mobject.mobject import Mobject, _AnimationBuilder
from ..scene.scene_file_writer import SceneFileWriter
from ..utils.exceptions import EndSceneEarlyException
from ..utils.iterables import list_update
from .vtk_exporter import VTKExporter
from .vtk_mobject_adapter import mobject_to_vtk_polydata

if TYPE_CHECKING:
    from manimvtk.animation.animation import Animation
    from manimvtk.scene.scene import Scene
    from manimvtk.typing import PixelArray

__all__ = ["VTKRenderer"]


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


class VTKRenderer:
    """A renderer using VTK for scientific visualization and export.

    This renderer provides:
    - Offscreen rendering via VTK render window
    - Export to VTK file formats (.vtp, .vtm, .pvd)
    - Time series animation export for ParaView/PyVista
    - High-quality shaded surface rendering

    Attributes
    ----------
    num_plays : int
        Number of play() functions in the scene.
    time : float
        Time elapsed since initialization of scene.
    vtk_export : bool
        Whether to export VTK files.
    vtk_time_series : bool
        Whether to export time series VTK files.
    """

    def __init__(
        self,
        file_writer_class: type[SceneFileWriter] = SceneFileWriter,
        camera_class: type[Camera] | None = None,
        skip_animations: bool = False,
        vtk_export: bool = False,
        vtk_time_series: bool = False,
        **kwargs: Any,
    ) -> None:
        self._file_writer_class = file_writer_class
        camera_cls = camera_class if camera_class is not None else Camera
        self.camera = camera_cls()

        self._original_skipping_status = skip_animations
        self.skip_animations = skip_animations
        self.animations_hashes: list[str | None] = []
        self.num_plays = 0
        self.time = 0.0
        self.static_image: PixelArray | None = None

        # VTK-specific settings
        self.vtk_export = vtk_export or config.get("vtk_export", False)
        self.vtk_time_series = vtk_time_series or config.get("vtk_time_series", False)

        # VTK objects (initialized lazily)
        self._vtk = None
        self._render_window = None
        self._renderer = None
        self._vtk_camera = None
        self._exporter: VTKExporter | None = None

        # Flag to track if VTK rendering is available (may not be in headless environments)
        self._vtk_rendering_available = False

        # Actor cache to avoid recreating actors every frame
        self._actor_cache: dict[int, Any] = {}

    @property
    def vtk(self):
        """Lazy load VTK module."""
        if self._vtk is None:
            self._vtk = _get_vtk()
        return self._vtk

    def _check_vtk_rendering_available(self) -> bool:
        """Check if VTK offscreen rendering is available.

        VTK requires either a display (X11), EGL, or OSMesa for offscreen rendering.
        This method checks the environment to determine if rendering is possible.

        Returns
        -------
        bool
            True if VTK offscreen rendering should be available.
        """
        import os
        import platform
        import ctypes

        # Check for display (works on all Unix-like systems)
        display = os.environ.get("DISPLAY", "")
        if display:
            return True

        system = platform.system()

        # Platform-specific library checks
        if system == "Darwin":  # macOS
            # On macOS, we can typically render without a display via OpenGL
            # Check for OpenGL framework
            try:
                ctypes.CDLL("/System/Library/Frameworks/OpenGL.framework/OpenGL")
                return True
            except OSError:
                pass
        elif system == "Windows":
            # On Windows, check for OpenGL32.dll
            try:
                ctypes.CDLL("opengl32.dll")
                return True
            except OSError:
                pass
        else:  # Linux and other Unix-like systems
            # Check for EGL (modern offscreen rendering)
            for egl_lib in ["libEGL.so.1", "libEGL.so"]:
                try:
                    ctypes.CDLL(egl_lib)
                    return True
                except OSError:
                    pass

            # Check for OSMesa (software rendering)
            for osmesa_lib in ["libOSMesa.so", "libOSMesa.so.8"]:
                try:
                    ctypes.CDLL(osmesa_lib)
                    return True
                except OSError:
                    pass

        return False

    def _init_vtk_rendering(self) -> None:
        """Initialize VTK rendering components.

        In headless environments (e.g., Google Colab without GPU), VTK rendering
        may fail. This method attempts to initialize VTK rendering and falls back
        to using the Cairo camera for video frames if VTK rendering is unavailable.
        VTK file export will still work regardless.
        """
        # Check if VTK rendering is possible before attempting initialization
        if not self._check_vtk_rendering_available():
            logger.warning(
                "VTK offscreen rendering not available (no display, EGL, or OSMesa). "
                "Video will use Cairo renderer. VTK export will still work."
            )
            self._vtk_rendering_available = False
            return

        vtk = self.vtk

        try:
            # Create render window
            self._render_window = vtk.vtkRenderWindow()
            self._render_window.SetOffScreenRendering(True)
            self._render_window.SetSize(config["pixel_width"], config["pixel_height"])

            # Create renderer
            self._renderer = vtk.vtkRenderer()

            # Set background color
            bg_color = config["background_color"]
            rgb = bg_color.to_rgb() if hasattr(bg_color, "to_rgb") else [0.0, 0.0, 0.0]
            self._renderer.SetBackground(*rgb)

            self._render_window.AddRenderer(self._renderer)

            # Create camera
            self._vtk_camera = vtk.vtkCamera()
            self._vtk_camera.SetPosition(0, 0, 10)
            self._vtk_camera.SetFocalPoint(0, 0, 0)
            self._vtk_camera.SetViewUp(0, 1, 0)

            # Set camera to match Manim's coordinate system
            frame_height = config["frame_height"]
            self._vtk_camera.ParallelProjectionOn()
            self._vtk_camera.SetParallelScale(frame_height / 2)

            self._renderer.SetActiveCamera(self._vtk_camera)

            # Test if VTK rendering actually works by doing a test render
            self._render_window.Render()
            self._vtk_rendering_available = True
            logger.debug("VTK offscreen rendering initialized successfully")
        except Exception as e:
            logger.warning(
                f"VTK offscreen rendering not available ({e}). "
                "Video will use Cairo renderer. VTK export will still work."
            )
            self._vtk_rendering_available = False
            self._render_window = None
            self._renderer = None
            self._vtk_camera = None

    def init_scene(self, scene: Scene) -> None:
        """Initialize the renderer for a scene.

        Parameters
        ----------
        scene : Scene
            The scene to render.
        """
        self.file_writer: Any = self._file_writer_class(
            self,
            scene.__class__.__name__,
        )
        self.scene = scene

        # Initialize VTK rendering
        self._init_vtk_rendering()

        # Initialize exporter if needed
        if self.vtk_export or self.vtk_time_series:
            vtk_dir = Path(config.get_dir("media_dir")) / "vtk" / scene.__class__.__name__
            self._exporter = VTKExporter(vtk_dir, scene.__class__.__name__)
            logger.info(f"VTK export enabled. Output directory: {vtk_dir}")

    def play(
        self,
        scene: Scene,
        *args: Animation | Mobject | _AnimationBuilder,
        **kwargs: Any,
    ) -> None:
        """Play animations in the scene.

        Parameters
        ----------
        scene : Scene
            The scene containing the animations.
        *args : Animation | Mobject | _AnimationBuilder
            Animations to play.
        **kwargs : Any
            Additional keyword arguments.
        """
        # Reset skip_animations to the original state
        self.skip_animations = self._original_skipping_status
        self.update_skipping_status()

        scene.compile_animation_data(*args, **kwargs)

        if self.skip_animations:
            logger.debug(f"Skipping animation {self.num_plays}")
            hash_current_animation = None
            self.time += scene.duration
        else:
            logger.info(f"VTK Renderer: Animation {self.num_plays}")
            hash_current_animation = f"vtk_{self.num_plays:05}"

        self.file_writer.add_partial_movie_file(hash_current_animation)
        self.animations_hashes.append(hash_current_animation)

        self.file_writer.begin_animation(not self.skip_animations)
        scene.begin_animations()

        # Save static image for static mobjects
        self.save_static_frame_data(scene, scene.static_mobjects)

        if scene.is_current_animation_frozen_frame():
            self.update_frame(scene, mobjects=scene.moving_mobjects)
            self.freeze_current_frame(scene.duration)
        else:
            scene.play_internal()

        self.file_writer.end_animation(not self.skip_animations)
        self.num_plays += 1

    def render(
        self,
        scene: Scene,
        time: float,
        moving_mobjects: Iterable[Mobject] | None = None,
    ) -> None:
        """Render a frame of the scene.

        Parameters
        ----------
        scene : Scene
            The scene to render.
        time : float
            Current time in the animation.
        moving_mobjects : Iterable[Mobject], optional
            List of moving mobjects.
        """
        self.update_frame(scene, moving_mobjects)
        frame = self.get_frame()
        self.add_frame(frame)

        # Export frame if time series is enabled
        if self.vtk_time_series and self._exporter is not None:
            all_mobjects = list(scene.mobjects) + list(scene.foreground_mobjects)
            self._exporter.export_frame(all_mobjects, self.time)

    def update_frame(
        self,
        scene: Scene,
        mobjects: Iterable[Mobject] | None = None,
        include_submobjects: bool = True,
        ignore_skipping: bool = True,
        **kwargs: Any,
    ) -> None:
        """Update the VTK frame.

        Parameters
        ----------
        scene : Scene
            The scene to render.
        mobjects : Iterable[Mobject], optional
            Mobjects to render. If None, uses all scene mobjects.
        include_submobjects : bool
            Whether to include submobjects.
        ignore_skipping : bool
            Whether to ignore skipping status.
        **kwargs : Any
            Additional keyword arguments.
        """
        if self.skip_animations and not ignore_skipping:
            return

        if not mobjects:
            mobjects = list_update(scene.mobjects, scene.foreground_mobjects)

        if self.static_image is not None:
            self.camera.set_frame_to_background(self.static_image)
        else:
            self.camera.reset()

        # Update VTK scene
        self._update_vtk_scene(mobjects)

        # Also update Cairo camera for compatibility
        kwargs["include_submobjects"] = include_submobjects
        self.camera.capture_mobjects(mobjects, **kwargs)

    def _update_vtk_scene(self, mobjects: Iterable[Mobject]) -> None:
        """Update VTK actors for the given mobjects.

        Parameters
        ----------
        mobjects : Iterable[Mobject]
            Mobjects to add/update in the VTK scene.
        """
        # Skip if VTK rendering isn't available
        if not self._vtk_rendering_available or self._renderer is None:
            return

        # Clear old actors
        self._renderer.RemoveAllViewProps()

        # Add actors for each mobject
        for mobj in mobjects:
            self._add_mobject_to_vtk(mobj)

    def _add_mobject_to_vtk(self, mobj: Mobject) -> None:
        """Add a mobject as a VTK actor.

        Parameters
        ----------
        mobj : Mobject
            The mobject to add.
        """
        # Skip if VTK rendering isn't available
        if not self._vtk_rendering_available or self._renderer is None:
            return

        vtk = self.vtk

        # Get or create polydata
        polydata = mobject_to_vtk_polydata(mobj)

        if polydata.GetNumberOfPoints() == 0:
            return

        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        # Create actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Set properties
        prop = actor.GetProperty()

        # Get color
        try:
            color = mobj.get_color()
            rgb = color.to_rgb() if hasattr(color, "to_rgb") else [1.0, 1.0, 1.0]
            prop.SetColor(*rgb)
        except Exception:
            prop.SetColor(1.0, 1.0, 1.0)

        # Get opacity
        try:
            opacity = mobj.get_fill_opacity() if hasattr(mobj, "get_fill_opacity") else 1.0
            prop.SetOpacity(opacity)
        except Exception:
            prop.SetOpacity(1.0)

        # Add to renderer
        self._renderer.AddActor(actor)

    def get_frame(self) -> PixelArray:
        """Get the current frame as a NumPy array.

        Returns
        -------
        PixelArray
            NumPy array of pixel values (height x width x 4) in RGBA format.
        """
        # Fall back to Cairo camera if VTK rendering isn't available
        if not self._vtk_rendering_available or self._render_window is None:
            return np.array(self.camera.pixel_array)

        vtk = self.vtk

        # Render
        self._render_window.Render()

        # Capture to numpy array with RGBA format for video encoding compatibility
        window_to_image = vtk.vtkWindowToImageFilter()
        window_to_image.SetInput(self._render_window)
        window_to_image.SetInputBufferTypeToRGBA()
        window_to_image.Update()

        # Convert to numpy
        vtk_image = window_to_image.GetOutput()
        width, height, _ = vtk_image.GetDimensions()

        vtk_array = vtk_image.GetPointData().GetScalars()
        num_components = vtk_array.GetNumberOfComponents()

        # Ensure we have 4 components (RGBA) for video encoding
        np_array = np.zeros((height, width, 4), dtype=np.uint8)

        for y in range(height):
            for x in range(width):
                idx = y * width + x
                for c in range(min(num_components, 4)):
                    np_array[height - 1 - y, x, c] = int(vtk_array.GetComponent(idx, c))

        # Set alpha to 255 if VTK only provided RGB (do this outside the loops for efficiency)
        if num_components < 4:
            np_array[:, :, 3] = 255

        # Also store in Cairo camera for compatibility
        if hasattr(self.camera, "pixel_array"):
            # Resize if needed
            if np_array.shape[:2] != self.camera.pixel_array.shape[:2]:
                pass  # Let camera handle its own array
            else:
                self.camera.pixel_array[:, :, :] = np_array

        return np_array

    def add_frame(self, frame: PixelArray, num_frames: int = 1) -> None:
        """Add a frame to the video file.

        Parameters
        ----------
        frame : PixelArray
            The frame to add.
        num_frames : int
            Number of times to add the frame.
        """
        dt = 1 / self.camera.frame_rate
        if self.skip_animations:
            return
        self.time += num_frames * dt
        self.file_writer.write_frame(frame, num_frames=num_frames)

    def freeze_current_frame(self, duration: float) -> None:
        """Add a static frame for a given duration.

        Parameters
        ----------
        duration : float
            Duration to freeze the frame.
        """
        dt = 1 / self.camera.frame_rate
        self.add_frame(
            self.get_frame(),
            num_frames=int(duration / dt),
        )

    def show_frame(self, scene: Scene) -> None:
        """Display the current frame.

        Parameters
        ----------
        scene : Scene
            The scene to display.
        """
        self.update_frame(scene, ignore_skipping=True)
        self.camera.get_image().show()

    def save_static_frame_data(
        self,
        scene: Scene,
        static_mobjects: Iterable[Mobject],
    ) -> PixelArray | None:
        """Save static frame data.

        Parameters
        ----------
        scene : Scene
            The scene.
        static_mobjects : Iterable[Mobject]
            Static mobjects.

        Returns
        -------
        PixelArray | None
            The static image or None.
        """
        self.static_image = None
        if not static_mobjects:
            return None
        self.update_frame(scene, mobjects=static_mobjects)
        self.static_image = self.get_frame()
        return self.static_image

    def update_skipping_status(self) -> None:
        """Check if animations should be skipped."""
        if self.file_writer.sections[-1].skip_animations:
            self.skip_animations = True
        if config["save_last_frame"]:
            self.skip_animations = True
        if (
            config.from_animation_number > 0
            and self.num_plays < config.from_animation_number
        ):
            self.skip_animations = True
        if (
            config.upto_animation_number >= 0
            and self.num_plays > config.upto_animation_number
        ):
            self.skip_animations = True
            raise EndSceneEarlyException()

    def scene_finished(self, scene: Scene) -> None:
        """Handle scene completion.

        Parameters
        ----------
        scene : Scene
            The completed scene.
        """
        # Ensure exporter is available when export is requested. In some edge cases
        # (for example, when initialization failed early), the exporter may not
        # have been created even though the export flags are set. Recreate it here
        # so we still persist geometry instead of silently leaving empty folders.
        if (self.vtk_export or self.vtk_time_series) and self._exporter is None:
            vtk_dir = Path(config.get_dir("media_dir")) / "vtk" / scene.__class__.__name__
            self._exporter = VTKExporter(vtk_dir, scene.__class__.__name__)
            logger.info(f"VTK export enabled (fallback). Output directory: {vtk_dir}")

        # Export final VTK if enabled
        if self.vtk_export and self._exporter is not None:
            all_mobjects = list(scene.mobjects) + list(scene.foreground_mobjects)
            filepath = self._exporter.export_scene_static(all_mobjects)
            logger.info(f"VTK static export: {filepath}")

        # Write PVD for time series
        if self.vtk_time_series and self._exporter is not None:
            pvd_path = self._exporter.write_pvd()
            logger.info(f"VTK time series export: {pvd_path}")

            # Also generate HTML viewer
            html_path = self._exporter.generate_html_viewer()
            logger.info(f"VTK HTML viewer: {html_path}")

        # Handle movie file
        if self.num_plays:
            self.file_writer.finish()
        elif config.write_to_movie:
            config.save_last_frame = True
            config.write_to_movie = False
        else:
            self.static_image = None
            self.update_frame(scene)

        if config["save_last_frame"]:
            self.static_image = None
            self.update_frame(scene)
            self.file_writer.save_image(self.camera.get_image())

    def export_vtk(self, scene: Scene, path: str | Path | None = None) -> Path:
        """Export the current scene to VTK format.

        Parameters
        ----------
        scene : Scene
            The scene to export.
        path : str | Path, optional
            Output path. If None, uses default location.

        Returns
        -------
        Path
            Path to the exported file.
        """
        if self._exporter is None:
            vtk_dir = Path(config.get_dir("media_dir")) / "vtk" / scene.__class__.__name__
            self._exporter = VTKExporter(vtk_dir, scene.__class__.__name__)

        all_mobjects = list(scene.mobjects) + list(scene.foreground_mobjects)
        return self._exporter.export_scene_static(all_mobjects, path)
