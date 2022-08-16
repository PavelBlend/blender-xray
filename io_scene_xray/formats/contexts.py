# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import log
from .. import utils


# base context
class Context:
    def __init__(self):
        self.filepath = None
        self.operator = None
        self.multiply = utils.version.get_multiply()
        self.version = utils.plugin_version_number()
        self.errors = []


# import contexts
class ImportContext(Context):
    def __init__(self):
        super().__init__()


class ImportMeshContext(ImportContext):
    def __init__(self):
        super().__init__()
        self.textures_folder = None

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
        for bpy_image in bpy.data.images:
            if bpy.path.abspath(bpy_image.filepath) == filepath:
                result = bpy_image
                break
        if result is None:
            try:
                result = bpy.data.images.load(filepath)
            except RuntimeError:    # e.g. 'Error: Cannot read ...'
                log.warn('texture file not found', path=filepath)
                result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
                result.source = 'FILE'
                result.filepath = filepath
        return result


class ImportAnimationBaseContext(ImportContext):
    def __init__(self):
        super().__init__()
        self.add_actions_to_motion_list = None
        self.selected_names = None
        self.motions_filter = None


class ImportAnimationContext(ImportAnimationBaseContext):
    def __init__(self):
        super().__init__()
        self.import_motions = None


class ImportAnimationOnlyContext(ImportAnimationBaseContext):
    def __init__(self):
        super().__init__()
        self.bpy_arm_obj = None


# export contexts
class ExportContext(Context):
    def __init__(self):
        super().__init__()


class ExportMeshContext(ExportContext):
    def __init__(self):
        super().__init__()
        preferences = utils.version.get_preferences()
        self.textures_folder = preferences.textures_folder_auto
        self.texname_from_path = None


class ExportAnimationContext(ExportContext):
    def __init__(self):
        super().__init__()
        self.export_motions = None


class ExportAnimationOnlyContext(ExportContext):
    def __init__(self):
        super().__init__()
        self.bpy_arm_obj = None
