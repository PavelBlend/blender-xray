# blender modules
import bpy

# addon modules
from .. import fmt
from .... import rw
from .... import log
from .... import utils
from .... import text


class DiscardedWeights:
    def __init__(self):
        self.obj_name = None
        self.verts = set()
        self.max_weights_count = None


def _select_verts_by_discarded_weights(ctx, bpy_obj, dis_wghts):

    bpy.ops.object.select_all(action='DESELECT')

    if dis_wghts.verts:

        utils.version.set_active_object(bpy_obj)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy_mesh = bpy_obj.data

        vert_sel = [False, ] * len(bpy_mesh.vertices)
        for vert_index in dis_wghts.verts:
            vert_sel[vert_index] = True

        utils.version.set_vert_sel(bpy_mesh, vert_sel)

        log.warn(
            text.warn.ogf_discarded_weights,
            object_name=bpy_obj.name,
            vertices_count=len(dis_wghts.verts),
            weights_count_max=dis_wghts.max_weights_count,
            weights_count_limit=2 if ctx.fmt_ver=='soc' else 4
        )


def write_verts_static(vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        vertices_writer.putv3f(vertex[1])    # coord
        vertices_writer.putv3f((
            norm_coef * vertex[2][0],
            norm_coef * vertex[2][1],
            norm_coef * vertex[2][2]
        ))    # normal
        vertices_writer.putf('<2f', *vertex[5])    # uv


def write_verts_1l(vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        vertices_writer.putv3f(vertex[1])    # coord
        vertices_writer.putv3f((
            norm_coef * vertex[2][0],
            norm_coef * vertex[2][1],
            norm_coef * vertex[2][2]
        ))    # normal
        vertices_writer.putv3f(vertex[3])    # tangent
        vertices_writer.putv3f(vertex[4])    # bitangent
        vertices_writer.putf('<2f', *vertex[5])    # uv
        vertices_writer.putf('<I', vertex[6][0][0])    # bone


def write_verts_2l(dis_wghts, vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        weights = vertex[6]

        if len(weights) > 2:
            weights = utils.mesh.weights_top(dis_wghts, weights, 2)

        weight = 0

        # 2-link vertex
        if len(weights) == 2:
            first = True
            weight0 = 0
            for vgi, vert_weight, _ in weights:
                vertices_writer.putf('<H', vgi)
                if first:
                    weight0 = vert_weight
                    first = False
                else:
                    weight = 1 - (weight0 / (weight0 + vert_weight))

        # 1-link vertex
        elif len(weights) == 1:
            vertices_writer.putf(
                '<2H',
                weights[0][0],
                weights[0][0]
            )
        else:
            raise Exception('oops: {} {}'.format(
                len(weights),
                weights.keys()
            ))

        # write vertex data
        vertices_writer.putv3f(vertex[1])    # coord
        vertices_writer.putv3f((
            norm_coef * vertex[2][0],
            norm_coef * vertex[2][1],
            norm_coef * vertex[2][2]
        ))    # normal
        vertices_writer.putv3f(vertex[3])    # tangent
        vertices_writer.putv3f(vertex[4])    # bitangent
        vertices_writer.putf('<f', weight)    # weight
        vertices_writer.putf('<2f', *vertex[5])    # uv


def write_verts_3l(dis_wghts, vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        weights = vertex[6]

        if len(weights) > 3:
            weights = utils.mesh.weights_top(dis_wghts, weights, 3)

        # 3-link vertex
        if len(weights) == 3:
            group_1 = weights[0][0]
            group_2 = weights[1][0]
            group_3 = weights[2][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]
            weight_3 = weights[2][1]

            weight_sum = weight_1 + weight_2 + weight_3

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum

            vertices_writer.putf('<3H', group_1, group_2, group_3)

        # 2-link vertex
        elif len(weights) == 2:
            group_1 = weights[0][0]
            group_2 = weights[1][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]

            weight_sum = weight_1 + weight_2

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum

            vertices_writer.putf('<3H', group_1, group_2, group_1)

        # 1-link vertex
        elif len(weights) == 1:
            group_1 = weights[0][0]

            weight_1_norm = 1.0
            weight_2_norm = 0.0

            vertices_writer.putf('<3H', group_1, group_1, group_1)

        else:
            raise Exception('oops: {} {}'.format(
                len(weights),
                weights.keys()
            ))

        # write vertex data
        vertices_writer.putv3f(vertex[1])    # coord
        vertices_writer.putv3f((
            norm_coef * vertex[2][0],
            norm_coef * vertex[2][1],
            norm_coef * vertex[2][2]
        ))    # normal
        vertices_writer.putv3f(vertex[3])    # tangent
        vertices_writer.putv3f(vertex[4])    # bitangent
        vertices_writer.putf('<2f', weight_1_norm, weight_2_norm)    # weights
        vertices_writer.putf('<2f', *vertex[5])    # uv


def write_verts_4l(dis_wghts, vertices_writer, vertices, norm_coef=1):
    for vertex in vertices:
        weights = vertex[6]

        if len(weights) > 4:
            weights = utils.mesh.weights_top(dis_wghts, weights, 4)

        # 4-link vertex
        if len(weights) == 4:
            group_1 = weights[0][0]
            group_2 = weights[1][0]
            group_3 = weights[2][0]
            group_4 = weights[3][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]
            weight_3 = weights[2][1]
            weight_4 = weights[3][1]

            weight_sum = weight_1 + weight_2 + weight_3 + weight_4

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum
            weight_3_norm = weight_3 / weight_sum

            vertices_writer.putf('<4H', group_1, group_2, group_3, group_4)

        # 3-link vertex
        elif len(weights) == 3:
            group_1 = weights[0][0]
            group_2 = weights[1][0]
            group_3 = weights[2][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]
            weight_3 = weights[2][1]

            weight_sum = weight_1 + weight_2 + weight_3

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum
            weight_3_norm = weight_3 / weight_sum

            vertices_writer.putf('<4H', group_1, group_2, group_3, group_1)

        # 2-link vertex
        elif len(weights) == 2:
            group_1 = weights[0][0]
            group_2 = weights[1][0]

            weight_1 = weights[0][1]
            weight_2 = weights[1][1]

            weight_sum = weight_1 + weight_2

            # normalize
            weight_1_norm = weight_1 / weight_sum
            weight_2_norm = weight_2 / weight_sum
            weight_3_norm = 0.0

            vertices_writer.putf('<4H', group_1, group_2, group_1, group_1)

        # 1-link vertex
        elif len(weights) == 1:
            group_1 = weights[0][0]

            weight_1_norm = 1.0
            weight_2_norm = 0.0
            weight_3_norm = 0.0

            vertices_writer.putf('<4H', group_1, group_1, group_1, group_1)

        else:
            raise Exception('oops: {} {}'.format(
                len(weights),
                weights.keys()
            ))

        # write vertex data
        vertices_writer.putv3f(vertex[1])    # coord
        vertices_writer.putv3f((
            norm_coef * vertex[2][0],
            norm_coef * vertex[2][1],
            norm_coef * vertex[2][2]
        ))    # normal
        vertices_writer.putv3f(vertex[3])    # tangent
        vertices_writer.putv3f(vertex[4])    # bitangent
        # weights
        vertices_writer.putf(
            '<3f',
            weight_1_norm,
            weight_2_norm,
            weight_3_norm
        )
        vertices_writer.putf('<2f', *vertex[5])    # uv


def write_verts(
        ctx,
        bpy_obj,
        vertices,
        two_sided,
        vertex_max_weights,
        chunked_writer
    ):

    vertices_writer = rw.write.PackedWriter()
    verts_count = len(vertices)
    if two_sided:
        verts_count *= 2

    if verts_count > fmt.VERTS_COUNT_LIMIT:
        raise log.AppError(
            text.error.ogf_verts_count_limit,
            log.props(
                object=bpy_obj.name,
                vertices_count=verts_count,
                vertices_count_limit=fmt.VERTS_COUNT_LIMIT
            )
        )

    dis_wghts = DiscardedWeights()
    dis_wghts.max_weights_count = vertex_max_weights

    # static vertices
    if not vertex_max_weights:
        vert_fmt = fmt.VertexFormat.FVF_OGF
        vertices_writer.putf('<2I', vert_fmt, verts_count)
        write_verts_static(vertices_writer, vertices)

        if two_sided:
            write_verts_static(vertices_writer, vertices, norm_coef=-1)

    # 1-link vertices
    elif vertex_max_weights == 1:
        if ctx.fmt_ver == 'soc':
            vert_fmt = fmt.VertexFormat.FVF_1L
        else:
            vert_fmt = fmt.VertexFormat.FVF_1L_CS

        vertices_writer.putf('<2I', vert_fmt, verts_count)
        write_verts_1l(vertices_writer, vertices)

        if two_sided:
            write_verts_1l(vertices_writer, vertices, norm_coef=-1)

    # 2-link vertices
    elif vertex_max_weights == 2 or ctx.fmt_ver == 'soc':
        if ctx.fmt_ver == 'soc':
            vert_fmt = fmt.VertexFormat.FVF_2L
        else:
            vert_fmt = fmt.VertexFormat.FVF_2L_CS

        vertices_writer.putf('<2I', vert_fmt, verts_count)
        write_verts_2l(dis_wghts, vertices_writer, vertices)

        if two_sided:
            write_verts_2l(dis_wghts, vertices_writer, vertices, norm_coef=-1)

    # 3-link vertices
    elif vertex_max_weights == 3:
        vert_fmt = fmt.VertexFormat.FVF_3L_CS

        vertices_writer.putf('<2I', vert_fmt, verts_count)
        write_verts_3l(dis_wghts, vertices_writer, vertices)

        if two_sided:
            write_verts_3l(dis_wghts, vertices_writer, vertices, norm_coef=-1)

    # 4-link vertices
    else:
        vert_fmt = fmt.VertexFormat.FVF_4L_CS

        vertices_writer.putf('<2I', vert_fmt, verts_count)
        write_verts_4l(dis_wghts, vertices_writer, vertices)

        if two_sided:
            write_verts_4l(dis_wghts, vertices_writer, vertices, norm_coef=-1)

    chunked_writer.put(fmt.Chunks_v4.VERTICES, vertices_writer)

    _select_verts_by_discarded_weights(ctx, bpy_obj, dis_wghts)

    return verts_count
