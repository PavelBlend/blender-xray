# blender modules
import bpy

# addon modules
from . import name
from .. import fmt
from .... import utils
from .... import rw


def _create_portal_object(portal_index, verts, collection, portals_obj):
    object_name = '{0}_{1:0>3}'.format(name.PORTAL_NAME, portal_index)

    faces = [list(range(len(verts))), ]
    portal_mesh = bpy.data.meshes.new(object_name)
    portal_mesh.from_pydata(verts, (), faces)
    utils.stats.created_msh()

    portal_obj = utils.obj.create_object(object_name, portal_mesh, False)
    portal_obj.parent = portals_obj

    collection.objects.link(portal_obj)
    if not utils.version.IS_28:
        utils.version.link_object(portal_obj)

    return portal_obj


def _import_portal(reader, index, collection, level, portals_obj):
    sector_front, sector_back = reader.getf('<2H')

    # read vertices
    if level.xrlc_version <= fmt.VERSION_5:
        used_verts_count = reader.uint32()

    verts = []
    for _ in range(fmt.PORTAL_VERTEX_COUNT):
        coord = reader.getv3f()
        verts.append(coord)

    if level.xrlc_version >= fmt.VERSION_8:
        used_verts_count = reader.uint32()

    verts = verts[ : used_verts_count]

    # create object
    portal_obj = _create_portal_object(index, verts, collection, portals_obj)

    # set props
    xray = portal_obj.xray
    xray.version = level.addon_version
    xray.isroot = False
    xray.is_level = True
    xray.level.object_type = 'PORTAL'
    xray.level.sector_front = level.sectors_objects[sector_front].name
    xray.level.sector_back = level.sectors_objects[sector_back].name

    return portal_obj


def _create_portals_object(level_object, collection):
    portals_obj = utils.obj.create_object(name.PORTAL_NAME + 's', None, False)
    portals_obj.parent = level_object
    level_object.xray.level.portals_obj = portals_obj.name

    collection.objects.link(portals_obj)
    if not utils.version.IS_28:
        utils.version.link_object(portals_obj)

    return portals_obj


def import_portals(level, level_object, chunks, chunks_ids):
    data = chunks.pop(chunks_ids.PORTALS)
    reader = rw.read.PackedReader(data)
    collection = level.collections[name.LEVEL_PORTALS_COLLECTION_NAME]

    # create portals root-object
    portals_obj = _create_portals_object(level_object, collection)

    # import portals
    portals_count = len(data) // fmt.PORTAL_SIZE

    for index in range(portals_count):
        _import_portal(reader, index, collection, level, portals_obj)
