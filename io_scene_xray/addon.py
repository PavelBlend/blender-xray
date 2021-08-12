from . import plugin
from . import ui
from . import menus
from . import panels
from . import plugin_prefs
from . import hotkeys
from . import ops
from . import props
from . import icons
from . import skls_browser
from . import edit_helpers
from . import xray_io
from . import utils


xray_io.ENCODE_ERROR = utils.AppError


modules = (
    icons,
    plugin_prefs,
    skls_browser,
    props,
    plugin,
    ui,
    panels,
    menus,
    hotkeys,
    ops,
    edit_helpers,
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
