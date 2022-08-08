# blender modules
import bpy

# addon modules
from . import utils


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
    bpy.app.handlers.load_post.append(load_post)
    utils.version.get_scene_update_post().append(scene_update_post)


def unregister():
    utils.version.get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
