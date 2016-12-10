
import io
import bpy
import bmesh
import mathutils
from .utils import convert_object_to_space_bmesh, AppError, gen_texture_name
from .xray_io import PackedWriter


def _export(bpy_obj, pw, cx):
    if not len(bpy_obj.data.uv_layers):
        raise AppError('UV-map is required, but not found')
    material_count = len(bpy_obj.material_slots)
    if material_count == 0:
        raise AppError('mesh "' + bpy_obj.data.name + '" has no material')
    elif material_count > 1:
        raise AppError('mesh "' + bpy_obj.data.name + '" has more than one material')
    else:
        bpy_material = bpy_obj.material_slots[0].material
        if not bpy_material:
            raise AppError('mesh "' + bpy_obj.data.name + '" has empty material slot')
    bpy_texture = None
    for ts in bpy_material.texture_slots:
        if ts:
            bpy_texture = ts.texture
            if bpy_texture:
                break
    if bpy_texture:
        if bpy_texture.type == 'IMAGE':
            if not bpy_texture.image:
                raise AppError('texture "' + bpy_texture.name + '" has no image')
            if cx.texname_from_path:
                tx_name = gen_texture_name(bpy_texture, cx.textures_folder)
            else:
                tx_name = bpy_texture.name
        else:
            raise AppError('texture "' + bpy_texture.name + '" has an incorrect type: ' + bpy_texture.type)
    else:
        raise AppError('material "' + bpy_material.name + '" has no texture')
    pw.puts(bpy_material.xray.eshader)
    pw.puts(tx_name)
    pw.putf('<I', int(bpy_obj.xray.no_waving))
    pw.putf('<ff', bpy_obj.xray.min_scale, bpy_obj.xray.max_scale)
    bm = convert_object_to_space_bmesh(bpy_obj, mathutils.Matrix.Identity(4))
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bpy_data = bpy.data.meshes.new('.export-dm')
    bm.to_mesh(bpy_data)
    bml_uv = bm.loops.layers.uv.active
    vertices = []
    indices = []
    vmap = {}
    for f in bm.faces:
        ii = []
        for li, l in enumerate(f.loops):
            dl = bpy_data.loops[f.index * 3 + li]
            uv = l[bml_uv].uv
            vtx = (l.vert.co.to_tuple(), (uv[0], uv[1]))
            vi = vmap.get(vtx)
            if vi is None:
                vmap[vtx] = vi = len(vertices)
                vertices.append(vtx)
            ii.append(vi)
        indices.append(ii)
    pw.putf('<I', len(vertices))
    pw.putf('<I', len(indices) * 3)
    for vtx in vertices:
        pw.putf('<fffff', vtx[0][0], vtx[0][2], vtx[0][1], vtx[1][0], vtx[1][1])
    for tris in indices:
        pw.putf('<HHH', tris[0], tris[2], tris[1])
    bpy.data.meshes.remove(bpy_data)


def export_file(bpy_obj, fpath, cx):
    with io.open(fpath, 'wb') as f:
        pw = PackedWriter()
        _export(bpy_obj, pw, cx)
        f.write(pw.data)
