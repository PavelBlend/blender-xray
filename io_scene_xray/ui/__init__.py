# addon modules
from . import action
from . import armature
from . import bone
from . import collapsible
from . import dynamic_menu
from . import edit_helper
from . import list_helper
from . import material
from . import mesh
from . import motion_list
from . import obj
from . import scene
from . import view3d


modules = (
    action,
    armature,
    bone,
    collapsible,
    dynamic_menu,
    edit_helper,
    list_helper,
    material,
    mesh,
    motion_list,
    obj,
    scene,
    view3d
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
