# addon modules
from ... import contexts


class ImportObjectMeshContext(contexts.ImportMeshContext):
    def __init__(self):
        super().__init__()
        self.soc_sgroups = None
        self.split_by_materials = None
        self.objects_folder = None

    def before_import_file(self):
        self.loaded_materials = {}


class ImportObjectAnimationContext(contexts.ImportAnimationContext):
    def __init__(self):
        super().__init__()


class ImportObjectContext(
        ImportObjectMeshContext,
        ImportObjectAnimationContext
    ):
    def __init__(self):
        super().__init__()
