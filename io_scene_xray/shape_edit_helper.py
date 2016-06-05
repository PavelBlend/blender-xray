import bpy
import bmesh
import math
import mathutils
from . import utils

__HELPER_NAME = utils.HELPER_OBJECT_NAME_PREFIX + 'bone-shape-edit'


def _helper():
    hobj = bpy.data.objects.get(__HELPER_NAME)
    if hobj is None:
        return
    sp = hobj.xray.helper_data.split('/')
    if len(sp) != 2:
        return
    arm = bpy.data.armatures.get(sp[0], None)
    if arm is None:
        return
    bone = arm.bones.get(sp[1], None)
    if bone is None:
        return
    return hobj, bone


def is_active():
    h = _helper()
    if h is None:
        return False
    b = bpy.context.active_bone
    if b is None:
        return False
    return (h[1].name == b.name) and (h[1].id_data == b.id_data)


def _apply_type(mesh, xt):
    bm = bmesh.new()
    if xt == '1':
        bmesh.ops.create_cube(bm, size=2)
    elif xt == '2':
        bmesh.ops.create_icosphere(bm, subdivisions=2, diameter=1)
    elif xt == '3':
        bmesh.ops.create_cone(bm, segments=16, diameter1=1, diameter2=1, depth=2)
    else:
        raise AssertionError('unsupported shape type: ' + xt)
    bm.to_mesh(mesh)


def _v2ms(vector):
    ms = mathutils.Matrix.Identity(4)
    for i, v in enumerate(vector):
        ms[i][i] = v
    return ms


def _bone_matrix(bone):
    xsh = bone.xray.shape
    m = bone.matrix_local * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
    if xsh.type == '1':  # box
        rt = xsh.box_rot
        m *= mathutils.Matrix.Translation(xsh.box_trn)
        m *= mathutils.Matrix((rt[0:3], rt[3:6], rt[6:9])).transposed().to_4x4()
        m *= _v2ms(xsh.box_hsz)
    elif xsh.type == '2':  # sphere
        m *= mathutils.Matrix.Translation(xsh.sph_pos)
        m *= _v2ms((xsh.sph_rad, xsh.sph_rad, xsh.sph_rad))
    elif xsh.type == '3':  # cylinder
        m *= mathutils.Matrix.Translation(xsh.cyl_pos)
        v_dir = mathutils.Vector(xsh.cyl_dir)
        q_rot = v_dir.rotation_difference((0, 0, 1))
        m *= q_rot.to_matrix().transposed().to_4x4()
        m *= _v2ms((xsh.cyl_rad, xsh.cyl_rad, xsh.cyl_hgh * 0.5))
    else:
        raise AssertionError('unsupported shape type: ' + xsh.type)
    return m


def activate(bone, from_chtype=False):
    h = _helper()
    if h is None:
        mesh = bpy.data.meshes.new(name=__HELPER_NAME + '.mesh')
        hobj = bpy.data.objects.new(__HELPER_NAME, mesh)
        hobj.draw_type = 'WIRE'
        hobj.show_x_ray = True
        hobj.hide_render = True
        bpy.context.scene.objects.link(hobj)
        h = hobj, bone
    else:
        hobj, _ = h
    hobj.parent = bpy.context.active_object
    _apply_type(hobj.data, bone.xray.shape.type)
    m = _bone_matrix(bone)
    hobj.matrix_local = m
    hobj.xray.helper_data = bone.id_data.name + '/' + bone.name

    vs = m.to_scale()
    if not (vs.x and vs.y and vs.z):
        bpy.ops.io_scene_xray.shape_edit_fit()

    if not from_chtype:
        bpy.context.scene.objects.active = hobj
        for obj in bpy.context.selectable_objects:
            obj.select = obj == hobj


def deactivate():
    hobj, _ = _helper()
    bpy.context.scene.objects.unlink(hobj)
    mesh = hobj.data
    bpy.data.objects.remove(hobj)
    bpy.data.meshes.remove(mesh)


def is_helper_object(obj):
    return obj.name == __HELPER_NAME


