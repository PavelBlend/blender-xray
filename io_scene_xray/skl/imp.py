# standart modules
import os

# addon modules
from .. import log
from .. import utils
from .. import contexts
from .. import xray_io
from .. import xray_motions
from .. import ie_utils


class ImportSklContext(contexts.ImportAnimationOnlyContext):
    def __init__(self):
        super().__init__()
        self.filename = None


def _import_skl(file_path, context, chunked_reader):
    basename = os.path.basename(file_path.lower())
    name = os.path.splitext(basename)[0]
    if not context.motions_filter(name):
        return
    for cid, cdata in chunked_reader:
        if cid == 0x1200:
            reader = xray_io.PackedReader(cdata)
            bonesmap = {
                bone.name.lower(): bone
                for bone in context.bpy_arm_obj.data.bones
            }
            xray_motions.import_motion(
                reader, context, bonesmap, set(), skl_file_name=name
            )
        else:
            log.debug('unknown chunk', cid=cid)


@log.with_context(name='file')
def import_skl_file(file_path, context):
    log.update(path=file_path)
    ie_utils.check_file_exists(file_path)
    file_data = utils.read_file(file_path)
    chunked_reader = xray_io.ChunkedReader(file_data)
    _import_skl(file_path, context, chunked_reader)


@log.with_context(name='file')
def import_skls_file(file_path, context):
    log.update(path=file_path)
    ie_utils.check_file_exists(file_path)
    file_data = utils.read_file(file_path)
    reader = xray_io.PackedReader(file_data)
    xray_motions.import_motions(reader, context, context.motions_filter)
