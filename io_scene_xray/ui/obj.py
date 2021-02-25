# blender modules
import bpy

# addon modules
from . import list_helper, collapsible, base
from .. import registry
from ..utils import is_helper_object
from ..details import ui as det_ui
from ..version_utils import assign_props, IS_28
from ..ops.transform_utils import (
    XRAY_OT_UpdateXRayObjectTranforms,
    XRAY_OT_UpdateBlenderObjectTranforms,
    XRAY_OT_CopyObjectTranforms
)
from ..ops import xray_camera


items = (
    ('copy', '', '', 'COPYDOWN', 0),
    ('paste', '', '', 'PASTEDOWN', 1),
    ('clear', '', '', 'X', 2)
)
prop_clip_op_props = {
    'oper': bpy.props.EnumProperty(items=items),
    'path': bpy.props.StringProperty()
}
TRANSLATION_TEXT = 'Translation'
ROTATION_TEXT = 'Rotation'


class PropClipOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.propclip'
    bl_label = ''

    if not IS_28:
        for prop_name, prop_value in prop_clip_op_props.items():
            exec('{0} = prop_clip_op_props.get("{0}")'.format(prop_name))

    def execute(self, context):
        *path, prop = self.path.split('.')
        obj = context
        for name in path:
            obj = getattr(obj, name)
        if self.oper == 'copy':
            context.window_manager.clipboard = getattr(obj, prop)
        elif self.oper == 'paste':
            setattr(obj, prop, context.window_manager.clipboard)
        elif self.oper == 'clear':
            setattr(obj, prop, '')
        return {'FINISHED'}

    @classmethod
    def drawall(cls, layout, path, value):
        for item in items:
            lay = layout
            if item[0] in ('copy', 'clear') and not value:
                lay = lay.split(align=True)
                lay.enabled = False
            props = lay.operator(cls.bl_idname, icon=item[3])
            props.oper = item[0]
            props.path = path


assign_props([
    (prop_clip_op_props, PropClipOp),
])


@registry.module_thing
class XRayMotionList(bpy.types.UIList):
    bl_idname = 'XRAY_UL_MotionList'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        data = context.object.xray
        motion = data.motions_collection[index]

        if data.motions_collection_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)
        row.prop_search(motion, 'name', bpy.data, 'actions', text='')
        if data.use_custom_motion_names:
            row.prop(motion, 'export_name', icon_only=True)


class XRayAddAllActions(bpy.types.Operator):
    bl_idname = 'io_scene_xray.add_all_actions'
    bl_label = 'Add All Actions'
    bl_description = 'Add All Actions'

    def execute(self, context):
        obj = context.object
        for action in bpy.data.actions:
            if not obj.xray.motions_collection.get(action.name):
                motion = obj.xray.motions_collection.add()
                motion.name = action.name
        return {'FINISHED'}


class XRayRemoveAllActions(bpy.types.Operator):
    bl_idname = 'io_scene_xray.remove_all_actions'
    bl_label = 'Remove All Actions'
    bl_description = 'Remove All Actions'

    def execute(self, context):
        obj = context.object
        obj.xray.motions_collection.clear()
        return {'FINISHED'}


def draw_motion_list_custom_elements(layout):
    layout.operator(XRayAddAllActions.bl_idname, text='', icon='ACTION')
    layout.operator(XRayRemoveAllActions.bl_idname, text='', icon='X')


