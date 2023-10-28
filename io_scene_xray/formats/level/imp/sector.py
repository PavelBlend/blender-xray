# addon modules
from . import create
from .. import fmt
from .... import rw
from .... import utils


SECTOR_OBJECT_NAME = 'sector'
SECTORS_OBJECT_NAME = 'sectors'


def _create_sector_object(sector_id, collection, sectors_object):
    object_name = '{0}_{1:0>3}'.format(SECTOR_OBJECT_NAME, sector_id)
    sector_object = create.create_object(object_name, None)
    sector_object.parent = sectors_object
    collection.objects.link(sector_object)

    if not utils.version.IS_28:
        utils.version.link_object(sector_object)

    return sector_object


def _create_sectors_object(collection, level_object):
    sectors_object = create.create_object(SECTORS_OBJECT_NAME, None)
    sectors_object.parent = level_object
    level_object.xray.level.sectors_obj = sectors_object.name
    collection.objects.link(sectors_object)

    if not utils.version.IS_28:
        utils.version.link_object(sectors_object)

    return sectors_object


def _read_sector(data, level, sector_object):
    chunked_reader = rw.read.ChunkedReader(data)

    for chunk_id, chunk_data in chunked_reader:

        if chunk_id == fmt.SectorChunks.ROOT:
            packed_reader = rw.read.PackedReader(chunk_data)
            root_visual = packed_reader.uint32()
            level.visuals[root_visual].parent = sector_object


def import_sectors(data, level, level_object):
    chunked_reader = rw.read.ChunkedReader(data)

    # create sectors root-object
    collection = level.collections[create.LEVEL_SECTORS_COLLECTION_NAME]
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
