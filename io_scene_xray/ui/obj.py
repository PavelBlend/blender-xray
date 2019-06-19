import bpy

from . import list_helper, collapsible, base
from .. import registry
from ..utils import is_helper_object
from ..details import ui as det_ui


class PropClipOp(bpy.types.Operator):
    bl_idname = 'io_scene_xray.propclip'
    bl_label = ''

    items = (
        ('copy', '', '', 'COPYDOWN', 0),
        ('paste', '', '', 'PASTEDOWN', 1),
        ('clear', '', '', 'X', 2)
    )
    oper = bpy.props.EnumProperty(items=items)
    path = bpy.props.StringProperty()

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
        for item in cls.items:
            lay = layout
            if item[0] in ('copy', 'clear') and not value:
                lay = lay.split(align=True)
                lay.enabled = False
            props = lay.operator(cls.bl_idname, icon=item[3])
            props.oper = item[0]
            props.path = path


@registry.module_thing
class XRayMotionList(bpy.types.UIList):
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
class XRayObjectPanel(base.XRayPanel):
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
                    box.label(line)

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
                    'XRayMotionList', 'name',
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
