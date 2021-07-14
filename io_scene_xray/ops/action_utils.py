import bpy

from .. import xray_ltx


SECTION_NAME = 'action_xray_settings'


def get_xray_settings():
    obj = bpy.context.object
    if not obj:
        return
    anim_data = obj.animation_data
    if anim_data:
        action = anim_data.action
        xray = action.xray
        return xray


def write_buffer_data():
    xray = get_xray_settings()
    buffer_text = ''
    if xray:
        buffer_text += '[{}]\n'.format(SECTION_NAME)
        buffer_text += 'fps = {}\n'.format(xray.fps)
        buffer_text += 'flags = {}\n'.format(xray.flags)
        buffer_text += 'speed = {}\n'.format(xray.speed)
        buffer_text += 'accrue = {}\n'.format(xray.accrue)
        buffer_text += 'falloff = {}\n'.format(xray.falloff)
        buffer_text += 'power = {}\n'.format(xray.power)
        buffer_text += 'bonepart_name = "{}"\n'.format(xray.bonepart_name)
        buffer_text += 'bonestart_name = "{}"\n'.format(xray.bonestart_name)
    bpy.context.window_manager.clipboard = buffer_text


def read_buffer_data():
    xray = get_xray_settings()
    if xray:
        buffer_text = bpy.context.window_manager.clipboard
        ltx = xray_ltx.StalkerLtxParser(None, data=buffer_text)
        section = ltx.sections.get(SECTION_NAME, None)
        if not section:
            return
        params = section.params
        xray.fps = float(params.get('fps'))
        xray.flags = int(params.get('flags'))
        xray.speed = float(params.get('speed'))
        xray.accrue = float(params.get('accrue'))
        xray.falloff = float(params.get('falloff'))
        xray.power = float(params.get('power'))
        xray.bonepart_name = params.get('bonepart_name')
        xray.bonestart_name = params.get('bonestart_name')


class XRayCopyActionSettingsOperator(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_action_settings'
    bl_label = 'Copy'

    def execute(self, context):
        write_buffer_data()
        return {'FINISHED'}


class XRayPasteActionSettingsOperator(bpy.types.Operator):
    bl_idname = 'io_scene_xray.paste_action_settings'
    bl_label = 'Paste'

    def execute(self, context):
        read_buffer_data()
        return {'FINISHED'}


classes = (
    XRayCopyActionSettingsOperator,
    XRayPasteActionSettingsOperator
)


def register():
    for operator in classes:
        bpy.utils.register_class(operator)


def unregister():
    for operator in reversed(classes):
        bpy.utils.unregister_class(operator)
