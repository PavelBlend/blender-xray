# blender modules
import bpy

# addon modules
from .. import fmt
from .... import text
from .... import log
from .... import rw


def write_portals(level_writer, level, level_object):
    portals_writer = rw.write.PackedWriter()

    for child_name in level.visuals_cache.children[level_object.name]:
        child_obj = bpy.data.objects[child_name]

        if child_obj.name.startswith('portals'):
            portals_objs = level.visuals_cache.children[child_obj.name]

            for portal_index, portal_name in enumerate(portals_objs):
                portal_obj = bpy.data.objects[portal_name]
                xray = portal_obj.xray

                if xray.level.object_type != 'PORTAL':
                    continue

                if portal_obj.type != 'MESH':
                    raise log.AppError(
                        text.error.level_portal_is_no_mesh,
                        log.props(
                            portal_object=portal_obj.name,
                            object_type=portal_obj.type
                        )
                    )

                portal_mesh = portal_obj.data
                verts_count = len(portal_mesh.vertices)
                faces_count = len(portal_mesh.polygons)
                error_message = None

                # check vertices
                if not verts_count:
                    error_message = text.error.level_portal_no_vert
                elif verts_count < 3:
                    error_message = text.error.level_portal_bad
                elif verts_count > 6:
                    error_message = text.error.level_portal_many_verts

                if error_message:
                    raise log.AppError(
                        error_message,
                        log.props(
                            portal_object=portal_obj.name,
                            vertices_count=verts_count
                        )
                    )

                # check polygons
                if not faces_count:
                    error_message = text.error.level_portal_no_faces
                elif faces_count > 1:
                    error_message = text.error.level_portal_many_faces

                if error_message:
                    raise log.AppError(
                        error_message,
                        log.props(
                            portal_object=portal_obj.name,
                            polygons_count=faces_count
                        )
                    )

                # write portal sectors
                if xray.level.sector_front:
                    sect_front = level.sectors_indices[xray.level.sector_front]
                else:
                    raise log.AppError(
                        text.error.level_portal_no_front,
                        log.props(portal_object=portal_obj.name)
                    )

                if xray.level.sector_back:
                    sect_back = level.sectors_indices[xray.level.sector_back]
                else:
                    raise log.AppError(
                        text.error.level_portal_no_back,
                        log.props(portal_object=portal_obj.name)
                    )

                portals_writer.putf('<2H', sect_front, sect_back)

                # write vertices
                for vert_index in portal_mesh.polygons[0].vertices:
                    vert = portal_mesh.vertices[vert_index]
                    portals_writer.putf('<3f', vert.co.x, vert.co.z, vert.co.y)

                # write not used vertices
                verts_count = len(portal_mesh.vertices)
                for vert_index in range(verts_count, fmt.PORTAL_VERTEX_COUNT):
                    portals_writer.putf('<3f', 0.0, 0.0, 0.0)

                portals_writer.putf('<I', verts_count)

    level_writer.put(fmt.Chunks13.PORTALS, portals_writer)
