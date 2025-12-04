<p align="center">
    <a href="https://manimvtk.mathify.dev"><img src="https://raw.githubusercontent.com/mathifylabs/manimvtk/main/logo/cropped.png"></a>
    <br />
    <h1 align="center">ManimVTK</h1>
    <h3 align="center">Scientific Visualization meets Mathematical Animation</h3>
    <br />
    <p align="center">
    <a href="https://github.com/mathifylabs/manimVTK"><img src="https://img.shields.io/badge/fork-manimvtk-blue?style=flat&logo=github" alt="GitHub Fork"></a>
    <a href="http://choosealicense.com/licenses/mit/"><img src="https://img.shields.io/badge/license-MIT-red.svg?style=flat" alt="MIT License"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
    </p>
</p>
<hr />

**ManimVTK** is a fork of [Manim Community](https://www.manim.community/) that integrates VTK (Visualization Toolkit) for scientific visualization and export capabilities. It keeps Manim's elegant syntax and animation system while adding the ability to:

- **Export VTK assets** for visualization in ParaView, PyVista, and vtk.js
- **Render with VTK** for high-quality shaded surfaces
- **Create time series** animations for CFD and scientific data
- **Generate interactive 3D datasets** alongside traditional video output

## 🎯 What's New

Users can now render scenes with VTK and export scientific visualization data:

```bash
# Export both an MP4 video AND VTK scene files
manimvtk -pqh MyScene --renderer vtk --vtk-export

# Export time series for ParaView animation scrubbing
manimvtk MyScene --renderer vtk --vtk-time-series
```

## 🚀 Quick Start

### Installation

#### Prerequisites (Linux only)

ManimVTK depends on [ManimPango](https://github.com/ManimCommunity/ManimPango), which requires system dependencies on Linux since pre-built wheels are not available. Install them first:

**Debian/Ubuntu (including Google Colab):**

```bash
sudo apt install libpango1.0-dev pkg-config python3-dev
```

**Fedora:**

```bash
sudo dnf install pango-devel pkg-config python3-devel
```

**Arch Linux:**

```bash
sudo pacman -S pango pkgconf
```

#### Install ManimVTK

```bash
# Clone the repository
git clone https://github.com/mathifylabs/manimVTK.git
cd manimVTK

# Install with VTK support
pip install -e ".[vtk]"

# Or install with full scientific stack (includes PyVista)
pip install -e ".[scientific]"
```

Or install from PyPI:

```bash
pip install manimvtk[vtk]
```

### Basic Usage

```python
from manimvtk import *

class CFDVisualization(Scene):
    def construct(self):
        # Create a surface (e.g., representing pressure field)
        surface = Surface(
            lambda u, v: np.array([u, v, np.sin(u) * np.cos(v)]),
            u_range=[-2, 2],
            v_range=[-2, 2],
            resolution=(50, 50),
        )
        surface.set_color(BLUE)

        self.play(Create(surface))
        self.wait()
```

Render with VTK export:

```bash
manimvtk -pqh example.py CFDVisualization --renderer vtk --vtk-export
```

This produces:

- `media/videos/example/1080p60/CFDVisualization.mp4` - Standard video output
- `media/vtk/CFDVisualization/CFDVisualization_final.vtm` - VTK MultiBlock file

## 📦 VTK Export Options

### Static Export (`--vtk-export`)

Exports the final scene state to VTK format:

- Single mobject: `.vtp` (PolyData)
- Multiple mobjects: `.vtm` (MultiBlock)

### Time Series Export (`--vtk-time-series`)

Exports frame-by-frame VTK files with a `.pvd` collection file:

```
media/vtk/MyScene/
├── MyScene.pvd              # ParaView Data collection file
├── MyScene_00000.vtp        # Frame 0
├── MyScene_00001.vtp        # Frame 1
├── ...
└── MyScene_viewer.html      # Basic HTML viewer template
```

Load the `.pvd` file in ParaView to scrub through animations using its native time slider.

## 🔧 CLI Options

| Option              | Description                          |
| ------------------- | ------------------------------------ |
| `--renderer vtk`    | Use VTK renderer                     |
| `--vtk-export`      | Export final scene to VTK format     |
| `--vtk-time-series` | Export all frames as VTK time series |

## 💡 Use Cases

### CFD Visualization

```python
from manimvtk import *
from manimvtk.vtk import add_scalar_field, add_vector_field

class PressureField(Scene):
    def construct(self):
        # Create surface mesh
        surface = Surface(
            lambda u, v: np.array([u, v, 0]),
            u_range=[-2, 2],
            v_range=[-2, 2],
        )

        # Color by pressure (handled in VTK export)
        self.add(surface)
        self.wait()
```

### Interactive Web Viewing

The exported `.vtkjs` files can be embedded in web applications using vtk.js, perfect for:

- Educational platforms
- Research presentations
- Interactive documentation

## 🏗 Architecture

ManimVTK adds a new renderer layer:

```
┌─────────────────────────────────────────────────────────┐
│                    Manim Core                           │
│  (Scene, Mobject, VMobject, Animation, play, etc.)     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│               Renderer Abstraction                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │CairoRenderer│ │OpenGLRenderer│ │ VTKRenderer ✨  │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            VTK Export / Viewer Layer                    │
│  • vtk_exporter.py - File export (.vtp, .vtm, .pvd)   │
│  • vtk_mobject_adapter.py - Manim → VTK conversion    │
│  • HTML/vtk.js viewer template                         │
└─────────────────────────────────────────────────────────┘
```

## 📊 Supported Mobjects

| Mobject Type           | VTK Export | Notes                             |
| ---------------------- | ---------- | --------------------------------- |
| `VMobject` (2D shapes) | ✅         | Converted to PolyData with colors |
| `Surface`              | ✅         | Full mesh with UV coordinates     |
| `Sphere`, `Cube`, etc. | ✅         | 3D primitives                     |
| `ParametricSurface`    | ✅         | Parametric surfaces               |
| `VGroup`               | ✅         | Exported as MultiBlock            |

## 🔬 Scientific Features

### Scalar Fields

Attach scalar data (pressure, temperature) to VTK exports:

```python
from manimvtk.vtk import add_scalar_field

# After creating polydata
add_scalar_field(polydata, "pressure", pressure_values)
```

### Vector Fields

Attach velocity/force fields for glyphs and streamlines:

```python
from manimvtk.vtk import add_vector_field

# Attach velocity (U, V, W components)
add_vector_field(polydata, "velocity", velocity_vectors)
```

## 🧪 Testing

### Running the Test Suite

The project includes a comprehensive test suite for VTK functionality with 61 tests covering:

- **VTK Mobject Adapter**: Conversion of Manim mobjects to VTK PolyData
- **VTK Exporter**: File export (.vtp, .vtm, .pvd, .vtkjs)
- **VTK Renderer**: Renderer initialization and scene handling

To run the tests:

```bash
# Install dev dependencies
pip install -e ".[vtk]"
pip install pytest pytest-cov pytest-xdist

# Run VTK tests (headless environments require xvfb)
xvfb-run -a pytest tests/test_vtk/ -v

# Run with display available
pytest tests/test_vtk/ -v
```

### VTK Example Scenes

Try the example scenes in `example_scenes/vtk_examples.py` to verify VTK functionality:

```bash
# Basic 2D example with VTK export
manimvtk -pql example_scenes/vtk_examples.py Circle2DExample --vtk-export

# 3D surface example
manimvtk -pql example_scenes/vtk_examples.py ParametricSurfaceExample --vtk-export

# Time series export for ParaView
manimvtk -pql example_scenes/vtk_examples.py AnimatedCircle --vtk-time-series

# List all available example scenes
python -c "from example_scenes.vtk_examples import EXAMPLE_SCENES; print([s.__name__ for s in EXAMPLE_SCENES])"
```

Available example categories:

- **Basic 2D**: Circle2DExample, Square2DExample, MultipleShapes2D, PolygonExample
- **Basic 3D**: Sphere3DExample, Cube3DExample, ParametricSurfaceExample, TorusSurface
- **Animated**: AnimatedCircle, SquareToCircleVTK, Rotating3DObject, GrowingSurface
- **Scientific**: WaveSurface, PressureFieldVisualization, VelocityFieldArrows
- **Edge Cases**: EmptyScene, ManyShapes, TinyMobject, LargeMobject

## 🤝 Contributing

Contributions are welcome! This fork is particularly interested in:

- Additional mobject → VTK conversions
- vtk.js web viewer improvements
- CFD-specific visualization features
- Performance optimizations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

The software is double-licensed under the MIT license:

- Copyright by 3blue1brown LLC (see LICENSE)
- Copyright by Manim Community Developers (see LICENSE.community)
- Copyright by Mathify Labs for VTK extensions

## 🙏 Acknowledgments

- [Manim Community](https://www.manim.community/) - The original animation engine
- [3Blue1Brown](https://www.3blue1brown.com/) - Creator of the original Manim
- [VTK](https://vtk.org/) - The Visualization Toolkit
- [ParaView](https://www.paraview.org/) - Scientific visualization application

---

<p align="center">
<i>Describe your simulation → get both a video and an interactive 3D dataset.</i>
</p>
