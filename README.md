<p align="center">
    <a href="https://www.manim.community/"><img src="https://raw.githubusercontent.com/ManimCommunity/manim/main/logo/cropped.png"></a>
    <br />
    <h1 align="center">Manim-VTK</h1>
    <h3 align="center">Scientific Visualization meets Mathematical Animation</h3>
    <br />
    <p align="center">
    <a href="https://github.com/mathifylabs/manimVTK"><img src="https://img.shields.io/badge/fork-manim--vtk-blue?style=flat&logo=github" alt="GitHub Fork"></a>
    <a href="http://choosealicense.com/licenses/mit/"><img src="https://img.shields.io/badge/license-MIT-red.svg?style=flat" alt="MIT License"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
    </p>
</p>
<hr />

**Manim-VTK** is a fork of [Manim Community](https://www.manim.community/) that integrates VTK (Visualization Toolkit) for scientific visualization and export capabilities. It keeps Manim's elegant syntax and animation system while adding the ability to:

- **Export VTK assets** for visualization in ParaView, PyVista, and vtk.js
- **Render with VTK** for high-quality shaded surfaces
- **Create time series** animations for CFD and scientific data
- **Generate interactive 3D datasets** alongside traditional video output

## 🎯 What's New

Users can now render scenes with VTK and export scientific visualization data:

```bash
# Export both an MP4 video AND VTK scene files
manim -pqh MyScene --renderer vtk --vtk-export

# Export time series for ParaView animation scrubbing
manim MyScene --renderer vtk --vtk-time-series
```

## 🚀 Quick Start

### Installation

#### Prerequisites (Linux only)

Manim depends on [ManimPango](https://github.com/ManimCommunity/ManimPango), which requires system dependencies on Linux since pre-built wheels are not available. Install them first:

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

#### Install Manim-VTK

```bash
# Clone the repository
git clone https://github.com/mathifylabs/manimVTK.git
cd manimVTK

# Install with VTK support
pip install -e ".[vtk]"

# Or install with full scientific stack (includes PyVista)
pip install -e ".[scientific]"
```

### Basic Usage

```python
from manim import *

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
manim -pqh example.py CFDVisualization --renderer vtk --vtk-export
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

| Option | Description |
|--------|-------------|
| `--renderer vtk` | Use VTK renderer |
| `--vtk-export` | Export final scene to VTK format |
| `--vtk-time-series` | Export all frames as VTK time series |

## 💡 Use Cases

### CFD Visualization

```python
from manim import *
from manim.vtk import add_scalar_field, add_vector_field

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

Manim-VTK adds a new renderer layer:

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

| Mobject Type | VTK Export | Notes |
|--------------|------------|-------|
| `VMobject` (2D shapes) | ✅ | Converted to PolyData with colors |
| `Surface` | ✅ | Full mesh with UV coordinates |
| `Sphere`, `Cube`, etc. | ✅ | 3D primitives |
| `ParametricSurface` | ✅ | Parametric surfaces |
| `VGroup` | ✅ | Exported as MultiBlock |

## 🔬 Scientific Features

### Scalar Fields

Attach scalar data (pressure, temperature) to VTK exports:

```python
from manim.vtk import add_scalar_field

# After creating polydata
add_scalar_field(polydata, "pressure", pressure_values)
```

### Vector Fields

Attach velocity/force fields for glyphs and streamlines:

```python
from manim.vtk import add_vector_field

# Attach velocity (U, V, W components)
add_vector_field(polydata, "velocity", velocity_vectors)
```

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
