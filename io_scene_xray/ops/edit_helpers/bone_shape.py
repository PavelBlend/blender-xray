# standart modules
import math

# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import base_bone
from ... import utils
from ... import formats


class _BoneShapeEditHelper(base_bone.AbstractBoneEditHelper):
    def draw(self, layout, context):
        if self.is_active(context):
            layout.operator(XRAY_OT_apply_shape.bl_idname, icon='FILE_TICK')
            layout.operator(
                XRAY_OT_fit_shape.bl_idname,
                icon=utils.version.get_icon('BBOX')
            )
            super().draw(layout, context)
            return

        layout.operator(XRAY_OT_edit_shape.bl_idname, text='Edit Shape')

    def _create_helper(self, name):
        mesh = bpy.data.meshes.new(name=name)
        return bpy.data.objects.new(name, mesh)

    def _delete_helper(self, helper):
        mesh = helper.data
        super()._delete_helper(helper)
        bpy.data.meshes.remove(mesh)

    def _update_helper(self, helper, target):
        bone = target
        shape_type = bone.xray.shape.type
        if shape_type == '0':
            self.deactivate()
            return

        super()._update_helper(helper, target)
        mesh = _create_bmesh(shape_type)
        mesh.to_mesh(helper.data)

        mat = _bone_matrix(bone)
        helper.matrix_local = mat

        vscale = mat.to_scale()
        if not (vscale.x and vscale.y and vscale.z):
            bpy.ops.io_scene_xray.edit_bone_shape_fit()


HELPER = _BoneShapeEditHelper('bone-shape-edit')


def _create_bmesh(shape_type):
    mesh = bmesh.new()
    if shape_type == '1':
        bmesh.ops.create_cube(mesh, size=2)
    elif shape_type == '2':
        utils.version.create_bmesh_icosphere(mesh)
    elif shape_type == '3':
        utils.version.create_bmesh_cone(mesh, segments=16)
    else:
        raise AssertionError('unsupported bone shape type: ' + shape_type)
    return mesh


class XRAY_OT_edit_shape(bpy.types.Operator):
    bl_idname = 'io_scene_xray.edit_bone_shape'
    bl_label = 'Edit Bone Shape'
    bl_description = 'Create a helper object that can be ' \
        'used for adjusting bone shape'

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_ARMATURE':
            return False
        bone = context.active_bone
        return bone and (bone.xray.shape.type != '0') and \
            not HELPER.is_active(context)

    def execute(self, context):
        target = context.active_object.data.bones[context.active_bone.name]
        HELPER.activate(target)
        return {'FINISHED'}


def _v2ms(vector):
    matrix = mathutils.Matrix.Identity(4)
    for i, val in enumerate(vector):
        matrix[i][i] = val
    return matrix

def _bone_matrix(bone):
    xsh = bone.xray.shape
    global pose_bone
    pose_bone = bpy.context.object.pose.bones[bone.name]
    multiply = utils.version.get_multiply()
    mat = multiply(
        pose_bone.matrix,
        mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
    )
    mat = multiply(mat, xsh.get_matrix_basis())
    if xsh.type == '1':  # box
        mat = multiply(mat, mathutils.Matrix.Scale(-1, 4, (0, 0, 1)))
        mat = multiply(mat, _v2ms(xsh.box_hsz))
    elif xsh.type == '2':  # sphere
        mat = multiply(mat, _v2ms((xsh.sph_rad, xsh.sph_rad, xsh.sph_rad)))
    elif xsh.type == '3':  # cylinder
        mat = multiply(mat, formats.motions.const.MATRIX_BONE_INVERTED)
        mat = multiply(
            mat,
            _v2ms((
                xsh.cyl_rad,
                xsh.cyl_rad,
                xsh.cyl_hgh * 0.5
            ))
        )
    else:
        raise AssertionError('unsupported bone shape type: ' + xsh.type)
    return mat


