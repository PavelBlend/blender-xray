# addon modules
from . import gl_utils
from . import gpu_utils
from . import const
from .. import utils


class DrawContext:
    def __init__(self):
        self.coords_obj = []
        self.lines_obj = []
        self.faces_obj = []

        self.coords_active = []
        self.lines_active = []
        self.faces_active = []

        self.coords_sel = []
        self.lines_sel = []
        self.faces_sel = []

        self.coords_desel = []
        self.lines_desel = []
        self.faces_desel = []

    def draw(self):
        self._draw_shapes(
            self.coords_obj,
            self.lines_obj,
            self.faces_obj,
            (0.8, 0.8, 0.8, 0.8),
            0.2
        )
        self._draw_shapes(
            self.coords_active,
            self.lines_active,
            self.faces_active,
            (1.0, 1.0, 1.0, 0.8),
            0.2
        )
        self._draw_shapes(
            self.coords_sel,
            self.lines_sel,
            self.faces_sel,
            (0.0, 0.8, 0.8, 0.8),
            0.2
        )
        self._draw_shapes(
            self.coords_desel,
            self.lines_desel,
            self.faces_desel,
            (0.0, 0.0, 0.8, 0.8),
            0.2
        )

    def _draw_shapes(self, coords, lines, faces, color, alpha_factor):
        utils.draw.set_gl_blend_mode()
        utils.draw.set_gl_state()
        utils.draw.set_gl_line_width(const.LINE_WIDTH)
        gpu_utils.draw_geom(
            coords,
            lines,
            faces,
            color,
            alpha_factor
        )