@registry.requires(list_helper, PropClipOp, XRayAddAllActions, XRayRemoveAllActions)
@registry.module_thing
class XRAY_PT_ObjectPanel(base.XRayPanel):
    bl_context = 'object'
    bl_label = base.build_label('Object')

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and not is_helper_object(context.active_object)
        )

    def draw(self, context):
        layout = self.layout
        data = context.object.xray
        layout.prop(data, 'isroot', text='Object', toggle=True)

        if data.isroot:
            object_box = layout.box()
            if not data.flags_use_custom:
                object_box.prop(data, 'flags_simple', text='Type')
            else:
                row = object_box.row(align=True)
                row.prop(data, 'flags_simple', text='Type')
                row.prop(data, 'flags_custom_type', text='')
                col = object_box.column(align=True)
                row = col.row(align=True)
                row.prop(data, 'flags_custom_progressive', text='Progressive', toggle=True)
                row.prop(data, 'flags_custom_lod', text='LOD', toggle=True)
                row.prop(data, 'flags_custom_hom', text='HOM', toggle=True)
                row = col.row(align=True)
                row.prop(data, 'flags_custom_musage', text='Multi Usage', toggle=True)
                row.prop(data, 'flags_custom_soccl', text='Sound Occluder', toggle=True)
                row.prop(data, 'flags_custom_hqexp', text='HQ Export', toggle=True)
            object_box.prop(data, 'lodref')
            object_box.prop(data, 'export_path')
            row, box = collapsible.draw(
                object_box,
                'object:userdata',
                'User Data',
                enabled=data.userdata != '',
                icon='VIEWZOOM'
            )
            PropClipOp.drawall(row, 'object.xray.userdata', data.userdata)
            if box:
                box = box.column(align=True)
                for line in data.userdata.splitlines():
                    box.label(text=line)

            if data.motions:
                split = object_box.split()
                split.alert = True
                split.prop(data, 'motions')
            _, box = collapsible.draw(
                object_box,
                'object:motions',
                'Motions (%d)' % len(data.motions_collection)
            )
            if box:
                box.prop(data, 'play_active_motion', toggle=True, icon='PLAY')
                box.prop(data, 'use_custom_motion_names', toggle=True)
                box.prop_search(data, 'dependency_object', bpy.data, 'objects')
                row = box.row()
                row.template_list(
                    'XRAY_UL_MotionList', 'name',
                    data, 'motions_collection',
                    data, 'motions_collection_index'
                )
                col = row.column(align=True)
                list_helper.draw_list_ops(
                    col, data,
                    'motions_collection', 'motions_collection_index',
                    custom_elements_func=draw_motion_list_custom_elements
                )

            if data.motionrefs:
                split = object_box.split()
                split.alert = True
                split.prop(data, 'motionrefs')
            _, box = collapsible.draw(
                object_box,
                'object:motionsrefs',
                'Motion Refs (%d)' % len(data.motionrefs_collection)
            )
            if box:
                box.prop(data, 'load_active_motion_refs', toggle=True)
                row = box.row()
                row.template_list(
                    'UI_UL_list', 'name',
                    data, 'motionrefs_collection',
                    data, 'motionrefs_collection_index'
                )
                col = row.column(align=True)
                list_helper.draw_list_ops(
                    col, data,
                    'motionrefs_collection', 'motionrefs_collection_index',
                )

            box = object_box.box()
            box.prop(data.revision, 'owner', text='Owner')
            box.prop(data.revision, 'ctime_str', text='Created')

        if context.object.type in {'MESH', 'EMPTY'}:
            layout.prop(data, 'is_details', text='Details', toggle=True)
            if data.is_details:
                det_ui.draw_function(self, context)

        if IS_28:
            layout.prop(data, 'is_level', text='Level', toggle=True)
            if data.is_level:
                ogf_box = layout.box()

                ogf_box.prop(data.level, 'object_type')
                object_type = data.level.object_type

                if object_type == 'LEVEL':
                    ogf_box.prop(data.level, 'source_path')

                elif object_type == 'PORTAL':
                    ogf_box.prop_search(data.level, 'sector_front', bpy.data, 'objects')
                    ogf_box.prop_search(data.level, 'sector_back', bpy.data, 'objects')

                elif object_type == 'VISUAL':
                    ogf_box.prop(data.level, 'visual_type')
                    if data.level.visual_type in {'TREE_ST', 'TREE_PM'}:
                        # color scale
                        color_scale_box = ogf_box.box()
                        color_scale_box.label(text='Color Scale:')

                        col = color_scale_box.row()
                        col.prop(data.level, 'color_scale_rgb')

                        col = color_scale_box.row()
                        col.prop(data.level, 'color_scale_hemi')

                        col = color_scale_box.row()
                        col.prop(data.level, 'color_scale_sun')

                        # color bias
                        color_bias_box = ogf_box.box()
                        color_bias_box.label(text='Color Bias:')

                        col = color_bias_box.row()
                        col.prop(data.level, 'color_bias_rgb')

                        col = color_bias_box.row()
                        col.prop(data.level, 'color_bias_hemi')

                        col = color_bias_box.row()
                        col.prop(data.level, 'color_bias_sun')

                    elif data.level.visual_type in {'NORMAL', 'PROGRESSIVE'}:
                        ogf_box.prop(data.level, 'use_fastpath')

                elif object_type == 'LIGHT_DYNAMIC':
                    ogf_box.prop(data.level, 'controller_id')
                    ogf_box.prop(data.level, 'light_type')
                    ogf_box.prop(data.level, 'diffuse')
                    ogf_box.prop(data.level, 'specular')
                    ogf_box.prop(data.level, 'ambient')
                    ogf_box.prop(data.level, 'range_')
                    ogf_box.prop(data.level, 'falloff')
                    ogf_box.prop(data.level, 'attenuation_0')
                    ogf_box.prop(data.level, 'attenuation_1')
                    ogf_box.prop(data.level, 'attenuation_2')
                    ogf_box.prop(data.level, 'theta')
                    ogf_box.prop(data.level, 'phi')

        row, box = collapsible.draw(
            layout,
            'object:utils',
            'Utils'
        )
        if box:
            box.label(text='X-Ray Engine Transforms:')
            box.prop(data, 'position')
            box.prop(data, 'orientation')
            column = box.column(align=True)
            column.operator(XRAY_OT_UpdateBlenderObjectTranforms.bl_idname)
            column.operator(XRAY_OT_UpdateXRayObjectTranforms.bl_idname)
            column.operator(XRAY_OT_CopyObjectTranforms.bl_idname)
            box.label(text='X-Ray Engine Camera:')
            box.operator(xray_camera.XRAY_OT_AddCamera.bl_idname)
