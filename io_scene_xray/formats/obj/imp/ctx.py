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
        self.objs_folder = pref.objects_folder_auto

    def before_import_file(self):
        self.loaded_materials = {}

    @property
    def objects_folder(self):
        if not self.objs_folder:
            if not self.reported:
                self.reported = True
                self.operator.report(
                    {'WARNING'},
                    text.get_text(text.warn.objs_folder_not_spec)
                )
        return self.objs_folder


class ImportObjectAnimationContext(contexts.ImportAnimationContext):
    pass


class ImportObjectContext(
        ImportObjectMeshContext,
        ImportObjectAnimationContext
    ):
    pass
