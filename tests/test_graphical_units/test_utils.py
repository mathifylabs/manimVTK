from __future__ import annotations

from manimvtk.utils.testing.frames_comparison import frames_comparison

__module_test__ = "utils"


@frames_comparison
def test_pixel_error_threshold(scene):
    """Scene produces black frame, control data has 11 modified pixel values."""
    pass
