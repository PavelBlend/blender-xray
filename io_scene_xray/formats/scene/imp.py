# standart modules
import os

# addon modules
from .. import le
from ... import text
from ... import log
from ... import utils
from ... import rw


URL_FOR_ERR = 'https://github.com/PavelBlend/blender-xray/wiki/Scene-Selection-Import'


def _read_version(version_chunk):
    packed_reader = rw.read.PackedReader(version_chunk)
    version = packed_reader.uint32()

    if version != le.fmt.SCENE_VERSION:
        raise log.AppError(
            text.error.scene_ver,
            log.props(version=version)
        )


def import_(filepath, chunked_reader, import_context):
    # get chunks
    data_chunk_id = le.fmt.ToolsChunks.DATA + le.fmt.ClassID.OBJECT
    version_chunk = chunked_reader.get_chunk(le.fmt.SceneChunks.VERSION)
    data_chunk = chunked_reader.get_chunk(data_chunk_id)

    if not version_chunk or not data_chunk:
        utils.draw.show_message(
            text.error.scene_incorrect_file,
            (text.get_text(text.error.scene_err_info), ),
            text.get_text(text.warn.info_title),
            'ERROR',
            operators=('wm.url_open', ),
            operators_props=({'url': URL_FOR_ERR, }, ),
            operators_labels=(URL_FOR_ERR, )
        )
        return

    # read
    _read_version(version_chunk)
    ref, pos, rot, scl = le.read.read_data(data_chunk)

    # import
    name = os.path.basename(filepath)
    le.imp.import_objects(name, import_context, ref, pos, rot, scl)


@log.with_context(name='import-scene-selection')
@utils.stats.timer
def import_file(file_path, import_context):
    utils.stats.status('Import File', file_path)

    chunked_reader = rw.utils.get_file_reader(file_path, chunked=True)
    import_(file_path, chunked_reader, import_context)
