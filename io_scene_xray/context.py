import os

import bpy

from . import utils, version_utils, plugin_prefs


# base context
class Context:
    def __init__(self):
        self.filepath = None
        self.operator = None
        self.multiply = version_utils.get_multiply()
        self.version = utils.plugin_version_number()


# import contexts
class ImportContext(Context):
    def __init__(self):
        Context.__init__(self)


class ImportMeshContext(ImportContext):
    def __init__(self):
        ImportContext.__init__(self)
        self.textures_folder = None


class ImportAnimationBaseContext(ImportContext):
    def __init__(self):
        ImportContext.__init__(self)
        self.add_actions_to_motion_list = None
        self.selected_names = None
        self.use_motion_prefix_name = None
        self.motions_filter = None


class ImportAnimationContext(ImportAnimationBaseContext):
    def __init__(self):
        ImportAnimationBaseContext.__init__(self)
        self.import_motions = None


class ImportAnimationOnlyContext(ImportAnimationBaseContext):
    def __init__(self):
        ImportAnimationBaseContext.__init__(self)
        self.bpy_arm_obj = None


# export contexts
class ExportContext(Context):
    def __init__(self):
        Context.__init__(self)


class ExportMeshContext(ExportContext):
    def __init__(self):
        ExportContext.__init__(self)
        prefs = plugin_prefs.get_preferences()
        self.textures_folder = prefs.textures_folder_auto
        self.texname_from_path = None


class ExportAnimationContext(ExportContext):
    def __init__(self):
        ExportContext.__init__(self)
        self.export_motions = None


class ExportAnimationOnlyContext(ExportContext):
    def __init__(self):
        ExportContext.__init__(self)
        self.bpy_arm_obj = None
