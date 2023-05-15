# blender modules
import bpy

# addon modules
from .. import fmt
from .... import rw


def _append_portal(sectors_portals, sector_index, portal_index):
    sectors_portals.setdefault(sector_index, []).append(portal_index)


def get_sectors_portals(level, level_object):
    sectors_portals = {}

    for obj_name in level.visuals_cache.children[level_object.name]:
        obj = bpy.data.objects[obj_name]
        if obj.name.startswith('portals'):
            portal_objs = level.visuals_cache.children[obj.name]

            for portal_index, portal_name in enumerate(portal_objs):
                portal_obj = bpy.data.objects[portal_name]

                _append_portal(
                    sectors_portals,
                    portal_obj.xray.level.sector_front,
                    portal_index
                )
                _append_portal(
                    sectors_portals,
                    portal_obj.xray.level.sector_back,
                    portal_index
                )

    return sectors_portals


def _write_sector_root(sector_writer, root_index):
    root_writer = rw.write.PackedWriter()
    root_writer.putf('<I', root_index)
    sector_writer.put(fmt.SectorChunks.ROOT, root_writer)


def _write_sector_portals(sector_writer, sectors_portals, sector_name):
    portals_writer = rw.write.PackedWriter()

    # None - when there are no sectors
    portals = sectors_portals.get(sector_name, None)
    if portals:
        for portal_index in portals:
            portals_writer.putf('<H', portal_index)

    sector_writer.put(fmt.SectorChunks.PORTALS, portals_writer)


def write_sector(root_index, sectors_portals, sector_name):
    sector_writer = rw.write.ChunkedWriter()

    # write portals
    _write_sector_portals(sector_writer, sectors_portals, sector_name)

    # write root-visual
    _write_sector_root(sector_writer, root_index)

    return sector_writer
