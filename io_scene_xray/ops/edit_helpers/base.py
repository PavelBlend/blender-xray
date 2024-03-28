# blender modules
import bpy

# addon modules
from ... import text
from ... import utils


__HELPERS__ = {}


class AbstractHelper:
    def __init__(self, name):
        if name in __HELPERS__:
            raise AssertionError(
                'helper with name {} is already registered'.format(name)
            )
        __HELPERS__[name] = self
        self._name = utils.obj.HELPER_OBJECT_NAME_PREFIX + name

    def get_helper(self):
        return bpy.data.objects.get(self._name)

    def get_target(self):
        helper = self.get_helper()
        if helper is None:
            return None, None
        return helper, self._get_target_object(helper)

    def activate(self, target):
        helper = self.get_helper()
        if helper is None:
            helper = self._create_helper(self._name)
            utils.version.set_object_draw_type(helper, 'WIRE')
            utils.version.set_object_show_xray(helper, True)
            helper.hide_render = True
            utils.version.link_object(helper)

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

    def draw(self, layout, context):    # pragma: no cover
        if self.is_active(context):
            layout.operator(
                XRAY_OT_edit_cancel.bl_idname,
                text=text.get_iface(text.iface.cancel),
                icon='X'
            )

    def is_active(self, context=bpy.context):
        obj = context.active_object
        if utils.obj.is_helper_object(obj):
            if obj.name != self._name:
                return False
            target = self._get_target_object(obj)
            return target is not None
        target = self.get_target()
        return target and self._is_active_target(target[1], context)

    @staticmethod
    def _select_object(_object):
        utils.version.set_active_object(_object)
        for obj in bpy.context.selectable_objects:
            utils.version.set_object_select(obj, obj == _object)

    def _is_active_target(self, target, context):
        raise NotImplementedError()

    def _get_target_object(self, helper):
        raise NotImplementedError()

    def _create_helper(self, name):
        raise NotImplementedError()

    def _delete_helper(self, helper):
        if utils.version.IS_28:
            bpy.context.scene.collection.objects.unlink(helper)
        else:
            bpy.context.scene.objects.unlink(helper)
        bpy.data.objects.remove(helper)

    def _update_helper(self, helper, target):
        raise NotImplementedError()


def get_object_helper(context):
    obj = context.active_object
    if not utils.obj.is_helper_object(obj):
        return None
    name = obj.name[len(utils.obj.HELPER_OBJECT_NAME_PREFIX):]
    helper = __HELPERS__[name]
    if not helper.is_active(context):
        return None
    return helper


class XRAY_OT_edit_cancel(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.edit_cancel'
    bl_label = text.iface.cancel
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


def register():
    bpy.utils.register_class(XRAY_OT_edit_cancel)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_edit_cancel)
