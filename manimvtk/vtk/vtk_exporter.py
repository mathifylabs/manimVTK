"""VTK Exporter - Export Manim scenes to VTK file formats.

This module provides functionality to export Manim scenes and mobjects
to various VTK file formats including:
- .vtp (VTK PolyData)
- .vtm (VTK MultiBlock)
- .pvd (ParaView Data - time series)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .vtk_mobject_adapter import mobject_to_vtk_polydata

if TYPE_CHECKING:
    from manimvtk.mobject.mobject import Mobject

__all__ = ["VTKExporter"]


def _get_vtk():
    """Lazy import of VTK to avoid import errors when VTK is not installed."""
    try:
        import vtk

        return vtk
    except ImportError as e:
        raise ImportError(
            "VTK is required for VTK export. Install it with: pip install vtk"
        ) from e


class VTKExporter:
    """Export Manim scenes and mobjects to VTK file formats.

    This exporter supports:
    - Static export: Single .vtp file with all mobjects
    - Time series export: .pvd file with frame-by-frame .vtp files

    Parameters
    ----------
    output_dir : str | Path
        Directory where VTK files will be saved.
    scene_name : str
        Name of the scene (used for file naming).
    """

    def __init__(self, output_dir: str | Path, scene_name: str = "scene") -> None:
        self.output_dir = Path(output_dir)
        self.scene_name = scene_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # For time series export
        self.frame_count = 0
        self.frame_files: list[tuple[float, str]] = []

    def export_mobject(self, mobj: Mobject, filename: str | None = None) -> Path:
        """Export a single mobject to a .vtp file.

        Parameters
        ----------
        mobj : Mobject
            The mobject to export.
        filename : str, optional
            Output filename. If None, uses the mobject class name.

        Returns
        -------
        Path
            Path to the exported file.
        """
        vtk = _get_vtk()

        if filename is None:
            filename = f"{mobj.__class__.__name__}.vtp"

        if not filename.endswith(".vtp"):
            filename = f"{filename}.vtp"

        filepath = self.output_dir / filename

        polydata = mobject_to_vtk_polydata(mobj)

        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetFileName(str(filepath))
        writer.SetInputData(polydata)
        writer.Write()

        return filepath

    def export_scene_static(
        self, mobjects: list[Mobject], filename: str | None = None
    ) -> Path:
        """Export all mobjects in a scene to a single .vtp or .vtm file.

        Parameters
        ----------
        mobjects : list[Mobject]
            List of mobjects to export.
        filename : str, optional
            Output filename. If None, uses scene_name.

        Returns
        -------
        Path
            Path to the exported file.
        """
        vtk = _get_vtk()

        if filename is None:
            filename = f"{self.scene_name}_final.vtm"

        if len(mobjects) == 0:
            # Empty scene
            filepath = self.output_dir / filename.replace(".vtm", ".vtp")
            polydata = vtk.vtkPolyData()
            writer = vtk.vtkXMLPolyDataWriter()
            writer.SetFileName(str(filepath))
            writer.SetInputData(polydata)
            writer.Write()
            return filepath

        if len(mobjects) == 1:
            # Single mobject - use .vtp
            return self.export_mobject(mobjects[0], filename.replace(".vtm", ".vtp"))

        # Multiple mobjects - use MultiBlock
        multiblock = vtk.vtkMultiBlockDataSet()
        multiblock.SetNumberOfBlocks(len(mobjects))

        for i, mobj in enumerate(mobjects):
            polydata = mobject_to_vtk_polydata(mobj)
            multiblock.SetBlock(i, polydata)
            multiblock.GetMetaData(i).Set(
                vtk.vtkCompositeDataSet.NAME(), mobj.__class__.__name__
            )

        if not filename.endswith(".vtm"):
            filename = f"{filename}.vtm"

        filepath = self.output_dir / filename

        writer = vtk.vtkXMLMultiBlockDataWriter()
        writer.SetFileName(str(filepath))
        writer.SetInputData(multiblock)
        writer.Write()

        return filepath

    def export_frame(
        self, mobjects: list[Mobject], time: float, frame_number: int | None = None
    ) -> Path:
        """Export a single frame of an animation to a .vtp file.

        Parameters
        ----------
        mobjects : list[Mobject]
            List of mobjects to export.
        time : float
            Time stamp for this frame.
        frame_number : int, optional
            Frame number. If None, uses internal counter.

        Returns
        -------
        Path
            Path to the exported file.
        """
        vtk = _get_vtk()

        if frame_number is None:
            frame_number = self.frame_count
            self.frame_count += 1

        filename = f"{self.scene_name}_{frame_number:05d}.vtp"
        filepath = self.output_dir / filename

        # Combine all mobjects into a single PolyData with append filter
        append_filter = vtk.vtkAppendPolyData()

        for mobj in mobjects:
            polydata = mobject_to_vtk_polydata(mobj)
            if polydata.GetNumberOfPoints() > 0:
                append_filter.AddInputData(polydata)

        if append_filter.GetNumberOfInputConnections(0) > 0:
            append_filter.Update()
            combined = append_filter.GetOutput()
        else:
            combined = vtk.vtkPolyData()

        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetFileName(str(filepath))
        writer.SetInputData(combined)
        writer.Write()

        # Record for PVD generation
        self.frame_files.append((time, filename))

        return filepath

    def write_pvd(self, filename: str | None = None) -> Path:
        """Write a ParaView Data (.pvd) file for time series animation.

        The .pvd file references all frame .vtp files with their timestamps,
        allowing ParaView to scrub through the animation.

        Parameters
        ----------
        filename : str, optional
            Output filename. If None, uses scene_name.

        Returns
        -------
        Path
            Path to the exported .pvd file.
        """
        if filename is None:
            filename = f"{self.scene_name}.pvd"

        if not filename.endswith(".pvd"):
            filename = f"{filename}.pvd"

        filepath = self.output_dir / filename

        # Build PVD XML content
        lines = [
            '<?xml version="1.0"?>',
            '<VTKFile type="Collection" version="0.1">',
            "  <Collection>",
        ]

        for time, frame_file in self.frame_files:
            lines.append(f'    <DataSet timestep="{time:.6f}" file="{frame_file}"/>')

        lines.extend(
            [
                "  </Collection>",
                "</VTKFile>",
            ]
        )

        with open(filepath, "w") as f:
            f.write("\n".join(lines))

        return filepath

    def reset_time_series(self) -> None:
        """Reset the time series export state."""
        self.frame_count = 0
        self.frame_files = []

    def export_to_vtkjs(self, mobjects: list[Mobject], filename: str | None = None) -> Path:
        """Export scene to vtk.js format for web visualization.

        This creates a JSON-based format that can be loaded by vtk.js viewers.

        Parameters
        ----------
        mobjects : list[Mobject]
            List of mobjects to export.
        filename : str, optional
            Output filename. If None, uses scene_name.

        Returns
        -------
        Path
            Path to the exported .vtkjs file.

        Note
        ----
        This feature requires additional setup for full web compatibility.
        Consider using PyVista's export_vtkjs() for production use.
        """
        # Ensure VTK is available (for dependency checking)
        _get_vtk()

        if filename is None:
            filename = f"{self.scene_name}.vtkjs"

        if not filename.endswith(".vtkjs"):
            filename = f"{filename}.vtkjs"

        filepath = self.output_dir / filename

        # For now, export as JSON-friendly format
        # Full vtk.js export would require additional tooling
        import json

        scene_data = {
            "type": "vtkjs_scene",
            "version": "1.0",
            "scene_name": self.scene_name,
            "objects": [],
        }

        for mobj in mobjects:
            polydata = mobject_to_vtk_polydata(mobj)
            obj_data = {
                "name": mobj.__class__.__name__,
                "num_points": polydata.GetNumberOfPoints(),
                "num_cells": polydata.GetNumberOfCells(),
            }

            # Extract points
            points = []
            for i in range(polydata.GetNumberOfPoints()):
                p = polydata.GetPoint(i)
                points.extend([p[0], p[1], p[2]])
            obj_data["points"] = points

            scene_data["objects"].append(obj_data)

        with open(filepath, "w") as f:
            json.dump(scene_data, f)

        return filepath

    def generate_html_viewer(self, vtkjs_path: Path | None = None) -> Path:
        """Generate an HTML file with an embedded vtk.js viewer.

        Parameters
        ----------
        vtkjs_path : Path, optional
            Path to the .vtkjs file. If None, generates a basic template.

        Returns
        -------
        Path
            Path to the generated HTML file.
        """
        html_path = self.output_dir / f"{self.scene_name}_viewer.html"

        data_file = vtkjs_path.name if vtkjs_path else f"{self.scene_name}.vtkjs"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Manim-VTK Viewer: {self.scene_name}</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        #renderWindow {{
            width: 100%;
            height: 100%;
        }}
        .info {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial, sans-serif;
        }}
    </style>
</head>
<body>
    <div class="info">
        <h3>Manim-VTK Scene: {self.scene_name}</h3>
        <p>Use mouse to rotate, scroll to zoom</p>
        <p>Data file: {data_file}</p>
    </div>
    <div id="renderWindow"></div>

    <script type="text/javascript">
        // vtk.js viewer code would go here
        // For full implementation, include vtk.js library and loader code
        console.log("Manim-VTK Viewer");
        console.log("Load data from: {data_file}");

        // Placeholder message
        document.getElementById('renderWindow').innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100%; flex-direction: column;">
                <h2>Manim-VTK Scene: {self.scene_name}</h2>
                <p>To view this scene interactively:</p>
                <ol>
                    <li>Open the .vtp files in ParaView</li>
                    <li>Or use PyVista in Python</li>
                    <li>Or integrate vtk.js for web viewing</li>
                </ol>
                <p>Data files are in the same directory as this HTML file.</p>
            </div>
        `;
    </script>
</body>
</html>
"""

        with open(html_path, "w") as f:
            f.write(html_content)

        return html_path
