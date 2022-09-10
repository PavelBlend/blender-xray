from . import formats
from . import ui
from . import menus
from . import panels
from . import prefs
from . import ops
from . import props
from . import icons
from . import handlers
from . import viewport
from . import translate
from . import tests


modules = (
    icons,
    prefs,
    ops,
    props,
    formats,
    handlers,
    ui,
    panels,
    menus,
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
