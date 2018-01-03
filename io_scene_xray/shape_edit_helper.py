import math

import bpy
import bmesh
import mathutils

from . import utils
from . import registry

__HELPER_NAME = utils.HELPER_OBJECT_NAME_PREFIX + 'bone-shape-edit'


def _helper():
    hobj = bpy.data.objects.get(__HELPER_NAME)
    if hobj is None:
        return
    split = hobj.xray.helper_data.split('/')
    if len(split) != 2:
        return
    arm = bpy.data.armatures.get(split[0], None)
    if arm is None:
        return
    bone = arm.bones.get(split[1], None)
    if bone is None:
        return
    return hobj, bone


def is_active():
    helper = _helper()
    if helper is None:
        return False
    bone = bpy.context.active_bone
    if bone is None:
        return False
    return (helper[1].name == bone.name) and (helper[1].id_data == bone.id_data)


def _apply_type(mesh, type):
    bmsh = bmesh.new()
    if type == '1':
        bmesh.ops.create_cube(bmsh, size=2)
    elif type == '2':
        bmesh.ops.create_icosphere(bmsh, subdivisions=2, diameter=1)
    elif type == '3':
        bmesh.ops.create_cone(bmsh, segments=16, diameter1=1, diameter2=1, depth=2)
    else:
        raise AssertionError('unsupported shape type: ' + type)
    bmsh.to_mesh(mesh)


def _v2ms(vector):
    matrix = mathutils.Matrix.Identity(4)
    for i, val in enumerate(vector):
        matrix[i][i] = val
    return matrix


def _bone_matrix(bone):
    xsh = bone.xray.shape
    mat = bone.xray.matrix_local(bone) * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
    if xsh.type == '1':  # box
        rot = xsh.box_rot
        mat *= mathutils.Matrix.Translation(xsh.box_trn)
        mat *= mathutils.Matrix((rot[0:3], rot[3:6], rot[6:9])).transposed().to_4x4()
        mat *= _v2ms(xsh.box_hsz)
    elif xsh.type == '2':  # sphere
        mat *= mathutils.Matrix.Translation(xsh.sph_pos)
        mat *= _v2ms((xsh.sph_rad, xsh.sph_rad, xsh.sph_rad))
    elif xsh.type == '3':  # cylinder
        mat *= mathutils.Matrix.Translation(xsh.cyl_pos)
        v_dir = mathutils.Vector(xsh.cyl_dir)
        q_rot = v_dir.rotation_difference((0, 0, 1))
        mat *= q_rot.to_matrix().transposed().to_4x4()
        mat *= _v2ms((xsh.cyl_rad, xsh.cyl_rad, xsh.cyl_hgh * 0.5))
    else:
        raise AssertionError('unsupported shape type: ' + xsh.type)
    return mat


def activate(bone, from_chtype=False):
    helper = _helper()
    if helper is None:
        mesh = bpy.data.meshes.new(name=__HELPER_NAME + '.mesh')
        hobj = bpy.data.objects.new(__HELPER_NAME, mesh)
        hobj.draw_type = 'WIRE'
        hobj.show_x_ray = True
        hobj.hide_render = True
        bpy.context.scene.objects.link(hobj)
        helper = hobj, bone
    else:
        hobj, _ = helper
    hobj.parent = bpy.context.active_object
    _apply_type(hobj.data, bone.xray.shape.type)
    mat = _bone_matrix(bone)
    hobj.matrix_local = mat
    hobj.xray.helper_data = bone.id_data.name + '/' + bone.name

    vscale = mat.to_scale()
    if not (vscale.x and vscale.y and vscale.z):
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


@registry.module_thing
class _ShapeEditApplyOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.shape_edit_apply'
    bl_label = 'Apply Shape'
    bl_options = {'UNDO'}

    def execute(self, _context):
        def maxabs(*args):
            result = 0
            for arg in args:
                result = max(result, abs(arg))
            return result

        hobj, bone = _helper()
        xsh = bone.xray.shape
        mat = (bone.xray.matrix_local(bone) * mathutils.Matrix.Scale(-1, 4, (0, 0, 1))).inverted() \
            * hobj.matrix_local
        if xsh.type == '1':  # box
            xsh.box_trn = mat.to_translation().to_tuple()
            xsh.box_hsz = (1, 1, 1)
            mrt = mat.to_3x3().transposed()
            for i in range(3):
                xsh.box_rot[i * 3:i * 3 + 3] = mrt[i].to_tuple()
        elif xsh.type == '2':  # sphere
            xsh.sph_pos = mat.to_translation().to_tuple()
            xsh.sph_rad = maxabs(*mat.to_scale())
        elif xsh.type == '3':  # cylinder
            xsh.cyl_pos = mat.to_translation().to_tuple()
            vscale = mat.to_scale()
            xsh.cyl_hgh = abs(vscale[2]) * 2
            xsh.cyl_rad = maxabs(vscale[0], vscale[1])
            mat3 = mat.to_3x3()
            mscale = mathutils.Matrix.Identity(3)
            for i in range(3):
                mscale[i][i] = 1 / vscale[i]
            mat3 *= mscale
            qrot = mat3.transposed().to_quaternion().inverted()
            vrot = qrot * mathutils.Vector((0, 0, 1))
            xsh.cyl_dir = vrot.to_tuple()
        else:
            raise AssertionError('unsupported shape type: ' + xsh.type)
        xsh.set_curver()
        for obj in bpy.data.objects:
            if obj.data == bone.id_data:
                bpy.context.scene.objects.active = obj
                break
        deactivate()
        bpy.context.scene.update()
        return {'FINISHED'}


