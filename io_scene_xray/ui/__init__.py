# addon modules
from . import base
from . import collapsible
from . import dynamic_menu
from . import icons
from . import list_helper
from . import motion_filter


modules = (
    collapsible,
    dynamic_menu,
    icons,
    list_helper,
    motion_filter,
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
