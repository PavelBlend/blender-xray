# addon modules
from ... import contexts
from .... import utils
from .... import text


class ImportObjectMeshContext(contexts.ImportMeshContext):
    def __init__(self):
        super().__init__()
        self.soc_sgroups = None
        self.split_by_materials = None
        pref = utils.version.get_preferences()
        self.reported = False
        self.objs_folders = utils.ie.get_pref_paths('objects_folder')

    def before_import_file(self):
        self.loaded_materials = {}

    @property
    def objects_folders(self):
        if not self.objs_folders:
            if not self.reported:
                self.reported = True
                self.operator.report(
                    {'WARNING'},
                    text.warn.objs_folder_not_spec
                )
        return self.objs_folders


class ImportObjectAnimationContext(contexts.ImportAnimationContext):
    pass


class ImportObjectContext(
        ImportObjectMeshContext,
        ImportObjectAnimationContext
    ):
    pass
