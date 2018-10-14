
import os

import bpy

from ..xray_io import PackedReader, ChunkedReader
from .fmt import Chunks


def import_(filepath, chunked_reader, operator):
    for chunk_id, chunk_data in chunked_reader:
        if chunk_id == Chunks.INVALID or chunk_id == Chunks.INVALID_EXPORT:
            packed_reader = PackedReader(chunk_data)
            faces_count = packed_reader.getf('I')[0]

            if faces_count:
                object_name = os.path.basename(filepath.lower())
                bpy_mesh = bpy.data.meshes.new(object_name)
                bpy_obj = bpy.data.objects.new(object_name, bpy_mesh)
                bpy_obj.show_x_ray = True
                bpy.context.scene.objects.link(bpy_obj)

                vertices = []
                faces = []
                vertex_indices_list = [0, 2, 1]

                if chunk_id == Chunks.INVALID:
                    for face_index in range(faces_count):
                        face_indices = []
                        for vertex_index in range(3):
                            coord_x, coord_y, coord_z = packed_reader.getf('3f')
                            vertices.append((coord_x, coord_z, coord_y))
                            face_indices.append(
                                face_index * 3 + vertex_indices_list[vertex_index]
                                )
                        faces.append(face_indices)

                elif chunk_id == Chunks.INVALID_EXPORT:
                    for face_index in range(faces_count):
                        face_indices = []
                        for vertex_index in range(3):
                            coord_x, coord_y, coord_z = packed_reader.getf('3f')
                            vertices.append((coord_x, coord_z, coord_y))
                            face_indices.append(
                                face_index * 3 + vertex_indices_list[vertex_index]
                                )
                        c = packed_reader.getf('I')[0]    # ?
                        i = packed_reader.getf('H')[0]    # ?
                        m = packed_reader.getf('H')[0]    # ?
                        faces.append(face_indices)

                bpy_mesh.from_pydata(vertices, (), faces)

            else:
                operator.report(
                    {'WARNING', },
                    'File "{0}" has no invalid faces.'.format(filepath)
                    )


def import_file(filepath, operator):
    with open(filepath, 'rb') as file:
        import_(filepath, ChunkedReader(file.read()), operator)
