# blender modules
import bpy
import bmesh
import mathutils

# addon modules
from . import general
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


def check_invalid_smooth_groups(objs):
    # search invalid objects
    invalid_objects = set()

    for bpy_obj in objs:
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

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='SELECTED_OBJECTS',
        items=general.MODE_ITEMS
    )

    def draw(self, context):    # pragma: no cover
        col = self.layout.column(align=True)

        col.label(text='Mode:')
        col.prop(self, 'mode', expand=True)

    def execute(self, context):
        # get objects
        objs = general.get_objs_by_mode(self)

        if not objs:
            bpy.ops.object.select_all(action='DESELECT')
            utils.version.set_active_object(None)
            return {'CANCELLED'}

        check_invalid_smooth_groups(objs)

        self.report({'INFO'}, text.warn.ready)

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_check_sg_incompatibility(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.check_sg_incompatibility'
    bl_label = 'Check Smoothing Groups Incompatibility'
    bl_description = 'Find smoothing groups incompatibility'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='SELECTED_OBJECTS',
        items=general.MODE_ITEMS
    )

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    def check_sg_incomp(self, context, bpy_obj):

        if bpy_obj.type != 'MESH':
            return

        bpy_mesh = bpy_obj.data

        bm = bmesh.new()
        bm.from_mesh(bpy_mesh)

        # generate smoothing groups
        smooth_groups = gen_smooth_groups(bm.faces)

        # search incompatibility edges smoothing
        incomp_sg = False
        incomp_edges = set()
        for edge in bm.edges:
            if len(edge.link_faces) != 2:
                continue
            sg_0 = smooth_groups[edge.link_faces[0]]
            sg_1 = smooth_groups[edge.link_faces[1]]
            if not edge.smooth:
                if sg_0 == sg_1:
                    incomp_edges.add(edge.index)
                    incomp_sg = True

        # select incompatibility edges
        if incomp_sg:
            utils.version.set_active_object(bpy_obj)

            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            for edge_index in incomp_edges:
                bpy_mesh.edges[edge_index].select = True

        return incomp_sg

    @utils.set_cursor_state
    def execute(self, context):

        # set object mode
        if context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')

        # get objects
        objs = general.get_objs_by_mode(self)

        # if no objects found, then deselect
        if not objs:
            general.deselect_objs()
            return {'CANCELLED'}

        # search bad objects
        bad_objects = []
        for obj in objs:
            is_invalid = self.check_sg_incomp(context, obj)
            if is_invalid:
                bad_objects.append(obj.name)

        # select bad objects
        general.select_objs(bad_objects)

        # report
        self.report(
            {'INFO'},
            text.get_tip(text.warn.invalid_sg_objs_count) + \
            ': {}'.format(len(bad_objects))
        )

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_check_invalid_sg_objs,
    XRAY_OT_check_sg_incompatibility
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
