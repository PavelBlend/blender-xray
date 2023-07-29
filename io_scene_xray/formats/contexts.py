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
        self._tex_folder = utils.ie.get_textures_folder()
        self.tex_folder_repored = False

    @property
    def tex_folder(self):
        if not self._tex_folder:
            if not self.tex_folder_repored:
                self.tex_folder_repored = True
                self.operator.report(
                    {'WARNING'},
                    text.get_text(text.warn.tex_folder_not_spec)
                )
        return self._tex_folder


# import contexts
class ImportContext(Context):
    pass


class ImportMeshContext(MeshContext):
    def image(self, relpath):
        relpath = utils.tex.normalize_tex_relpath(relpath)

        if not self.tex_folder:
            relpath = utils.tex.add_tex_ext(relpath)
            return utils.tex.create_empty_img(relpath)

        tex_abspath = utils.tex.make_abs_tex_path(self.tex_folder, relpath)

        bpy_img = utils.tex.search_image_by_tex_path(tex_abspath)

        if not bpy_img:
            bpy_img = utils.tex.load_image_by_tex_path(tex_abspath)

            if not bpy_img:
                log.warn('Texture file not found', path=tex_abspath)
                bpy_img = utils.tex.create_empty_img(tex_abspath)

        return bpy_img


class ImportAnimationBaseContext(ImportContext):
    def __init__(self):
        super().__init__()
        self.add_to_motion_list = None
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
