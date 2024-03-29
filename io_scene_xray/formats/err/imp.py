# standart modules
import os

# blender modules
import bpy

# addon modules
from . import fmt
from ... import utils
from ... import text
from ... import log
from ... import rw


def import_(filepath, chunked_reader):
    for chunk_id, chunk_data in chunked_reader:
        if not chunk_id in (fmt.Chunks.INVALID, fmt.Chunks.INVALID_LE):
            continue

        packed_reader = rw.read.PackedReader(chunk_data)
        faces_count = packed_reader.uint32()

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
                color = packed_reader.uint32()    # RGBA
                draw_index = packed_reader.getf('<H')[0]    # bool
                m = packed_reader.getf('<H')[0]    # ?
                faces.append(face_indices)

        # import geometry
        object_name = os.path.basename(filepath.lower())
        bpy_mesh = bpy.data.meshes.new(object_name)
        bpy_obj = bpy.data.objects.new(object_name, bpy_mesh)
        utils.version.set_object_show_xray(bpy_obj, True)
        utils.version.link_object(bpy_obj)
        bpy_mesh.from_pydata(vertices, (), faces)
        utils.stats.created_obj()
        utils.stats.created_msh()


@log.with_context(name='import-err')
@utils.stats.timer
def import_file(file_path, imp_context):
    utils.stats.status('Import File', file_path)

    chunked_reader = rw.utils.get_file_reader(file_path, chunked=True)
    import_(file_path, chunked_reader)
