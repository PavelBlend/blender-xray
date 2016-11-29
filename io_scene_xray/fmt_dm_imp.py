
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
        self.textures_folder = textures
        self.op = op
        self.used_materials = None

    def before_import_file(self):
        self.used_materials = {}


def _import(fpath, cx, pr):
    if cx.bpy:
        object_name = os.path.basename(fpath.lower())
        bpy_mesh = cx.bpy.data.meshes.new(object_name)
        bpy_obj = cx.bpy.data.objects.new(object_name, bpy_mesh)
        cx.bpy.context.scene.objects.link(bpy_obj)
        shader = pr.gets()
        texture = pr.gets()
        flags, minScale, maxScale, vertsCnt, indicesCnt = pr.getf('<IffII')
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
            bm.faces.new((bm.verts[fi[0]], bm.verts[fi[2]], bm.verts[fi[1]]))
        bm.faces.ensure_lookup_table()
        uvLayer = bm.loops.layers.uv.new('texture')
        for face in bm.faces:
            for loop in face.loops:
                loop[uvLayer].uv = uvs[loop.vert]
        bm.normal_update()
        bm.to_mesh(bpy_mesh)


def import_file(fpath, cx):
    with io.open(fpath, 'rb') as f:
        _import(fpath, cx, PackedReader(f.read()))
