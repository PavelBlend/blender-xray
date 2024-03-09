# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from .. import utils
from .. import text


def gen_smooth_groups(bm_faces):
    sgroup_gen = 0
    smooth_groups = {}

    for face in bm_faces:
        sgroup_index = smooth_groups.get(face)

        if sgroup_index is None:
            sgroup_index = sgroup_gen
            smooth_groups[face] = sgroup_index
            sgroup_gen += 1
            faces = [face, ]

            for bm_face in faces:
                for edge in bm_face.edges:
                    if edge.smooth:

                        for linked_face in edge.link_faces:
                            if smooth_groups.get(linked_face) is None:
                                smooth_groups[linked_face] = sgroup_index
                                faces.append(linked_face)

    return smooth_groups


def find_invalid_smooth_groups_verts(bpy_mesh):
    # create and triangulate mesh
    bm = bmesh.new()
    bm.from_mesh(bpy_mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    EPS = 0.0000001
    invalid_verts = set()
    smooth_groups = gen_smooth_groups(bm.faces)

    # find invalid smooth group
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert

            # vertex split-normal
            normal = mathutils.Vector((0.0, 0.0, 0.0))

            for vert_face in vert.link_faces:
                if smooth_groups[face] == smooth_groups[vert_face]:
                    normal += vert_face.normal

            normal_length = normal.length

            if normal_length < EPS:
                invalid_verts.add(vert.index)

    return invalid_verts


def select_invalid_smooth_groups_verts(bpy_obj):
    has_invalid_verts = False

    if bpy_obj.type != 'MESH':
        return has_invalid_verts

    # search invalid vertices
    bpy_mesh = bpy_obj.data
    invalid_verts = find_invalid_smooth_groups_verts(bpy_mesh)

    # select invalid vertices
    if invalid_verts:
        utils.version.set_active_object(bpy_obj)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        for vert_index in invalid_verts:
            bpy_mesh.vertices[vert_index].select = True

    has_invalid_verts = bool(invalid_verts)

    return has_invalid_verts


def check_invalid_smooth_groups():
    # search invalid objects
    invalid_objects = set()

    for bpy_obj in bpy.context.selected_objects:
        has_invalid_verts = select_invalid_smooth_groups_verts(bpy_obj)
        if has_invalid_verts:
            invalid_objects.add(bpy_obj)

    # select invalid objects
    utils.version.set_active_object(None)
    bpy.ops.object.select_all(action='DESELECT')

    for bpy_obj in invalid_objects:
        utils.version.select_object(bpy_obj)


class XRAY_OT_check_invalid_sg_objs(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.check_invalid_sg_objs'
    bl_label = 'Check Invalid Smooth Groups'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        check_invalid_smooth_groups()

        self.report({'INFO'}, text.warn.ready)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(XRAY_OT_check_invalid_sg_objs)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_check_invalid_sg_objs)
