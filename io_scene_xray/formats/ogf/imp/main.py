# addon modules
from . import types
from . import body
from .... import log
from .... import utils
from .... import rw


@log.with_context(name='import-ogf')
def import_file(context, file_path, file_name):
    log.update(file=file_path)
    utils.ie.check_file_exists(file_path)
    data = rw.utils.read_file(file_path)

    # init visual
    visual = types.Visual()
    visual.file_path = file_path
    visual.visual_id = 0
    visual.name = file_name
    visual.is_root = True

    body.import_ogf_visual(context, data, visual)
