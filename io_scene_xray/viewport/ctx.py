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

        pref = utils.version.get_preferences()
        colors_solid = {
            'obj': pref.gl_solid_col_obj,
            'active': pref.gl_solid_col_active,
            'sel': pref.gl_solid_col_sel,
            'desel': pref.gl_solid_col_desel
        }
        colors_wire = {
            'obj': pref.gl_object_mode_shape_color,
            'active': pref.gl_active_shape_color,
            'sel': pref.gl_select_shape_color,
            'desel': pref.gl_shape_color
        }

        if utils.version.IS_28:
            draw_fun = gpu_utils.draw_geom
        else:
            draw_fun = gl_utils.draw_geom

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

                color_solid = colors_solid[state_type]
                color_wire = colors_wire[state_type]

                draw_fun(
                    coords,
                    lines,
                    faces,
                    color_solid,
                    color_wire
                )
