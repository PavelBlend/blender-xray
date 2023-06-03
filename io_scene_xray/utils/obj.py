# standart modules
import time
import platform
import getpass

# blender modules
import bpy

# addon modules
from . import version
from . import stats
from .. import log
from .. import text


HELPER_OBJECT_NAME_PREFIX = '.xray-helper--'


def is_helper_object(obj):
    if not obj:
        return False
    return obj.name.startswith(HELPER_OBJECT_NAME_PREFIX)


def is_armature_context(context):
    obj = context.active_object
    if not obj:
        return False
    return obj.type == 'ARMATURE'


def get_revision_data(revision):
    pref = version.get_preferences()

    if pref.custom_owner_name:
        curruser = pref.custom_owner_name
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


def find_root(obj):
    if obj.xray.isroot:
        return obj
    if obj.parent:
        return find_root(obj.parent)
    else:
        return obj


def create_object(name, data):
    bpy_object = bpy.data.objects.new(name, data)
    version.link_object(bpy_object)
    stats.created_obj()
    return bpy_object


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