class _ShapeEditApplyOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.shape_edit_apply'
    bl_label = 'Apply Shape'
    bl_options = {'UNDO'}

    def execute(self, context):
        def maxabs(*args):
            r = 0
            for a in args:
                r = max(r, abs(a))
            return r

        hobj, bone = _helper()
        xsh = bone.xray.shape
        md = (bone.matrix_local * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))).inverted() * hobj.matrix_local
        if xsh.type == '1':  # box
            xsh.box_trn = md.to_translation().to_tuple()
            xsh.box_hsz = (1, 1, 1)
            mr = md.to_3x3().transposed()
            for i in range(3):
                xsh.box_rot[i * 3:i * 3 + 3] = mr[i].to_tuple()
        elif xsh.type == '2':  # sphere
            xsh.sph_pos = md.to_translation().to_tuple()
            xsh.sph_rad = maxabs(*md.to_scale())
        elif xsh.type == '3':  # cylinder
            xsh.cyl_pos = md.to_translation().to_tuple()
            vs = md.to_scale()
            xsh.cyl_hgh = abs(vs[2]) * 2
            xsh.cyl_rad = maxabs(vs[0], vs[1])
            m3 = md.to_3x3()
            ms = mathutils.Matrix.Identity(3)
            for i in range(3):
                ms[i][i] = 1 / vs[i]
            m3 *= ms
            qr = m3.transposed().to_quaternion().inverted()
            vr = qr * mathutils.Vector((0, 0, 1))
            xsh.cyl_dir = vr.to_tuple()
        else:
            raise AssertionError('unsupported shape type: ' + xsh.type)
        for obj in bpy.data.objects:
            if obj.data == bone.id_data:
                bpy.context.scene.objects.active = obj
                break
        deactivate()
        bpy.context.scene.update()
        return {'FINISHED'}


def _bone_objects(bone):
    arm = bone.id_data
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        vg = o.vertex_groups.get(bone.name, None)
        if vg is None:
            continue
        for m in o.modifiers:
            if (m.type == 'ARMATURE') and m.object and (m.object.data == arm):
                yield o, vg.index
                break


def _bone_vertices(bone):
    for obj, vgi in _bone_objects(bone):
        bm = bmesh.new()
        bm.from_object(obj, bpy.context.scene)
        ld = bm.verts.layers.deform.verify()
        utils.fix_ensure_lookup_table(bm.verts)
        for v in bm.verts:
            w = v[ld].get(vgi, 0)
            if w:
                yield v.co


class _ShapeEditFitOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.shape_edit_fit'
    bl_label = 'Fit Shape'
    bl_options = {'UNDO'}

    def execute(self, context):
        def vf(va, vb, f):
            va.x = f(va.x, vb.x)
            va.y = f(va.y, vb.y)
            va.z = f(va.z, vb.z)

        hobj, bone = _helper()
        mr = hobj.matrix_local
        mi = mr
        try:
            mi = mr.inverted()
        except ValueError:
            mr = mathutils.Matrix.Identity(4)
            mi = mr
        hobj.scale = (1, 1, 1)  # ugly: force delayed refresh 3d-view
        mn = mathutils.Vector((+math.inf, +math.inf, +math.inf))
        mx = mathutils.Vector((-math.inf, -math.inf, -math.inf))
        xsh = bone.xray.shape
        if xsh.type == '1':  # box
            for v in _bone_vertices(bone):
                v = mi * v
                vf(mn, v, min)
                vf(mx, v, max)
            if mx.x > mn.x:
                vc = (mx + mn) / 2
                vs = (mx - mn) / 2
                hobj.matrix_local = mr * mathutils.Matrix.Translation(vc) * _v2ms(vs)
        else:
            vertices = []
            for v in _bone_vertices(bone):
                v = mi * v
                vf(mn, v, min)
                vf(mx, v, max)
                vertices.append(v)
            if mx.x > mn.x:
                vc = (mx + mn) / 2
                r = 0
                if xsh.type == '2':  # sphere
                    for v in vertices:
                        r = max(r, (v - vc).length)
                    hobj.matrix_local = mr * mathutils.Matrix.Translation(vc) * _v2ms((r, r, r))
                elif xsh.type == '3':  # cylinder
                    for v in vertices:
                        r = max(r, (v - vc).xy.length)
                    hobj.matrix_local = mr * mathutils.Matrix.Translation(vc) * _v2ms((r, r, (mx.z - mn.z) * 0.5))
                else:
                    raise AssertionError('unsupported shape type: ' + xsh.type)
        bpy.context.scene.update()
        return {'FINISHED'}


def draw(layout, bone):
    l = layout
    if bone.xray.shape.type == '0':
        l = l.split(align=True)
        l.enabled = False
    l.prop(bone.xray.shape, 'edit_mode', text='Edit Shape', toggle=True)
    if not bone.xray.shape.edit_mode:
        return
    layout.operator(_ShapeEditFitOp.bl_idname, icon='BBOX')
    layout.operator(_ShapeEditApplyOp.bl_idname, icon='FILE_TICK')


def draw_helper(layout, obj):
    layout.operator(_ShapeEditFitOp.bl_idname, icon='BBOX')
    layout.operator(_ShapeEditApplyOp.bl_idname, icon='FILE_TICK')


def register():
    bpy.utils.register_class(_ShapeEditApplyOp)
    bpy.utils.register_class(_ShapeEditFitOp)


def unregister():
    bpy.utils.unregister_class(_ShapeEditFitOp)
    bpy.utils.unregister_class(_ShapeEditApplyOp)
