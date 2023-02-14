# addon modules
from . import formats
from . import ui
from . import menus
from . import ops
from . import panels
from . import prefs
from . import props
from . import handlers
from . import viewport
from . import text


modules = (
    ops,
    props,
    formats,
    prefs,
    handlers,
    ui,
    panels,
    menus,
    viewport,
    text
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
