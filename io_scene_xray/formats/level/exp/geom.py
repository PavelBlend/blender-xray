# standart modules
import os

# addon modules
from . import header
from .. import fmt
from .... import rw


def _write_geom_swis(geom_writer):
    swis_writer = rw.write.PackedWriter()
    swis_writer.putf('<I', 0)    # swis count
    geom_writer.put(fmt.Chunks13.SWIS, swis_writer)


def _write_geom_ibs(geom_writer, ibs):
    ib_writer = rw.write.PackedWriter()

    buffers_count = len(ibs)
    ib_writer.putf('<I', buffers_count)

    for ib in ibs:
        indices_count = len(ib) // fmt.INDEX_SIZE
        ib_writer.putf('<I', indices_count)
        ib_writer.data.extend(ib)

    geom_writer.put(fmt.Chunks13.IB, ib_writer)


def _write_geom_vbs(geom_writer, vbs):
    vbs_writer = rw.write.PackedWriter()

    buffers_count = len(vbs)
    vbs_writer.putf('<I', buffers_count)

    for vb in vbs:

        if vb.vertex_format == 'NORMAL':
            offsets = (0, 12, 16, 20, 24, 28)    # vertex buffer offsets
            usage_indices = (0, 0, 0, 0, 0, 1)
            vertex_type = fmt.VERTEX_TYPE_BRUSH_14

        elif vb.vertex_format == 'TREE':
            offsets = (0, 12, 16, 20, 24)
            usage_indices = (0, 0, 0, 0, 0)
            vertex_type = fmt.VERTEX_TYPE_TREE

        elif vb.vertex_format == 'COLOR':
            offsets = (0, 12, 16, 20, 24, 28)
            usage_indices = (0, 0, 0, 0, 0, 0)
            vertex_type = fmt.VERTEX_TYPE_COLOR_14

        elif vb.vertex_format == 'FASTPATH':
            offsets = (0, )
            usage_indices = (0, )
            vertex_type = fmt.VERTEX_TYPE_FASTPATH

        else:
            raise BaseException('Unknown VB format:', vb.vertex_format)

        # write buffer header
        for index, (usage, value_type) in enumerate(vertex_type):
            vbs_writer.putf('<H', 0)    # stream
            vbs_writer.putf('<H', offsets[index])    # offset
            vbs_writer.putf('<B', value_type)    # type
            vbs_writer.putf('<B', 0)    # method
            vbs_writer.putf('<B', usage)    # usage
            vbs_writer.putf('<B', usage_indices[index])    # usage_index

        vbs_writer.putf('<H', 255)    # stream
        vbs_writer.putf('<H', 0)    # offset
        vbs_writer.putf('<B', fmt.types_values[fmt.UNUSED])    # type UNUSED
        vbs_writer.putf('<B', 0)    # method
        vbs_writer.putf('<B', 0)    # usage
        vbs_writer.putf('<B', 0)    # usage_index

        vbs_writer.putf('<I', vb.vertex_count)    # vertices count

        # write vertices
        if vb.vertex_format == 'NORMAL':
            for index in range(vb.vertex_count):
                vbs_writer.data.extend(vb.position[index*12 : index*12 + 12])
                vbs_writer.data.extend((
                    *vb.normal[index*3 : index*3 + 3],
                    vb.color_hemi[index]
                ))    # normal, hemi
                uv_fix = vb.uv_fix[index*2 : index*2 + 2]
                # tangent
                vbs_writer.data.extend((
                    *vb.tangent[index*3 : index*3 + 3],
                    uv_fix[0]
                ))
                # binormal
                vbs_writer.data.extend((
                    *vb.binormal[index*3 : index*3 + 3],
                    uv_fix[1]
                ))
                # texture coordinate
                vbs_writer.data.extend(vb.uv[index*4 : index*4 + 4])
                # light map texture coordinate
                vbs_writer.data.extend(vb.uv_lmap[index*4 : index*4 + 4])

        elif vb.vertex_format == 'TREE':
            for index in range(vb.vertex_count):
                vbs_writer.data.extend(vb.position[index*12 : index*12 + 12])
                vbs_writer.data.extend((
                    *vb.normal[index*3 : index*3 + 3],
                    vb.color_hemi[index]
                ))    # normal, hemi
                uv_fix = vb.uv_fix[index*2 : index*2 + 2]
                # tangent
                vbs_writer.data.extend((
                    *vb.tangent[index*3 : index*3 + 3],
                    uv_fix[0]
                ))
                # binormal
                vbs_writer.data.extend((
                    *vb.binormal[index*3 : index*3 + 3],
                    uv_fix[1]
                ))
                # texture coordinate
                vbs_writer.data.extend(vb.uv[index*4 : index*4 + 4])
                # tree shader data (wind coefficient and unused 2 bytes)
                frac = vb.shader_data[index*2 : index*2 + 2]
                frac.extend((0, 0))
                vbs_writer.data.extend(frac)

        elif vb.vertex_format == 'COLOR':
            for index in range(vb.vertex_count):
                vbs_writer.data.extend(vb.position[index*12 : index*12 + 12])
                vbs_writer.data.extend((
                    *vb.normal[index*3 : index*3 + 3],
                    vb.color_hemi[index]
                ))    # normal, hemi
                uv_fix = vb.uv_fix[index*2 : index*2 + 2]
                # tangent
                vbs_writer.data.extend((
                    *vb.tangent[index*3 : index*3 + 3],
                    uv_fix[0]
                ))
                # binormal
                vbs_writer.data.extend((
                    *vb.binormal[index*3 : index*3 + 3],
                    uv_fix[1]
                ))
                # vertex color
                vbs_writer.data.extend((
                    *vb.color_light[index*3 : index*3 + 3],
                    vb.color_sun[index]
                ))
                # texture coordinate
                vbs_writer.data.extend(vb.uv[index*4 : index*4 + 4])

        elif vb.vertex_format == 'FASTPATH':
            vbs_writer.data.extend(vb.position)

    geom_writer.put(fmt.Chunks13.VB, vbs_writer)


def write_geom(file_path, vbs, ibs, ext):
    # level.geom/level.geomx chunked writer
    geom_writer = rw.write.ChunkedWriter()

    # header
    header.write_header(geom_writer)

    # vertex buffers
    _write_geom_vbs(geom_writer, vbs)

    # index buffers
    _write_geom_ibs(geom_writer, ibs)

    # slide window items
    _write_geom_swis(geom_writer)

    # save level.geom/level.geomx file
    geom_path = file_path + os.extsep + ext
    rw.utils.save_file(geom_path, geom_writer)
