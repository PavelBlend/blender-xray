from . import plugins
from . import ui
from . import menus
from . import panels
from . import plugin_prefs
from . import hotkeys
from . import ops
from . import props
from . import icons
from . import handlers
from . import viewport
from . import skls_browser
from . import edit_helpers


modules = (
    icons,
    plugin_prefs,
    skls_browser,
    props,
    plugins,
    handlers,
    ui,
    panels,
    menus,
    hotkeys,
    ops,
    edit_helpers,
    viewport
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
