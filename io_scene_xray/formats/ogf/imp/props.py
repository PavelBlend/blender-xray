# standart modules
import os

# addon modules
from .. import fmt
from ... import omf
from .... import rw
from .... import log
from .... import text


def read_description(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_DESC, None)

    if chunk_data:
        packed_reader = rw.read.PackedReader(chunk_data)

        source_file = packed_reader.gets()

        try:
            build_name = packed_reader.gets()
            build_time = packed_reader.uint32()

            visual.create_name = packed_reader.gets()
            visual.create_time = packed_reader.uint32()

            visual.modif_name = packed_reader.gets()
            visual.modif_time = packed_reader.uint32()

        except rw.read.PackedReader.Errors as err:
            log.warn(
                text.warn.ogf_bad_description,
                error=str(err),
                file=visual.file_path
            )


def read_user_data(chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_USERDATA, None)

    if chunk_data:
        packed_reader = rw.read.PackedReader(chunk_data)

        visual.user_data = packed_reader.gets(
            onerror=lambda err: log.warn(
                text.warn.object_bad_userdata,
                error=str(err),
                file=visual.file_path
            )
        )


def read_lods(context, chunks, ogf_chunks, visual):
    chunk_data = chunks.pop(ogf_chunks.S_LODS, None)

    if chunk_data:
        packed_reader = rw.read.PackedReader(chunk_data)

        visual.lod = packed_reader.gets()

        if visual.lod.endswith('\r\n'):
            visual.lod = visual.lod[ : -2]


def _read_motion_refs_soc(data, visual):
    packed_reader = rw.read.PackedReader(data)
    visual.motion_refs = packed_reader.gets().split(',')


def _read_motion_refs_cs_cop(data, visual):
    packed_reader = rw.read.PackedReader(data)

    count = packed_reader.uint32()
    visual.motion_refs = [packed_reader.gets() for index in range(count)]


def import_bone_parts(context, visual):
    if not visual.motion_refs:
        return

    # search meshes folder
    meshes_folder = None
    meshes_folders = context.meshes_folders
    for folder in meshes_folders:
        if os.path.exists(folder):
            meshes_folder = folder
            break

    if meshes_folder:

        # get *.omf path
        omf_path = None

        for ref in visual.motion_refs:
            relative_path = ref.replace('\\', os.sep)
            relative_path = relative_path.replace('/', os.sep)
            ref_path = os.path.join(meshes_folder, relative_path)
            omf_path = ref_path + os.extsep + 'omf'

            if os.path.exists(omf_path):
                break

        if omf_path:

            # read file
            data = None
            try:
                data = rw.utils.read_file(omf_path)
            except:
                pass

            if data:

                # get params chunk
                chunks = rw.utils.get_chunks(data)
                params_data = chunks.get(fmt.Chunks_v4.S_SMPARAMS_1, None)

                # import bone parts
                if params_data:
                    params_chunk = 1
                    context.import_bone_parts = True
                    context.bpy_arm_obj = visual.arm_obj
                    omf.imp.read_params(
                        params_data,
                        context,
                        params_chunk
                    )


def read_motion_references(chunks, ogf_chunks, visual):
    data = chunks.pop(ogf_chunks.S_MOTION_REFS_0, None)

    if data:
        # soc
        _read_motion_refs_soc(data, visual)

    else:
        # cs/cop
        data = chunks.pop(ogf_chunks.S_MOTION_REFS_2, None)
        if data:
            _read_motion_refs_cs_cop(data, visual)
