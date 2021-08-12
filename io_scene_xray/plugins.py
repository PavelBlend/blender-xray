# blender modules
import bpy

# addon modules
from . import utils
from . import version_utils

# plugin modules
from . import details
from . import dm
from . import err
from . import scene
from . import obj
from . import anm
from . import skl
from . import bones
from . import ogf
from . import level
from . import omf


_INITIALIZER = utils.ObjectsInitializer([
    'objects',
    'materials',
])


@bpy.app.handlers.persistent
def load_post(_):
    _INITIALIZER.sync('LOADED', bpy.data)


@bpy.app.handlers.persistent
def scene_update_post(_):
    _INITIALIZER.sync('CREATED', bpy.data)


def register():
    details.ops.register()
    obj.imp.ops.register()
    obj.exp.ops.register()
    anm.ops.register()
    dm.ops.register()
    bones.ops.register()
    ogf.ops.register()
    skl.ops.register()
    omf.ops.register()
    scene.ops.register()
    level.ops.register()
    err.ops.register()

    bpy.app.handlers.load_post.append(load_post)
    version_utils.get_scene_update_post().append(scene_update_post)


def unregister():
    err.ops.unregister()
    dm.ops.unregister()
    bones.ops.unregister()
    ogf.ops.unregister()
    level.ops.unregister()
    scene.ops.unregister()
    omf.ops.unregister()
    skl.ops.unregister()
    anm.ops.unregister()
    obj.exp.ops.unregister()
    obj.imp.ops.unregister()
    details.ops.unregister()

    version_utils.get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
