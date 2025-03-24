# blender modules
import bpy

# addon modules
from . import general
from .. import utils
from .. import text


class XRAY_OT_sel_verts_by_weights(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.sel_verts_by_weights'
    bl_label = 'Select Vertices by Weights Count'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='SELECTED_OBJECTS',
        items=general.MODE_ITEMS
    )
    weights_count = bpy.props.IntProperty(
        name='Number of Weights',
        default=0,
        min=0,
        soft_min=0
    )
    sel_type = bpy.props.EnumProperty(
        name='Type',
        default='EQUAL',
        items=(
            ('LESS', 'Less Than', ''),
            ('EQUAL', 'Equal To', ''),
            ('GREATER', 'Greater Than', ''),
            ('NOT_EQUAL', 'Not Equal To', '')
        )
    )

    def _collect_vert_groups(self, mesh_obj, arm_obj):
        vertex_groups = set()

        for group_index, group in enumerate(mesh_obj.vertex_groups):
            bone = arm_obj.data.bones.get(group.name, None)

            if bone is None:
                continue

            if not utils.bone.is_exportable_bone(bone):
                continue

            vertex_groups.add(group_index)

        return vertex_groups

    def _search_arm_obj(self, mesh_obj):
        # search armatures
        arm_objs = set()
        for mod in mesh_obj.modifiers:
            if mod.type == 'ARMATURE':
                if mod.object:
                    arm_objs.add(mod.object)

        arm_objs = list(arm_objs)

        if not arm_objs:
            return None

        elif len(arm_objs) == 1:
            arm_obj = arm_objs[0]

        else:
            xray_arms = []
            for arm_obj in arm_objs:
                if arm_obj.xray.isroot:
                    xray_arms.append(arm_obj)
            if len(xray_arms) == 1:
                arm_obj = xray_arms[0]
            else:
                arm_obj = arm_objs[0]

        return arm_obj

    def _deselect_verts(self, mesh_obj):
        general.deselect_objs()
        utils.version.set_active_object(mesh_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        utils.version.set_active_object(None)

    def _select_verts(self, mesh_obj, fun, groups_count):
        has_selection = False
        for index, vert in enumerate(mesh_obj.data.vertices):
            count = groups_count[index]
            if fun(count):
                vert.select = True
                has_selection = True
        return has_selection

    def _sel_verts_by_weights(self, context, mesh_obj):
        if mesh_obj.type != 'MESH':
            return

        arm_obj = self._search_arm_obj(mesh_obj)
        if not arm_obj:
            return

        vgroups = self._collect_vert_groups(mesh_obj, arm_obj)

        # calculate groups count
        verts = mesh_obj.data.vertices
        groups_count = [0] * len(verts)

        for index, vert in enumerate(verts):
            for group in vert.groups:
                if group.group in vgroups:
                    groups_count[index] += 1

        # deselect vertices
        self._deselect_verts(mesh_obj)

        # select vertices
        if self.sel_type == 'LESS':
            fun = lambda x: x < self.weights_count

        elif self.sel_type == 'EQUAL':
            fun = lambda x: x == self.weights_count

        elif self.sel_type == 'GREATER':
            fun = lambda x: x > self.weights_count

        elif self.sel_type == 'NOT_EQUAL':
            fun = lambda x: x != self.weights_count

        has_selection = self._select_verts(mesh_obj, fun, groups_count)
        return has_selection

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)

        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        column.label(text='Type:')
        column.prop(self, 'sel_type', expand=True)

        layout.prop(self, 'weights_count', expand=True)

    @utils.set_cursor_state
    def execute(self, context):

        # set object mode
        if context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')

        # search objects
        objects = general.get_objs_by_mode(self)
        general.deselect_objs()
        if not objects:
            return {'CANCELLED'}

        # search objects for selection
        sel_objs = []
        for obj in objects:
            # select vertices
            has_verts = self._sel_verts_by_weights(context, obj)
            if has_verts:
                sel_objs.append(obj.name)

        # select objects
        general.select_objs(sel_objs)
        if len(sel_objs) == 1:
            obj = bpy.data.objects[sel_objs[0]]
            utils.version.set_active_object(obj)
            bpy.ops.object.mode_set(mode='EDIT')

        # report
        self.report({'INFO'}, text.get_tip(text.warn.ready))

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_sel_verts_by_weights,
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
