"""Tests for VTK Exporter - exporting Manim scenes to VTK file formats."""

from __future__ import annotations

from manimvtk import Circle, Dot, Square
from manimvtk.vtk import VTKExporter


class TestVTKExporterInitialization:
    """Tests for VTKExporter initialization."""

    def test_exporter_creates_output_directory(self, tmp_path):
        """Test that the exporter creates the output directory."""
        output_dir = tmp_path / "vtk_output"
        exporter = VTKExporter(output_dir, "TestScene")

        assert output_dir.exists()
        assert exporter.output_dir == output_dir
        assert exporter.scene_name == "TestScene"

    def test_exporter_initial_state(self, tmp_path):
        """Test the initial state of the exporter."""
        exporter = VTKExporter(tmp_path, "TestScene")

        assert exporter.frame_count == 0
        assert exporter.frame_files == []


class TestExportMobject:
    """Tests for exporting individual mobjects."""

    def test_export_circle(self, tmp_path):
        """Test exporting a Circle mobject."""
        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle(radius=1.0)

        filepath = exporter.export_mobject(circle)

        assert filepath.exists()
        assert filepath.suffix == ".vtp"
        assert "Circle" in filepath.name

    def test_export_square(self, tmp_path):
        """Test exporting a Square mobject."""
        exporter = VTKExporter(tmp_path, "TestScene")
        square = Square(side_length=2.0)

        filepath = exporter.export_mobject(square)

        assert filepath.exists()
        assert filepath.suffix == ".vtp"

    def test_export_with_custom_filename(self, tmp_path):
        """Test exporting with a custom filename."""
        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()

        filepath = exporter.export_mobject(circle, filename="my_circle.vtp")

        assert filepath.exists()
        assert filepath.name == "my_circle.vtp"

    def test_export_without_extension(self, tmp_path):
        """Test that .vtp extension is added if missing."""
        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()

        filepath = exporter.export_mobject(circle, filename="my_circle")

        assert filepath.suffix == ".vtp"


class TestExportSceneStatic:
    """Tests for static scene export."""

    def test_export_empty_scene(self, tmp_path):
        """Test exporting an empty scene."""
        exporter = VTKExporter(tmp_path, "EmptyScene")

        filepath = exporter.export_scene_static([])

        assert filepath.exists()
        # Empty scene should create a vtp file
        assert filepath.suffix == ".vtp"

    def test_export_single_mobject_scene(self, tmp_path):
        """Test exporting a scene with a single mobject."""
        exporter = VTKExporter(tmp_path, "SingleScene")
        circle = Circle()

        filepath = exporter.export_scene_static([circle])

        assert filepath.exists()
        # Single mobject uses .vtp
        assert filepath.suffix == ".vtp"

    def test_export_multiple_mobjects_scene(self, tmp_path):
        """Test exporting a scene with multiple mobjects."""
        exporter = VTKExporter(tmp_path, "MultiScene")
        circle = Circle()
        square = Square()
        dot = Dot()

        filepath = exporter.export_scene_static([circle, square, dot])

        assert filepath.exists()
        # Multiple mobjects use .vtm (MultiBlock)
        assert filepath.suffix == ".vtm"

    def test_export_with_custom_filename(self, tmp_path):
        """Test exporting scene with custom filename."""
        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()

        filepath = exporter.export_scene_static([circle], filename="custom.vtm")

        assert filepath.exists()


class TestExportTimeSeries:
    """Tests for time series frame export."""

    def test_export_single_frame(self, tmp_path):
        """Test exporting a single frame."""
        exporter = VTKExporter(tmp_path, "TimeSeriesScene")
        circle = Circle()

        filepath = exporter.export_frame([circle], time=0.0)

        assert filepath.exists()
        assert filepath.suffix == ".vtp"
        assert "00000" in filepath.name
        assert exporter.frame_count == 1
        assert len(exporter.frame_files) == 1

    def test_export_multiple_frames(self, tmp_path):
        """Test exporting multiple frames."""
        exporter = VTKExporter(tmp_path, "TimeSeriesScene")
        circle = Circle()

        for i in range(5):
            exporter.export_frame([circle], time=i * 0.1)

        assert exporter.frame_count == 5
        assert len(exporter.frame_files) == 5

        # Check all frame files exist
        for _time, filename in exporter.frame_files:
            filepath = tmp_path / filename
            assert filepath.exists()

    def test_export_frame_with_explicit_number(self, tmp_path):
        """Test exporting a frame with explicit frame number."""
        exporter = VTKExporter(tmp_path, "TimeSeriesScene")
        circle = Circle()

        filepath = exporter.export_frame([circle], time=0.5, frame_number=42)

        assert filepath.exists()
        assert "00042" in filepath.name


