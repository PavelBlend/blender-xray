import os.path

import bpy

from ... import utils
from ... import log


class ImportContext:
    def __init__(
            self,
            textures,
            soc_sgroups,
            import_motions,
            split_by_materials,
            operator,
            use_motion_prefix_name,
            objects=''
        ):

        self.version = utils.plugin_version_number()
        self.textures_folder = textures
        self.objects_folder = objects
        self.soc_sgroups = soc_sgroups
        self.import_motions = import_motions
        self.split_by_materials = split_by_materials
        self.operator = operator
        self.loaded_materials = None
        self.use_motion_prefix_name = use_motion_prefix_name

    def before_import_file(self):
        self.loaded_materials = {}

    def image(self, relpath):
        relpath = relpath.lower().replace('\\', os.path.sep)
        if not self.textures_folder:
            result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
            result.source = 'FILE'
            result.filepath = relpath + '.dds'
            return result

        filepath = os.path.abspath(
            os.path.join(self.textures_folder, relpath + '.dds')
        )
        result = None
        for i in bpy.data.images:
            if bpy.path.abspath(i.filepath) == filepath:
                result = i
                break
        if result is None:
            try:
                result = bpy.data.images.load(filepath)
            except RuntimeError as ex:  # e.g. 'Error: Cannot read ...'
                log.warn(ex)
                result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
                result.source = 'FILE'
                result.filepath = filepath
        return result
