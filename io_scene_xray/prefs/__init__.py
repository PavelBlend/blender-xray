# addon modules
from . import base
from . import hotkeys
from . import ops
from . import props
from . import preset
from . import paths
from . import ui


modules = (ops, paths, props, base, preset, hotkeys)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
