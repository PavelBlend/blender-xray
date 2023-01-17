# addon modules
from .. import fmt
from .... import log
from .... import text
from .... import rw


def read_bbox_v3(data):
    packed_reader = rw.read.PackedReader(data)

    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')


def read_bsphere_v3(data):
    packed_reader = rw.read.PackedReader(data)

    center = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]


def import_bounding_sphere(packed_reader):
    center = packed_reader.getf('<3f')
    radius = packed_reader.getf('<f')[0]


def import_bounding_box(packed_reader):
    bbox_min = packed_reader.getf('<3f')
    bbox_max = packed_reader.getf('<3f')


def import_header(chunks, visual, supported):
    data = chunks.pop(fmt.HEADER)
    packed_reader = rw.read.PackedReader(data)
    visual.format_version = packed_reader.getf('<B')[0]

    if visual.format_version in supported:

        visual.model_type = packed_reader.getf('<B')[0]
        visual.shader_id = packed_reader.getf('<H')[0]

        if visual.format_version == fmt.FORMAT_VERSION_4:
            import_bounding_box(packed_reader)
            import_bounding_sphere(packed_reader)

        elif visual.format_version == fmt.FORMAT_VERSION_3:
            bbox_data = chunks.pop(fmt.Chunks_v3.BBOX, None)
            if bbox_data:
                packed_reader = rw.read.PackedReader(bbox_data)
                import_bounding_box(packed_reader)

            bsphere_data = chunks.pop(fmt.Chunks_v3.BSPHERE, None)
            if bsphere_data:
                packed_reader = rw.read.PackedReader(bsphere_data)
                import_bounding_sphere(packed_reader)

    else:
        raise log.AppError(
            text.error.ogf_bad_ver,
            log.props(version=visual.format_version)
        )


def read_ogf_level_header(chunks, visual):
    import_header(chunks, visual, fmt.SUPPORT_LEVEL_FORMAT_VERSIONS)


def read_ogf_file_header(chunks, visual):
    import_header(chunks, visual, fmt.SUPPORT_FILE_FORMAT_VERSIONS)
