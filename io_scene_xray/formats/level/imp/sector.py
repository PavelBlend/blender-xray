# addon modules
from . import name
from .. import fmt
from .... import rw
from .... import utils


def _create_sector_object(sector_id, collection, sectors_object):
    object_name = '{0}_{1:0>3}'.format(name.SECTOR_NAME, sector_id)
    sector_object = utils.obj.create_object(object_name, None, False)
    sector_object.parent = sectors_object
    collection.objects.link(sector_object)

    if not utils.version.IS_28:
        utils.version.link_object(sector_object)

    return sector_object


def _create_sectors_object(collection, level_object):
    sectors_obj = utils.obj.create_object(name.SECTOR_NAME + 's', None, False)
    sectors_obj.parent = level_object
    level_object.xray.level.sectors_obj = sectors_obj.name
    collection.objects.link(sectors_obj)

    if not utils.version.IS_28:
        utils.version.link_object(sectors_obj)

    return sectors_obj


def _read_sector(data, level, sector_object):
    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:

        if chunk_id == fmt.SectorChunks.ROOT:
            packed_reader = rw.read.PackedReader(chunk_data)
            root_visual = packed_reader.uint32()
            level.visuals[root_visual].parent = sector_object


def import_sectors(level, level_object, chunks, chunks_ids):
    data = chunks.pop(chunks_ids.SECTORS)
    chunked_reader = rw.read.ChunkedReader(data)

    # create sectors root-object
    collection = level.collections[name.LEVEL_SECTORS_COLLECTION_NAME]
    sectors_object = _create_sectors_object(collection, level_object)

    for sector_id, sector_data in chunked_reader:
        # create sector object
        sector_object = _create_sector_object(
            sector_id,
            collection,
            sectors_object
        )
        level.sectors_objects[sector_id] = sector_object
        _read_sector(sector_data, level, sector_object)
