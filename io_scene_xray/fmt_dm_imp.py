
import io
import os
import bmesh
from .utils import AppError
from .xray_io import PackedReader


def _import(fpath, cx, pr, mode='DM'):
    if cx.bpy:
        object_name = os.path.basename(fpath.lower())
        bpy_mesh = cx.bpy.data.meshes.new(object_name)
        bpy_obj = cx.bpy.data.objects.new(object_name, bpy_mesh)
        cx.bpy.context.scene.objects.link(bpy_obj)
        shader = pr.gets()
        texture = pr.gets()
        abs_image_path = os.path.abspath(os.path.join(cx.textures_folder, texture + '.dds'))
        uv_map_name = 'Texture'
        bpy_material = None
        bpy_image = None
        bpy_texture = None
        for bm in cx.bpy.data.materials:
            if not bm.name.startswith(texture):
                continue
            if bm.xray.eshader != shader:
                continue
            tx_filepart = texture.replace('\\', os.path.sep)
            ts_found = False
            for ts in bm.texture_slots:
                if not ts:
                    continue
                if ts.uv_layer != uv_map_name:
                    continue
                if not hasattr(ts.texture, 'image'):
                    continue
                if not tx_filepart in ts.texture.image.filepath:
                    continue
                ts_found = True
                break
            if not ts_found:
                continue
            bpy_material = bm
            break
        if not bpy_material:
            bpy_material = cx.bpy.data.materials.new(texture)
            bpy_material.xray.eshader = shader
            bpy_material.use_shadeless = True
            bpy_material.use_transparency = True
            bpy_material.alpha = 0.0
            bpy_texture = cx.bpy.data.textures.get(texture)
            if bpy_texture:
                if not hasattr(bpy_texture, 'image'):
                    bpy_texture = None
                else:
                    if bpy_texture.image.filepath != abs_image_path:
                        bpy_texture = None
            if bpy_texture is None:
                bpy_texture = cx.bpy.data.textures.new(texture, type='IMAGE')
                bpy_texture.use_preview_alpha = True
                bpy_texture_slot = bpy_material.texture_slots.add()
                bpy_texture_slot.texture = bpy_texture
                bpy_texture_slot.texture_coords = 'UV'
                bpy_texture_slot.uv_layer = uv_map_name
                bpy_texture_slot.use_map_color_diffuse = True
                bpy_texture_slot.use_map_alpha = True
                bpy_image = None
                for bi in cx.bpy.data.images:
                    if abs_image_path == bi.filepath:
                        bpy_image = bi
                        break
                if not bpy_image:
                    bpy_image = cx.bpy.data.images.new(
                        os.path.basename(texture), 0, 0
                        )
                    bpy_image.source = 'FILE'
                    if not cx.textures_folder:
                        bpy_image.filepath = texture + '.dds'
                    else:
                        bpy_image.filepath = abs_image_path
                    bpy_image.use_alpha = True
                bpy_texture.image = bpy_image
            else:
                bpy_texture_slot = bpy_material.texture_slots.add()
                bpy_texture_slot.texture = bpy_texture
        bpy_mesh.materials.append(bpy_material)
        flags, min_scale, max_scale, verts_cnt, indices_cnt = pr.getf('<IffII')
        bpy_obj.xray.no_waving = bool(flags)
        bpy_obj.xray.min_scale = min_scale
        bpy_obj.xray.max_scale = max_scale
        if indices_cnt % 3 != 0:
            raise AppError('bad dm triangle indices')
        bm = bmesh.new()
        S_FFFFF = PackedReader.prep('fffff')    
        uvs = {}
        for _ in range(verts_cnt):
            v = pr.getp(S_FFFFF)    # x, y, z, u, v
            bm_vert = bm.verts.new((v[0], v[2], v[1]))
            uvs[bm_vert] = (v[3], v[4])
        bm.verts.ensure_lookup_table()
        S_HHH = PackedReader.prep('HHH')
        for _ in range(indices_cnt // 3):
            fi = pr.getp(S_HHH)    # face indices
            try:
                bm.faces.new(
                    (bm.verts[fi[0]], bm.verts[fi[2]], bm.verts[fi[1]])
                    )
            except ValueError:
                pass
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.new(uv_map_name)
        if mode == 'DM':
            for face in bm.faces:
                for loop in face.loops:
                    loop[uv_layer].uv = uvs[loop.vert]
        elif mode == 'DETAILS':
            for face in bm.faces:
                for loop in face.loops:
                    uv = uvs[loop.vert]
                    loop[uv_layer].uv = uv[0], 1 - uv[1]
        else:
            raise Exception(
                'unknown dm import mode: {0}. ' \
                'You must use DM or DETAILS'.format(mode)
                )
        if not bpy_image:
            bpy_image = bpy_material.texture_slots[0].texture.image
        bml_tex = bm.faces.layers.tex.new(uv_map_name)
        for bmf in bm.faces:
            bmf[bml_tex].image = bpy_image
        bm.normal_update()
        bm.to_mesh(bpy_mesh)
        return bpy_obj


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, PackedReader(f.read()))
