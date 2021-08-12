from . import plugin
from . import menus


modules = (
    plugin,
    menus
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
