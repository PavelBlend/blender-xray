# addon modules
from . import gl_utils
from . import gpu_utils
from . import const
from .. import utils


class DrawContext:
    def __init__(self):

        # init geometry lists
        self.geom = {}
        for data_type in ('shape', 'mass'):
            self.geom[data_type] = {}
            for state_type in ('obj', 'active', 'sel', 'desel'):
                self.geom[data_type][state_type] = {}
                for geom_type in ('coords', 'lines', 'faces'):
                    self.geom[data_type][state_type][geom_type] = []

    def draw(self):
        utils.draw.set_gl_line_width(const.LINE_WIDTH)

        colors = {
            'obj': (0.5, 0.5, 0.5, 0.8),
            'active': (1.0, 1.0, 1.0, 0.8),
            'sel': (0.0, 1.0, 1.0, 0.8),
            'desel': (0.0, 0.0, 1.0, 0.8)
        }

        for data_type, data in self.geom.items():
            for state_type, state in data.items():

                coords = state['coords']
                lines = state['lines']
                faces = state['faces']

                if data_type == 'shape': 
                    utils.draw.set_gl_blend_mode()
                    utils.draw.set_gl_state()
                elif data_type == 'mass': 
                    utils.draw.reset_gl_state()

                color = colors[state_type]

                gpu_utils.draw_geom(
                    coords,
                    lines,
                    faces,
                    color,
                    0.2
                )
