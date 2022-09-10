# standart modules
import math
import time
import platform
import getpass

# blender modules
import bpy
import bpy_extras

# addon modules
from . import draw
from . import ie
from . import image
from . import material
from . import mesh
from . import bone
from . import version
from .. import bl_info
from .. import log
from .. import text


def version_to_number(major, minor, release):
    return ((major & 0xff) << 24) | ((minor & 0xff) << 16) | (release & 0xffff)


__PLUGIN_VERSION_NUMBER__ = [None]
def plugin_version_number():
    number = __PLUGIN_VERSION_NUMBER__[0]
    if number is None:
        number = version_to_number(*bl_info['version'])
        __PLUGIN_VERSION_NUMBER__[0] = number
    return number


HELPER_OBJECT_NAME_PREFIX = '.xray-helper--'


def is_helper_object(obj):
    if not obj:
        return False
    return obj.name.startswith(HELPER_OBJECT_NAME_PREFIX)


BAD_VTX_GROUP_NAME = '.xr-bad!'


def smooth_euler(current, previous):
    for axis in range(3):
        current[axis] = _smooth_angle(current[axis], previous[axis])


def _smooth_angle(current, previous):
    delta = abs(current - previous)
    new_delta = (current - 2 * math.pi) - previous
    if abs(new_delta) < delta:
        return previous + new_delta
    new_delta = (current + 2 * math.pi) - previous
    if abs(new_delta) < delta:
        return previous + new_delta
    return current


class InitializationContext:
    def __init__(self, operation):
        self.operation = operation
        self.plugin_version_number = plugin_version_number()
        self.thing = None


class ObjectSet:
    def __init__(self):
        self._set = set()

    def sync(self, objects, callback):
        _old = self._set
        if len(objects) == len(_old):
            return
        _new = set()
        for obj in objects:
            hsh = hash(obj)
            _new.add(hsh)
            if hsh not in _old:
                callback(obj)
        self._set = _new


class ObjectsInitializer:
    def __init__(self, keys):
        self._sets = [(key, ObjectSet()) for key in keys]

    def sync(self, operation, collections):
        ctx = InitializationContext(operation)

        def init_thing(thing):
            ctx.thing = thing
            thing.xray.initialize(ctx)

        for key, objset in self._sets:
            things = getattr(collections, key)
            objset.sync(things, init_thing)


def execute_require_filepath(func):
    def wrapper(self, context):
        if not self.filepath:
            self.report({'ERROR'}, text.warn.no_file)
            return {'CANCELLED'}
        return func(self, context)
    return wrapper


def set_cursor_state(method):
    def wrapper(self, context, *args):
        context.window.cursor_set('WAIT')
        result = method(self, context, *args)
        context.window.cursor_set('DEFAULT')
        return result
    return wrapper


class FilenameExtHelper(bpy_extras.io_utils.ExportHelper):
    def export(self, context):
        pass

    @log.execute_with_logger
    @execute_require_filepath
    @set_cursor_state
    def execute(self, context):
        self.export(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.active_object:
            obj = context.active_object
        elif context.selected_objects:
            obj = context.selected_objects[0]
        else:
            obj = None
        if obj:
            self.filepath = obj.name
            if not self.filepath.lower().endswith(self.filename_ext):
                self.filepath += self.filename_ext
            return super().invoke(context, event)
        else:
            self.report({'ERROR'}, text.error.no_active_obj)
            return {'CANCELLED'}


def invoke_require_armature(func):
    def wrapper(self, context, event):
        active = context.active_object
        if not active:
            if context.selected_objects:
                active = context.selected_objects[0]
        if not active:
            self.report({'ERROR'}, text.error.no_active_obj)
            return {'CANCELLED'}
        if active.type != 'ARMATURE':
            self.report({'ERROR'}, text.error.is_not_arm)
            return {'CANCELLED'}
        return func(self, context, event)

    return wrapper


def time_log():
    def decorator(func):
        name = func.__name__
        def wrap(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                log.debug('time', func=name, time=(time.time() - start))
        return wrap
    return decorator


# temporarily not used
def print_time_info(message=None, tabs_count=None, total_time=None):
    if not message:
        print()
        return
    if tabs_count:
        spaces = ' ' * 4 * tabs_count
    else:
        spaces = ''
    if total_time is None:
        print('{0}{1} start...'.format(spaces, message))
    else:
        message_text = '{0}{1: <50}'.format(spaces, message + ' end:')
        message_time = '{0:.6f} sec'.format(total_time)
        print('{0}{1}'.format(message_text, message_time))


def get_revision_data(revision):
    preferences = version.get_preferences()
    if preferences.custom_owner_name:
        curruser = preferences.custom_owner_name
    else:
        curruser = '\\\\{}\\{}'.format(platform.node(), getpass.getuser())
    currtime = int(time.time())
    if (not revision.owner) or (revision.owner == curruser):
        owner = curruser
        if revision.ctime:
            ctime = revision.ctime
        else:
            ctime = currtime
        moder = ''
        mtime = 0
    else:
        owner = revision.owner
        ctime = revision.ctime
        moder = curruser
        mtime = currtime
    return owner, ctime, moder, mtime


def is_armature_context(context):
    obj = context.object
    if not obj:
        return False
    return obj.type == 'ARMATURE'


def get_armature_object(bpy_obj):
    arm_mods = []    # armature modifiers
    armature = None
    for modifier in bpy_obj.modifiers:
        if (modifier.type == 'ARMATURE') and modifier.object:
            arm_mods.append(modifier)
    if len(arm_mods) == 1:
        modifier = arm_mods[0]
        if not modifier.show_viewport:
            log.warn(
                text.warn.object_arm_mod_disabled,
                object=bpy_obj.name,
                modifier=modifier.name
            )
        armature = modifier.object
    elif len(arm_mods) > 1:
        used_mods = []
        for modifier in arm_mods:
            if modifier.show_viewport:
                used_mods.append(modifier)
        if len(used_mods) > 1:
            raise log.AppError(
                text.error.object_many_arms,
                log.props(
                    root_object=bpy_obj.name,
                    armature_objects=[mod.object.name for mod in used_mods]
                )
            )
        else:
            armature = used_mods[0].object
    return armature


def find_root(obj):
    if obj.xray.isroot:
        return obj
    if obj.parent:
        return find_root(obj.parent)
    else:
        return obj


def get_selection_state(context):
    active_object = context.active_object
    selected_objects = set()
    for obj in context.selected_objects:
        selected_objects.add(obj)
    if active_object:
        mode = bpy.context.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode=mode)
    else:
        bpy.ops.object.select_all(action='DESELECT')
    return active_object, selected_objects


def set_selection_state(active_object, selected_objects):
    version.set_active_object(active_object)
    for obj in selected_objects:
        version.select_object(obj)


def set_mode(mode):
    if bpy.context.object:
        bpy.ops.object.mode_set(mode=mode)
