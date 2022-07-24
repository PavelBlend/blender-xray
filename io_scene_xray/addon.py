from . import formats
from . import ui
from . import menus
from . import panels
from . import prefs
from . import hotkeys
from . import ops
from . import rig
from . import props
from . import icons
from . import handlers
from . import viewport
from . import edit_helpers
from . import viewer
from . import translate
from . import tests


modules = (
    icons,
    prefs,
    viewer,
    ops,
    props,
    formats,
    handlers,
    ui,
    panels,
    menus,
    hotkeys,
    rig,
    edit_helpers,
    viewport,
    translate,
    tests
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
