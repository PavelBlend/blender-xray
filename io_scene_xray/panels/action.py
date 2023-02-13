# blender modules
import bpy

# addon modules
from .. import ui
from .. import utils
from .. import formats
from .. import ops


class XRAY_PT_action(ui.base.XRayPanel):
    bl_category = ui.base.CATEGORY
    bl_space_type = utils.version.get_action_panel_space()
    bl_region_type = 'UI'
    bl_context = 'object'
    bl_label = ui.base.build_label('Action')

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if not obj:
            return

        if not (obj.animation_data and obj.animation_data.action):
            return

        pref = utils.version.get_preferences()

        panel_used = (
            # import formats
            pref.enable_object_import or
            pref.enable_skls_import or
            pref.enable_ogf_import or
            pref.enable_omf_import or
            pref.enable_anm_import or

            # export formats
            pref.enable_object_export or
            pref.enable_skls_export or
            pref.enable_skl_export or
            pref.enable_ogf_export or
            pref.enable_omf_export or
            pref.enable_anm_export
        )

        return panel_used

    def draw_refine_props(self, layout, data):
        layout.prop(data, 'autobake_custom_refine', toggle=True)

        col = layout.column(align=True)
        col.active = data.autobake_custom_refine

        col.prop(data, 'autobake_refine_location', text='Location Threshold')
        col.prop(data, 'autobake_refine_rotation', text='Rotation Threshold')

    def draw_bake_props(self, layout, data, autobake_props):
        col = layout.column(align=True)

        col.label(text='Bake:')

        if autobake_props:
            row = col.row(align=True)
            row.prop(data, 'autobake', expand=True)

            col = col.column(align=True)
            col.active = data.autobake != 'off'

        self.draw_refine_props(col, data)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        action = obj.animation_data.action
        data = action.xray

        col = layout.column(align=True)

        col.prop(data, 'fps', text='FPS')

        if obj.type != 'ARMATURE':
            # *.anm format properties
            self.draw_bake_props(layout, data, True)
            return

        col.prop(data, 'speed', text='Speed')
        col.prop(data, 'accrue', text='Accrue')
        col.prop(data, 'falloff', text='Falloff')

        layout.prop(data, 'flags_fx', text='Type FX', toggle=True)

        row = layout.row(align=True)

        if data.flags_fx:
            row.label(text='Start Bone:')
            row.prop_search(
                data,
                'bonestart_name',
                obj.pose,
                'bones',
                text=''
            )
            layout.prop(data, 'power', text='Power')

        else:
            row.label(text='Bone Part:')
            row.prop_search(
                data,
                'bonepart_name',
                obj.pose,
                'bone_groups',
                text=''
            )

            col = layout.column(align=True)
            row = col.row(align=True)

            row.prop(data, 'flags_stopatend', text='Stop', toggle=True)
            row.prop(data, 'flags_nomix', text='No Mix', toggle=True)
            row.prop(data, 'flags_syncpart', text='Sync', toggle=True)

            row = col.row(align=True)
            row.prop(data, 'flags_footsteps', text='Foot Steps', toggle=True)
            row.prop(data, 'flags_movexform', text='Move XForm', toggle=True)

            row = col.row(align=True)
            row.prop(data, 'flags_idle', text='Idle', toggle=True)
            row.prop(data, 'flags_weaponbone', text='Weapon Bone', toggle=True)

        # *.skls bake settings
        layout.separator()
        self.draw_bake_props(layout, data, False)
        layout.separator()

        # copy/paste operators
        row = layout.row(align=True)
        row.label(text='Settings:')
        row.operator(ops.action.XRAY_OT_copy_action_settings.bl_idname)
        row.operator(ops.action.XRAY_OT_paste_action_settings.bl_idname)

        # export operators
        layout.context_pointer_set(
            formats.skl.ops.XRAY_OT_export_skl.bl_idname + '.action',
            action
        )
        layout.operator(
            formats.skl.ops.XRAY_OT_export_skl.bl_idname,
            icon='EXPORT'
        )


def register():
    bpy.utils.register_class(XRAY_PT_action)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_action)
