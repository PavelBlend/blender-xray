# addon modules
from . import base
from . import collapsible
from . import dynamic_menu
from . import icons
from . import list_helper
from . import motion_filter
from . import motion_list
from . import motion_refs
from . import omf_list


modules = (
    collapsible,
    dynamic_menu,
    icons,
    list_helper,
    motion_filter,
    motion_list,
    motion_refs,
    omf_list
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
