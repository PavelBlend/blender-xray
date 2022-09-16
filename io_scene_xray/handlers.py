# blender modules
import bpy

# addon modules
from . import utils


class DataBlocksInitContext:
    def __init__(self, operation):
        self.operation = operation
        self.addon_version_number = utils.addon_version_number()


class DataBlocksSet:
    def __init__(self):
        self._hashes = set()

    def sync(self, bpy_collect, context):
        hashes_old = self._hashes
        if len(bpy_collect) == len(hashes_old):
            return
        hashes_new = set()
        for data_block in bpy_collect:
            block_hash = hash(data_block)
            hashes_new.add(block_hash)
            if not block_hash in hashes_old:
                data_block.xray.initialize(context)
        self._hashes = hashes_new


class DataBlocksInitializer:
    def __init__(self, collect_ids):
        self._collects = {collect: DataBlocksSet() for collect in collect_ids}

    def sync(self, operation):
        context = DataBlocksInitContext(operation)
        for collect_name, data_blocks_set in self._collects.items():
            bpy_collect = getattr(bpy.data, collect_name)
            data_blocks_set.sync(bpy_collect, context)


bpy_data_init_collects = ['objects', 'materials']
_INITIALIZER = DataBlocksInitializer(bpy_data_init_collects)


@bpy.app.handlers.persistent
def load_post(_):
    _INITIALIZER.sync('LOADED')


@bpy.app.handlers.persistent
def scene_update_post(_):
    _INITIALIZER.sync('CREATED')


def register():
    bpy.app.handlers.load_post.append(load_post)
    utils.version.get_scene_update_post().append(scene_update_post)


def unregister():
    utils.version.get_scene_update_post().remove(scene_update_post)
    bpy.app.handlers.load_post.remove(load_post)
