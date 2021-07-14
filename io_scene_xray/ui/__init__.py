from . import (
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
    view3d,
    icons
)


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
