import bpy

from . import obj, mesh, material, armature, bone, action, scene


modules = (obj, mesh, material, armature, bone, action, scene)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
