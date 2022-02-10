# standart modules
import os

# blender modules
import bpy

# addon modules
from . import fmt
from .. import utils
from .. import ie_utils
from .. import text
from .. import log
from .. import version_utils
from .. import xray_io


def import_(filepath, chunked_reader, operator):
    for chunk_id, chunk_data in chunked_reader:
        if not chunk_id in (fmt.Chunks.INVALID, fmt.Chunks.INVALID_LE):
            continue

        packed_reader = xray_io.PackedReader(chunk_data)
        faces_count = packed_reader.getf('<I')[0]

        if not faces_count:
            log.warn(
                text.warn.err_no_faces,
                file=filepath
            )
            return

        vertices = []
        faces = []
        vertex_order = [0, 2, 1]

        # err file from xrlc
        if chunk_id == fmt.Chunks.INVALID:
            for face_index in range(faces_count):
                face_indices = []
                for vertex_index in range(3):
                    coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                    vertices.append((coord_x, coord_z, coord_y))
                    face_indices.append(
                        face_index * 3 + vertex_order[vertex_index]
                    )
                faces.append(face_indices)

        # err file from level editor
        elif chunk_id == fmt.Chunks.INVALID_LE:
            for face_index in range(faces_count):
                face_indices = []
                for vertex_index in range(3):
                    coord_x, coord_y, coord_z = packed_reader.getf('<3f')
                    vertices.append((coord_x, coord_z, coord_y))
                    face_indices.append(
                        face_index * 3 + vertex_order[vertex_index]
                    )
                color = packed_reader.getf('<I')[0]    # RGBA
                draw_index = packed_reader.getf('<H')[0]    # bool
                m = packed_reader.getf('<H')[0]    # ?
                faces.append(face_indices)

        # import geometry
        object_name = os.path.basename(filepath.lower())
        bpy_mesh = bpy.data.meshes.new(object_name)
        bpy_obj = bpy.data.objects.new(object_name, bpy_mesh)
        version_utils.set_object_show_xray(bpy_obj, True)
        version_utils.link_object(bpy_obj)
        bpy_mesh.from_pydata(vertices, (), faces)


@log.with_context(name='import-err')
def import_file(file_path, operator):
    log.update(path=file_path)
    ie_utils.check_file_exists(file_path)
    data = utils.read_file(file_path)
    chunked_reader = xray_io.ChunkedReader(data)
    import_(file_path, chunked_reader, operator)
