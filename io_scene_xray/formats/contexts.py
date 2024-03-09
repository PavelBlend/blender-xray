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
        self._children = None

    @property
    def children(self):
        if not self._children:
            self._children = {}

            for obj in bpy.data.objects:
                self._children[obj.name] = []

            for child in bpy.data.objects:
                parent = child.parent

                if parent:
                    self._children[parent.name].append(child)

        return self._children


class MeshContext(Context):
    def __init__(self):
        super().__init__()

        (
            self.tex_dir,
            self.tex_mod_dir,
            self.lvl_folder,
            self.lvl_mod_folder
        ) = utils.ie.get_tex_dirs()

        self.level_name = None
        self.level_path = None
        self.tex_folder_repored = False

    @property
    def tex_folder(self):
        if not self.tex_dir:
            if not self.tex_folder_repored:
                self.tex_folder_repored = True
                self.operator.report(
                    {'WARNING'},
                    text.warn.tex_folder_not_spec
                )
        return self.tex_dir

    @property
    def tex_mod_folder(self):
        return self.tex_mod_dir


# import contexts
class ImportContext(Context):
    pass


class ImportMeshContext(MeshContext):
    def image(self, relpath):
        relpath = utils.tex.normalize_tex_relpath(relpath)

        # create empty image
        if not self.tex_mod_folder and not self.tex_folder and not self.level_name:
            relpath = utils.tex.add_tex_ext(relpath)
            return utils.tex.create_empty_img(relpath)

        # collect texture folders
        tex_dirs = [self.level_path, ]
        if self.level_name:
            for folder in (self.lvl_mod_folder, self.lvl_folder):
                if folder:
                    level_folder = os.path.join(folder, self.level_name)
                    tex_dirs.append(level_folder)
        tex_dirs.extend([self.tex_mod_folder, self.tex_folder])

        # collect texture absolute paths
        abs_paths = []
        for tex_dir in tex_dirs:
            if not tex_dir:
                continue
            tex_abspath = utils.tex.make_abs_tex_path(tex_dir, relpath)
            abs_paths.append(tex_abspath)

        # collect bpy-images
        img_files = []
        exists_paths = []
        for tex_path in abs_paths:
            bpy_img = utils.tex.search_image_by_tex_path(tex_path)
            file_exists = os.path.exists(tex_path)
            if bpy_img:
                img_files.append((bpy_img, file_exists))
            if file_exists:
                exists_paths.append(tex_path)

        # search bpy-images
        bpy_img = None
        for img, file_exists in img_files:
            if file_exists:
                bpy_img = img
                break

        if not bpy_img and not exists_paths:
            if img_files:
                bpy_img = img_files[0][0]

        # load bpy-image
        if not bpy_img:
            for tex_abspath in abs_paths:
                bpy_img = utils.tex.load_image_by_tex_path(tex_abspath)
                if bpy_img:
                    break

            # create empty image
            if not bpy_img:
                tex_abspath = utils.tex.make_abs_tex_path(self.tex_folder, relpath + '.dds')
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