def _bone_objects(bone):
    arm = bone.id_data
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        group = obj.vertex_groups.get(bone.name, None)
        if group is None:
            continue
        for mod in obj.modifiers:
            if (mod.type == 'ARMATURE') and mod.object and (mod.object.data == arm):
                yield obj, group.index
                break


def _bone_vertices(bone):
    for obj, vgi in _bone_objects(bone):
        bmsh = bmesh.new()
        bmsh.from_object(obj, bpy.context.scene)
        layer_deform = bmsh.verts.layers.deform.verify()
        utils.fix_ensure_lookup_table(bmsh.verts)
        for vtx in bmsh.verts:
            weight = vtx[layer_deform].get(vgi, 0)
            if weight:
                yield vtx.co


@registry.module_thing
class _ShapeEditFitOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.shape_edit_fit'
    bl_label = 'Fit Shape'
    bl_options = {'UNDO'}

    def execute(self, _context):
        def vfunc(vtx_a, vtx_b, func):
            vtx_a.x = func(vtx_a.x, vtx_b.x)
            vtx_a.y = func(vtx_a.y, vtx_b.y)
            vtx_a.z = func(vtx_a.z, vtx_b.z)

        hobj, bone = _helper()
        matrix = hobj.matrix_local
        matrix_inverted = matrix
        try:
            matrix_inverted = matrix.inverted()
        except ValueError:
            matrix = mathutils.Matrix.Identity(4)
            matrix_inverted = matrix
        hobj.scale = (1, 1, 1)  # ugly: force delayed refresh 3d-view
        vmin = mathutils.Vector((+math.inf, +math.inf, +math.inf))
        vmax = mathutils.Vector((-math.inf, -math.inf, -math.inf))
        xsh = bone.xray.shape
        if xsh.type == '1':  # box
            for vtx in _bone_vertices(bone):
                vtx = matrix_inverted * vtx
                vfunc(vmin, vtx, min)
                vfunc(vmax, vtx, max)
            if vmax.x > vmin.x:
                vcenter = (vmax + vmin) / 2
                vscale = (vmax - vmin) / 2
                hobj.matrix_local = matrix * mathutils.Matrix.Translation(vcenter) * _v2ms(vscale)
        else:
            vertices = []
            for vtx in _bone_vertices(bone):
                vtx = matrix_inverted * vtx
                vfunc(vmin, vtx, min)
                vfunc(vmax, vtx, max)
                vertices.append(vtx)
            if vmax.x > vmin.x:
                vcenter = (vmax + vmin) / 2
                radius = 0
                if xsh.type == '2':  # sphere
                    for vtx in vertices:
                        radius = max(radius, (vtx - vcenter).length)
                    hobj.matrix_local = matrix * mathutils.Matrix.Translation(vcenter) \
                        * _v2ms((radius, radius, radius))
                elif xsh.type == '3':  # cylinder
                    for vtx in vertices:
                        radius = max(radius, (vtx - vcenter).xy.length)
                    hobj.matrix_local = matrix * mathutils.Matrix.Translation(vcenter) \
                        * _v2ms((radius, radius, (vmax.z - vmin.z) * 0.5))
                else:
                    raise AssertionError('unsupported shape type: ' + xsh.type)
        bpy.context.scene.update()
        return {'FINISHED'}


def draw(layout, bone):
    lay = layout
    if bone.xray.shape.type == '0':
        lay = lay.split(align=True)
        lay.enabled = False
    lay.prop(bone.xray.shape, 'edit_mode', text='Edit Shape', toggle=True)
    if not bone.xray.shape.edit_mode:
        return
    layout.operator(_ShapeEditFitOp.bl_idname, icon='BBOX')
    layout.operator(_ShapeEditApplyOp.bl_idname, icon='FILE_TICK')


def draw_helper(layout):
    layout.operator(_ShapeEditFitOp.bl_idname, icon='BBOX')
    layout.operator(_ShapeEditApplyOp.bl_idname, icon='FILE_TICK')
