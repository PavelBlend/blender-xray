# standart modules
import os

# addon modules
from .. import contexts
from .. import motions
from ... import log
from ... import utils
from ... import rw


class ImportSklContext(contexts.ImportAnimationOnlyContext):
    def __init__(self):
        super().__init__()
        self.filename = None


def _import_skl(file_path, context, chunked_reader):
    basename = os.path.basename(file_path.lower())
    name = os.path.splitext(basename)[0]
    if not context.motions_filter(name):
        return
    has_main_chunk = False
    for cid, cdata in chunked_reader:
        if cid == 0x1200:
            has_main_chunk = True
            reader = rw.read.PackedReader(cdata)
            bonesmap = {
                bone.name.lower(): bone
                for bone in context.bpy_arm_obj.data.bones
            }
            motions.imp.import_motion(
                reader, context, bonesmap, set(), skl_file_name=name
            )
        else:
            log.debug('unknown chunk', cid=cid)
    if not has_main_chunk:
        raise 'skl file has no main chunk'


@log.with_context(name='import-skl')
@utils.stats.timer
def import_skl_file(file_path, context):
    utils.stats.status('Import File: "{}"'.format(file_path))

    chunked_reader = rw.utils.get_file_reader(file_path, chunked=True)
    _import_skl(file_path, context, chunked_reader)


@log.with_context(name='import-skls')
@utils.stats.timer
def import_skls_file(file_path, context):
    utils.stats.status('Import File: "{}"'.format(file_path))

    reader = rw.utils.get_file_reader(file_path, chunked=False)
    motions.imp.import_motions(reader, context, context.motions_filter)
