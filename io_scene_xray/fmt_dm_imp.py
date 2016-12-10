
import io
import os
import bmesh
from .xray_io import PackedReader


class ImportContext:
    def __init__(self, textures, report, op, bpy=None):
        from . import bl_info
        from .utils import version_to_number
        self.version = version_to_number(*bl_info['version'])
        self.report = report
        self.bpy = bpy
        if textures[-1] != os.sep:
            textures += os.sep
        self.textures_folder = textures
        self.op = op


def _import(fpath, cx, pr, mode='DM'):
    if cx.bpy:
        object_name = os.path.basename(fpath.lower())
        bpy_mesh = cx.bpy.data.meshes.new(object_name)
        bpy_obj = cx.bpy.data.objects.new(object_name, bpy_mesh)
        cx.bpy.context.scene.objects.link(bpy_obj)
        shader = pr.gets()
        texture = pr.gets()
        absoluteImagePath = cx.textures_folder + texture
        uvMapName = 'Texture'
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
                if ts.uv_layer != uvMapName:
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
            bpy_texture = cx.bpy.data.textures.get(texture)
            if bpy_texture:
                if not hasattr(bpy_texture, 'image'):
                    bpy_texture = None
                else:
                    if bpy_texture.image.filepath != absoluteImagePath + '.dds':
                        bpy_texture = None
            if bpy_texture is None:
                bpy_texture = cx.bpy.data.textures.new(texture, type='IMAGE')
                bpy_texture.use_preview_alpha = True
                bpy_texture_slot = bpy_material.texture_slots.add()
                bpy_texture_slot.texture = bpy_texture
                bpy_texture_slot.texture_coords = 'UV'
                bpy_texture_slot.uv_layer = uvMapName
                bpy_texture_slot.use_map_color_diffuse = True
                bpy_texture_slot.use_map_alpha = True
                bpy_image = None
                for bi in cx.bpy.data.images:
                    if absoluteImagePath in bi.filepath:
                        bpy_image = bi
                        break
                if not bpy_image:
                    bpy_image = cx.bpy.data.images.new(os.path.basename(texture), 0, 0)
                    bpy_image.source = 'FILE'
                    bpy_image.filepath = absoluteImagePath + '.dds'
                bpy_texture.image = bpy_image
            else:
                bpy_texture_slot = bpy_material.texture_slots.add()
                bpy_texture_slot.texture = bpy_texture
        bpy_mesh.materials.append(bpy_material)
        flags, minScale, maxScale, vertsCnt, indicesCnt = pr.getf('<IffII')
        bpy_obj.xray.no_waving = bool(flags)
        bpy_obj.xray.min_scale = minScale
        bpy_obj.xray.max_scale = maxScale
        if indicesCnt % 3 != 0:
            raise Exception(' ! bad dm triangle indices')
        bm = bmesh.new()
        S_FFFFF = PackedReader.prep('fffff')    
        uvs = {}
        for _ in range(vertsCnt):
            v = pr.getp(S_FFFFF)    # x, y, z, u, v
            bm_vert = bm.verts.new((v[0], v[2], v[1]))
            uvs[bm_vert] = (v[3], v[4])
        bm.verts.ensure_lookup_table()
        S_HHH = PackedReader.prep('HHH')
        for _ in range(indicesCnt // 3):
            fi = pr.getp(S_HHH)    # face indices
            try:
                bm.faces.new((bm.verts[fi[0]], bm.verts[fi[2]], bm.verts[fi[1]]))
            except ValueError:
                pass
        bm.faces.ensure_lookup_table()
        uvLayer = bm.loops.layers.uv.new(uvMapName)
        if mode == 'DM':
            for face in bm.faces:
                for loop in face.loops:
                    loop[uvLayer].uv = uvs[loop.vert]
        elif mode == 'DETAILS':
            for face in bm.faces:
                for loop in face.loops:
                    uv = uvs[loop.vert]
                    loop[uvLayer].uv = uv[0], 1 - uv[1]
        else:
            raise Exception(' ! unknown dm import mode: {}'.format(mode))
        if not bpy_image:
            bpy_image = bpy_material.texture_slots[0].texture.image
        bml_tex = bm.faces.layers.tex.new(uvMapName)
        for bmf in bm.faces:
            bmf[bml_tex].image = bpy_image
        bm.normal_update()
        bm.to_mesh(bpy_mesh)
        return bpy_obj


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, PackedReader(f.read()))