class XRAY_OT_apply_shape(bpy.types.Operator):
    bl_idname = 'io_scene_xray.edit_bone_shape_apply'
    bl_label = 'Apply Shape'
    bl_options = {'UNDO'}

    def execute(self, context):
        def maxabs(*args):
            result = 0
            for arg in args:
                result = max(result, abs(arg))
            return result

        hobj, bone = HELPER.get_target()
        xsh = bone.xray.shape
        multiply = utils.version.get_multiply()
        mat = multiply(
            multiply(
                pose_bone.matrix,
                mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
            ).inverted(),
            hobj.matrix_local
        )
        if xsh.type == '1':  # box
            mat = multiply(mat, mathutils.Matrix.Scale(-1, 4, (0, 0, 1)))
            xsh.box_trn = mat.to_translation().to_tuple()
            scale = mat.to_scale()
            xsh.box_hsz = scale.to_tuple()
            mrt = multiply(mat, _v2ms(scale).inverted()).to_3x3().transposed()
            for index in range(3):
                xsh.box_rot[index * 3 : index * 3 + 3] = mrt[index].to_tuple()
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
            for axis in range(3):
                mscale[axis][axis] = 1 / vscale[axis]
            mat3 = multiply(mat3, mscale)
            qrot = mat3.transposed().to_quaternion().inverted()
            vrot = multiply(qrot, mathutils.Vector((0, 0, 1)))
            xsh.cyl_dir = vrot.to_tuple()
        else:
            raise AssertionError('unsupported shape type: ' + xsh.type)
        xsh.set_curver()
        for obj in bpy.data.objects:
            if obj.data == bone.id_data:
                utils.version.set_active_object(obj)
                break
        HELPER.deactivate()
        if utils.version.IS_28:
            bpy.context.view_layer.update()
        else:
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
            if (mod.type == 'ARMATURE') and mod.object and \
                    (mod.object.data == arm):
                yield obj, group.index
                break


def _bone_vertices(bone):
    for obj, vgi in _bone_objects(bone):
        bmsh = bmesh.new()
        if utils.version.IS_28:
            bmsh.from_object(obj, bpy.context.view_layer.depsgraph)
        else:
            bmsh.from_object(obj, bpy.context.scene)
        layer_deform = bmsh.verts.layers.deform.verify()
        utils.mesh.fix_ensure_lookup_table(bmsh.verts)
        for vtx in bmsh.verts:
            weight = vtx[layer_deform].get(vgi, 0)
            if weight:
                yield vtx.co


class XRAY_OT_fit_shape(bpy.types.Operator):
    bl_idname = 'io_scene_xray.edit_bone_shape_fit'
    bl_label = 'Fit Shape'
    bl_options = {'UNDO'}

    def execute(self, context):
        def vfunc(vtx_a, vtx_b, func):
            vtx_a.x = func(vtx_a.x, vtx_b.x)
            vtx_a.y = func(vtx_a.y, vtx_b.y)
            vtx_a.z = func(vtx_a.z, vtx_b.z)

        hobj, bone = HELPER.get_target()
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
        multiply = utils.version.get_multiply()
        if xsh.type == '1':  # box
            for vtx in _bone_vertices(bone):
                vtx = multiply(matrix_inverted, vtx)
                vfunc(vmin, vtx, min)
                vfunc(vmax, vtx, max)
            if vmax.x > vmin.x:
                vcenter = (vmax + vmin) / 2
                vscale = (vmax - vmin) / 2
                hobj.matrix_local = multiply(
                    matrix,
                    mathutils.Matrix.Translation(vcenter),
                    _v2ms(vscale)
                )
        else:
            vertices = []
            for vtx in _bone_vertices(bone):
                vtx = multiply(matrix_inverted, vtx)
                vfunc(vmin, vtx, min)
                vfunc(vmax, vtx, max)
                vertices.append(vtx)
            if vmax.x > vmin.x:
                vcenter = (vmax + vmin) / 2
                radius = 0
                if xsh.type == '2':  # sphere
                    for vtx in vertices:
                        radius = max(radius, (vtx - vcenter).length)
                    hobj.matrix_local = multiply(
                        matrix,
                        mathutils.Matrix.Translation(vcenter),
                        _v2ms((radius, radius, radius))
                    )
                elif xsh.type == '3':  # cylinder
                    for vtx in vertices:
                        radius = max(radius, (vtx - vcenter).xy.length)
                    hobj.matrix_local = multiply(
                        matrix,
                        mathutils.Matrix.Translation(vcenter),
                        _v2ms((radius, radius, (vmax.z - vmin.z) * 0.5))
                    )
                else:
                    raise AssertionError('unsupported shape type: ' + xsh.type)
        if utils.version.IS_28:
            bpy.context.view_layer.update()
        else:
            bpy.context.scene.update()
        return {'FINISHED'}


classes = (
    XRAY_OT_edit_shape,
    XRAY_OT_apply_shape,
    XRAY_OT_fit_shape
)


def register():
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
