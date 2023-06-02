# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import log
from .. import text
from .. import utils


# base context
class Context:
    def __init__(self):
        self.filepath = None
        self.operator = None
        self.multiply = utils.version.get_multiply()
        self.version = utils.addon_version_number()
        self.errors = []
        self.fatal_errors = []


class MeshContext(Context):
    def __init__(self):
        super().__init__()
        pref = utils.version.get_preferences()
        self.tex_folder = pref.textures_folder_auto
        self.tex_folder_repored = False

    @property
    def textures_folder(self):
        if not self.tex_folder:
            if not self.tex_folder_repored:
                self.tex_folder_repored = True
                self.operator.report(
                    {'WARNING'},
                    text.get_text(text.warn.tex_folder_not_spec)
                )
        return self.tex_folder


# import contexts
class ImportContext(Context):
    pass


class ImportMeshContext(MeshContext):
    def image(self, relpath):
        relpath = relpath.lower().replace('\\', os.path.sep)
        if not self.textures_folder:
            result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
            result.source = 'FILE'
            result.filepath = relpath + '.dds'
            utils.stats.created_img()
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
            if os.path.exists(filepath):
                try:
                    result = bpy.data.images.load(filepath)
                    utils.stats.created_img()
                except RuntimeError:    # e.g. 'Error: Cannot read ...'
                    pass

            if not result:
                log.warn('texture file not found', path=filepath)
                result = bpy.data.images.new(os.path.basename(relpath), 0, 0)
                utils.stats.created_img()
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
    pass


class ExportMeshContext(ExportContext, MeshContext):
    def __init__(self):
        super().__init__()
        self.texname_from_path = None


class ExportAnimationContext(ExportContext):
    def __init__(self):
        super().__init__()
        self.export_motions = None


class ExportAnimationOnlyContext(ExportContext):
    def __init__(self):
        super().__init__()
        self.bpy_arm_obj = None
