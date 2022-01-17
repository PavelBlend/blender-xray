# addon modules
from . import utils
from . import icons


# import/export utils


def get_draw_fun(operator):
    def menu_func(self, context):
        icon = icons.get_stalker_icon()
        self.layout.operator(
            operator.bl_idname,
            text=utils.build_op_label(operator),
            icon_value=icon
        )
    operator.draw_fun = menu_func
    return menu_func
