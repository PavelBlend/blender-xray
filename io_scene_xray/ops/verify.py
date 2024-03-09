# blender modules
import bpy
import bmesh

# addon modules
from .. import utils
from .. import text


def get_objects(self):
    objects = []
    if self.mode == 'ACTIVE_OBJECT':
        active_obj = bpy.context.active_object
        if active_obj:
            objects.append(active_obj)
        else:
            self.report(
                {'WARNING'},
                text.get_text(text.error.no_active_obj)
            )
    elif self.mode == 'SELECTED_OBJECTS':
        if not bpy.context.selected_objects:
            self.report(
                {'WARNING'},
                text.get_text(text.error.no_selected_obj)
            )
        else:
            objects = [obj for obj in bpy.context.selected_objects]
    elif self.mode == 'ALL_OBJECTS':
        if not bpy.data.objects:
            self.report({'WARNING'}, text.error.no_blend_obj)
        else:
            objects = [obj for obj in bpy.context.scene.objects]
    return objects


mode_items = (
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', '')
)


class XRAY_OT_verify_uv(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.verify_uv'
    bl_label = 'Verify UV'
    bl_description = 'Find UV-maps errors in selected objects'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='SELECTED_OBJECTS',
        items=mode_items
    )

    MINIMUM_VALUE = -32.0
    MAXIMUM_VALUE = 32.0
    BAD_UV = True
    CORRECT_UV = False

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        # set object mode
        if context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')
        objects = get_objects(self)
        if not objects:
            bpy.ops.object.select_all(action='DESELECT')
            utils.version.set_active_object(None)
            return {'CANCELLED'}
        bad_objects = []
        for bpy_object in objects:
            uv_status = self.verify_uv(context, bpy_object)
            if uv_status == self.BAD_UV:
                bad_objects.append(bpy_object.name)
        bpy.ops.object.select_all(action='DESELECT')
        for bad_object_name in bad_objects:
            bad_object = bpy.data.objects[bad_object_name]
            utils.version.select_object(bad_object)
        utils.version.set_active_object(None)
        self.report(
            {'INFO'},
            text.get_text(text.warn.incorrect_uv_objs_count) + \
            ': {}'.format(len(bad_objects))
        )
        return {'FINISHED'}

    def verify_uv(self, context, bpy_object):
        if bpy_object.type != 'MESH':
            return self.CORRECT_UV
        utils.version.set_active_object(bpy_object)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        mesh = bpy_object.data
        has_bad_uv = False
        for uv_layer in mesh.uv_layers:
            for polygon in mesh.polygons:
                for loop in polygon.loop_indices:
                    uv = uv_layer.data[loop].uv
                    if not self.MINIMUM_VALUE < uv.x < self.MAXIMUM_VALUE:
                        polygon.select = True
                        has_bad_uv = True
                    if not self.MINIMUM_VALUE < uv.y < self.MAXIMUM_VALUE:
                        polygon.select = True
                        has_bad_uv = True

        if has_bad_uv:
            result = self.BAD_UV
        else:
            result = self.CORRECT_UV

        return result

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_check_invalid_faces(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.check_invalid_faces'
    bl_label = 'Check Invalid Faces'
    bl_description = 'Find invalid faces'
    bl_options = {'REGISTER', 'UNDO'}

    EPS = 0.00001
    EPS_UV = 0.5 / 4096    # half pixel from 4096 texture

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='SELECTED_OBJECTS',
        items=mode_items
    )
    face_area = bpy.props.BoolProperty(
        name='Check Face Area',
        default=True
    )
    uv_area = bpy.props.BoolProperty(
        name='Check UV Area',
        default=True
    )

    def check_invalid(self, context, bpy_obj):
        if bpy_obj.type != 'MESH':
            return False

        utils.version.set_active_object(bpy_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        mesh = bpy_obj.data
        is_invalid = False

        # check face area
        if self.face_area:
            for face in mesh.polygons:
                if face.area < self.EPS:
                    face.select = True
                    is_invalid = True

        # check uv area
        if self.uv_area:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.triangulate(bm, faces=bm.faces)

            # search invalid faces
            invalid_faces = set()

            for uv_name in bm.loops.layers.uv.keys():
                uv_layer = bm.loops.layers.uv[uv_name]
                for face in bm.faces:
                    uvs = []
                    for vert_index, vert in enumerate(face.verts):
                        uv_coord = face.loops[vert_index][uv_layer].uv
                        uvs.append(uv_coord)

                    dist_1 = abs((uvs[0] - uvs[1]).length)
                    dist_2 = abs((uvs[1] - uvs[2]).length)
                    dist_3 = abs((uvs[2] - uvs[0]).length)
                    perimeter = dist_1 + dist_2 + dist_3

                    if perimeter < self.EPS_UV:
                        invalid_faces.add(face)

            # select vertices
            if invalid_faces:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')

                for face in invalid_faces:
                    for vert in face.verts:
                        # select vertices as model is triangulated
                        mesh.vertices[vert.index].select = True
                is_invalid = True

        return is_invalid

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)
        column.prop(self, 'face_area')
        column.prop(self, 'uv_area')

    @utils.set_cursor_state
    def execute(self, context):
        # set object mode
        if context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')

        objs = get_objects(self)

        if not objs:
            bpy.ops.object.select_all(action='DESELECT')
            utils.version.set_active_object(None)
            return {'CANCELLED'}

        bad_objects = []
        for obj in objs:
            is_invalid = self.check_invalid(context, obj)
            if is_invalid:
                bad_objects.append(obj.name)

        bpy.ops.object.select_all(action='DESELECT')
        for obj_name in bad_objects:
            obj = bpy.data.objects[obj_name]
            utils.version.select_object(obj)
        utils.version.set_active_object(None)

        self.report(
            {'INFO'},
            text.get_text(text.warn.invalid_face_objs_count) + \
            ': {}'.format(len(bad_objects))
        )

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_verify_uv,
    XRAY_OT_check_invalid_faces
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
