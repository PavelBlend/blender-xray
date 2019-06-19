import bpy

from io_scene_xray import registry, utils


__HELPERS__ = dict()


class AbstractHelper:
    def __init__(self, name):
        if name in __HELPERS__:
            raise AssertionError('helper with name ' + name + ' is already registered')
        __HELPERS__[name] = self
        self._name = utils.HELPER_OBJECT_NAME_PREFIX + name

    def get_helper(self):
        return bpy.data.objects.get(self._name)

    def get_target(self):
        helper = self.get_helper()
        if helper is None:
            return
        return helper, self._get_target_object(helper)

    def activate(self, target):
        helper = self.get_helper()
        if helper is None:
            helper = self._create_helper(self._name)
            helper.draw_type = 'WIRE'
            helper.show_x_ray = True
            helper.hide_render = True
            bpy.context.scene.objects.link(helper)

        helper.parent = bpy.context.active_object
        self._update_helper(helper, target)

        AbstractHelper._select_object(helper)

    def update(self):
        helper = self.get_helper()
        if helper is None:
            return
        target = self._get_target_object(helper)
        self._update_helper(helper, target)

    def deactivate(self):
        helper = self.get_helper()
        if helper is not None:
            AbstractHelper._select_object(helper.parent)
            self._delete_helper(helper)

    def draw(self, layout, context):
        if self.is_active(context):
            layout.operator(EditCancel.bl_idname, icon='X')

    def is_active(self, context=bpy.context):
        obj = context.active_object
        if utils.is_helper_object(obj):
            if obj.name != self._name:
                return False
            target = self._get_target_object(obj)
            return target is not None
        target = self.get_target()
        return target and self._is_active_target(target[1], context)

    @staticmethod
    def _select_object(_object):
        bpy.context.scene.objects.active = _object
        for obj in bpy.context.selectable_objects:
            obj.select = obj == _object

    def _is_active_target(self, target, context):
        raise NotImplementedError()

    def _get_target_object(self, helper):
        raise NotImplementedError()

    def _create_helper(self, name):
        raise NotImplementedError()

    def _delete_helper(self, helper):
        bpy.context.scene.objects.unlink(helper)
        bpy.data.objects.remove(helper)

    def _update_helper(self, helper, target):
        raise NotImplementedError()


def get_object_helper(context):
    obj = context.active_object
    if not utils.is_helper_object(obj):
        return None
    name = obj.name[len(utils.HELPER_OBJECT_NAME_PREFIX):]
    helper = __HELPERS__[name]
    if not helper.is_active(context):
        return None
    return helper


@registry.module_thing
class EditCancel(bpy.types.Operator):
    bl_idname = 'io_scene_xray.edit_cancel'
    bl_label = 'Cancel'
    bl_description = 'Cancel editing and remove a helper object'

    @classmethod
    def poll(cls, context):
        return _get_active_helper(context) is not None

    def execute(self, context):
        helper = _get_active_helper(context)
        helper.deactivate()
        return {'FINISHED'}


def _get_active_helper(context):
    for helper in __HELPERS__.values():
        if helper.is_active(context):
            return helper
    return None