class TestWritePVD:
    """Tests for PVD (ParaView Data) file generation."""

    def test_write_pvd_empty(self, tmp_path):
        """Test writing an empty PVD file."""
        exporter = VTKExporter(tmp_path, "TestScene")

        pvd_path = exporter.write_pvd()

        assert pvd_path.exists()
        assert pvd_path.suffix == ".pvd"

        content = pvd_path.read_text()
        assert 'type="Collection"' in content

    def test_write_pvd_with_frames(self, tmp_path):
        """Test writing PVD with frame references."""
        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()

        for i in range(3):
            exporter.export_frame([circle], time=i * 0.1)

        pvd_path = exporter.write_pvd()

        assert pvd_path.exists()
        content = pvd_path.read_text()

        # Check that all frame files are referenced
        assert "DataSet timestep" in content
        assert "00000.vtp" in content
        assert "00001.vtp" in content
        assert "00002.vtp" in content

    def test_write_pvd_with_custom_filename(self, tmp_path):
        """Test writing PVD with custom filename."""
        exporter = VTKExporter(tmp_path, "TestScene")

        pvd_path = exporter.write_pvd(filename="custom.pvd")

        assert pvd_path.name == "custom.pvd"

    def test_write_pvd_adds_extension(self, tmp_path):
        """Test that .pvd extension is added if missing."""
        exporter = VTKExporter(tmp_path, "TestScene")

        pvd_path = exporter.write_pvd(filename="custom")

        assert pvd_path.suffix == ".pvd"


class TestResetTimeSeries:
    """Tests for resetting time series state."""

    def test_reset_clears_frame_count(self, tmp_path):
        """Test that reset clears frame count."""
        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()

        for i in range(5):
            exporter.export_frame([circle], time=i * 0.1)

        exporter.reset_time_series()

        assert exporter.frame_count == 0
        assert exporter.frame_files == []


class TestExportToVTKJS:
    """Tests for vtk.js format export."""

    def test_export_vtkjs_empty(self, tmp_path):
        """Test exporting empty scene to vtkjs."""
        exporter = VTKExporter(tmp_path, "TestScene")

        filepath = exporter.export_to_vtkjs([])

        assert filepath.exists()
        assert filepath.suffix == ".vtkjs"

    def test_export_vtkjs_with_mobjects(self, tmp_path):
        """Test exporting mobjects to vtkjs."""
        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()

        filepath = exporter.export_to_vtkjs([circle])

        assert filepath.exists()

        # Check JSON content
        import json

        content = json.loads(filepath.read_text())
        assert content["type"] == "vtkjs_scene"
        assert "objects" in content


class TestGenerateHTMLViewer:
    """Tests for HTML viewer generation."""

    def test_generate_html_viewer(self, tmp_path):
        """Test generating HTML viewer file."""
        exporter = VTKExporter(tmp_path, "TestScene")

        html_path = exporter.generate_html_viewer()

        assert html_path.exists()
        assert html_path.suffix == ".html"

        content = html_path.read_text()
        assert "TestScene" in content
        assert "<!DOCTYPE html>" in content

    def test_html_viewer_with_vtkjs_path(self, tmp_path):
        """Test generating HTML viewer with vtkjs path."""
        exporter = VTKExporter(tmp_path, "TestScene")
        vtkjs_path = tmp_path / "data.vtkjs"
        vtkjs_path.touch()

        html_path = exporter.generate_html_viewer(vtkjs_path=vtkjs_path)

        assert html_path.exists()
        content = html_path.read_text()
        assert "data.vtkjs" in content


class TestVTKFileContent:
    """Tests that verify the content of exported VTK files."""

    def test_exported_file_is_valid_xml(self, tmp_path):
        """Test that exported .vtp file is valid XML."""
        import xml.etree.ElementTree as ET

        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()

        filepath = exporter.export_mobject(circle)

        # Should be parseable XML
        tree = ET.parse(filepath)
        root = tree.getroot()
        assert root.tag == "VTKFile"

    def test_multiblock_file_is_valid_xml(self, tmp_path):
        """Test that exported .vtm file is valid XML."""
        import xml.etree.ElementTree as ET

        exporter = VTKExporter(tmp_path, "TestScene")
        circle = Circle()
        square = Square()

        filepath = exporter.export_scene_static([circle, square])

        # Should be parseable XML
        tree = ET.parse(filepath)
        root = tree.getroot()
        assert root.tag == "VTKFile"
