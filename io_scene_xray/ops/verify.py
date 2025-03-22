# standart modules
import os

# blender modules
import bpy
import bmesh

# addon modules
from . import general
from . import material
from .. import rw
from .. import formats
from .. import utils
from .. import text


class XRAY_OT_verify_uv(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.verify_uv'
    bl_label = 'Verify UV'
    bl_description = 'Find UV-maps errors in selected objects'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        name='Mode',
        default='SELECTED_OBJECTS',
        items=general.MODE_ITEMS
    )

    MIN_VAL = -32.0
    MAX_VAL = 32.0
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
        objects = general.get_objs_by_mode(self)
        if not objects:
            general.deselect_objs()
            return {'CANCELLED'}
        bad_objects = []
        for bpy_object in objects:
            uv_status = self.verify_uv(context, bpy_object)
            if uv_status == self.BAD_UV:
                bad_objects.append(bpy_object.name)
        general.select_objs(bad_objects)
        self.report(
            {'INFO'},
            text.get_tip(text.warn.incorrect_uv_objs_count) + \
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

        face_sel = [False] * len(mesh.polygons)
        for uv_layer in mesh.uv_layers:
            for polygon in mesh.polygons:
                for loop in polygon.loop_indices:
                    uv = uv_layer.data[loop].uv
                    if (
                            not self.MIN_VAL < uv.x < self.MAX_VAL or \
                            not self.MIN_VAL < uv.y < self.MAX_VAL
                        ):
                        face_sel[polygon.index] = True
                        has_bad_uv = True

        utils.version.set_face_sel(mesh, face_sel)

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
        items=general.MODE_ITEMS
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
            face_sel = [False] * len(mesh.polygons)

            for face in mesh.polygons:
                if face.area < self.EPS:
                    face_sel[face.index] = True
                    is_invalid = True

            utils.version.set_face_sel(mesh, face_sel)

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

                vert_sel = [False] * len(mesh.vertices)
                for face in invalid_faces:
                    for vert in face.verts:
                        vert_sel[vert.index] = True

                # select vertices as model is triangulated
                utils.version.set_vert_sel(mesh, vert_sel)

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

        objs = general.get_objs_by_mode(self)

        if not objs:
            general.deselect_objs()
            return {'CANCELLED'}

        bad_objects = []
        for obj in objs:
            is_invalid = self.check_invalid(context, obj)
            if is_invalid:
                bad_objects.append(obj.name)

        general.select_objs(bad_objects)

        self.report(
            {'INFO'},
            text.get_tip(text.warn.invalid_face_objs_count) + \
            ': {}'.format(len(bad_objects))
        )

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_check_materials(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.check_materials'
    bl_label = 'Check Material Parameters'
    bl_description = 'Check the parameters of the materials for correctness'
    bl_options = {'REGISTER', 'UNDO'}

    mode = material.mode_prop

    def draw(self, context):    # pragma: no cover
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    def _get_xr_data(self, prop):
        # search read function
        if prop == 'eshader_file':
            fun = formats.xr.parse_shaders
        elif prop == 'cshader_file':
            fun = formats.xr.parse_shaders_xrlc
        elif prop == 'gamemtl_file':
            fun = formats.xr.parse_gamemtl
        else:
            raise BaseException('unsupported property')

        # get file data
        files = utils.ie.get_pref_paths(prop)
        file_data = None
        for file in files:
            if os.path.exists(file):
                file_data = rw.utils.read_file(file)
                break

        # read xr data
        names = set()
        if file_data:
            for name, _, _ in fun(file_data):
                names.add(name)

        return names

    @utils.set_cursor_state
    def execute(self, context):
        # search *.xr files data
        shader_names = self._get_xr_data('eshader_file')
        compile_names = self._get_xr_data('cshader_file')
        gamemtl_names = self._get_xr_data('gamemtl_file')

        # search materials
        mats = material.get_materials(context, self.mode)

        # verify material parameters
        logs = []
        bad_mats_count = 0
        logs.append('Incorrect Materials:\n\n')

        # sort materials
        mat_names = [mat.name for mat in mats]
        mat_names.sort()
        mats = {mat.name: mat for mat in mats}

        # search bad materials
        for mat_name in mat_names:
            mat = mats[mat_name]
            xray = mat.xray
            has_err = False
            msg = '    Material: "{}":\n'.format(mat.name)

            if xray.eshader not in shader_names:
                msg += '        Engine Shader: "{}"\n'.format(xray.eshader)
                has_err = True

            if xray.cshader not in compile_names:
                msg += '        Compile Shader: "{}"\n'.format(xray.cshader)
                has_err = True

            if xray.gamemtl not in gamemtl_names:
                msg += '        Game Material: "{}"\n'.format(xray.gamemtl)
                has_err = True

            if has_err:
                msg += '\n'
                logs.append(msg)
                bad_mats_count += 1

        # create log
        report_msg = text.get_tip(text.warn.incorrect_mats)
        if bad_mats_count:
            LOG_FILE_NAME = 'log'
            report_msg = '{0} ({1} "{2}")'.format(
                report_msg,
                text.get_tip(text.warn.see_log),
                LOG_FILE_NAME
            )

            text_log = bpy.data.texts.get(LOG_FILE_NAME)
            if not text_log:
                text_log = bpy.data.texts.new(LOG_FILE_NAME)
                text_log.user_clear()
            text_log.from_string(''.join(logs))

        # report
        self.report(
            {'INFO'},
            report_msg + ': {}'.format(bad_mats_count)
        )

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_verify_uv,
    XRAY_OT_check_invalid_faces,
    XRAY_OT_check_materials
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
