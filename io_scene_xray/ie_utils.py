# standart modules
import os

# addon modules
from . import utils
from . import icons
from . import text
from . import log


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


def check_file_exists(file_path):
    if not os.path.exists(file_path):
        raise utils.AppError(
            text.error.file_not_found,
            log.props(file_path=file_path)
        )
