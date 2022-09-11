# blender modules
import bpy

# addon modules
from . import utils


class InitializationContext:
    def __init__(self, operation):
        self.operation = operation
        self.plugin_version_number = utils.plugin_version_number()
        self.thing = None


class ObjectSet:
    def __init__(self):
        self._set = set()

    def sync(self, objects, callback):
        _old = self._set
        if len(objects) == len(_old):
            return
        _new = set()
        for obj in objects:
            hsh = hash(obj)
            _new.add(hsh)
            if hsh not in _old:
                callback(obj)
        self._set = _new


class ObjectsInitializer:
    def __init__(self, keys):
        self._sets = [(key, ObjectSet()) for key in keys]

    def sync(self, operation, collections):
        ctx = InitializationContext(operation)

        def init_thing(thing):
            ctx.thing = thing
            thing.xray.initialize(ctx)

        for key, obj_set in self._sets:
            things = getattr(collections, key)
            obj_set.sync(things, init_thing)


_INITIALIZER = ObjectsInitializer([
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
