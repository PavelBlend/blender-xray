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

SOC_LEVEL_FOV = 67.5
SOC_HUD_FOV_FACTOR = 0.45
SOC_HUD_FOV = SOC_LEVEL_FOV * SOC_HUD_FOV_FACTOR


def is_helper_object(obj):
    if not obj:
        return False
    return obj.name.startswith(HELPER_OBJECT_NAME_PREFIX)


def is_armature_context(context):
    obj = context.active_object
    if not obj:
        return False
    return obj.type == 'ARMATURE'


def get_current_user():
    pref = version.get_preferences()

    if pref.custom_owner_name:
        curruser = pref.custom_owner_name
    else:
        curruser = '\\\\{}\\{}'.format(platform.node(), getpass.getuser())

    return curruser


def get_revision_data(revision):
    curruser = get_current_user()

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


def get_exp_objs(context, root_obj):
    # get exported objects

    objects = [root_obj, ]
    processed_obj = set()

    scan_obj(context, objects, processed_obj)

    exp_objs = [
        obj
        for obj in objects
            if obj.name in bpy.context.scene.objects
    ]

    return exp_objs


def scan_obj(context, objects, processed_obj):
    for obj in objects:
        parent = obj.parent
        if parent and parent not in processed_obj:
            objects.append(parent)

        for child_obj in context.children[obj.name]:
            if child_obj not in processed_obj:
                objects.append(child_obj)

        processed_obj.add(obj)


def scan_objs(context, objects):
    processed_obj = set()

    # collect exported objects
    scan_obj(context, objects, processed_obj)

    roots = []    # root-objects

    # get root-objects
    for obj in objects:
        if obj.xray.isroot and obj.name in bpy.context.scene.objects:
            roots.append(obj)

    # get root-object by active object
    if not roots:
        active_obj = bpy.context.active_object

        if active_obj and active_obj.xray.isroot:
            roots = [active_obj, ]

    return roots


def get_root_objs(context):
    # returns a list of root-objects

    # list of objects that need to be scanned
    objects = [obj for obj in bpy.context.selected_objects]

    roots = scan_objs(context, objects)

    return roots


def find_root(context, obj):
    objs = [obj, ]
    roots = scan_objs(context, objs)

    if len(roots) == 1:
        return roots[0]


def create_object(name, data, link=True):
    bpy_object = bpy.data.objects.new(name, data)
    stats.created_obj()

    if link:
        version.link_object(bpy_object)

    return bpy_object


def get_armature_object(bpy_obj):
    armature = None
    arm_mods = []    # armature modifiers

    # collect armature modifiers
    for modifier in bpy_obj.modifiers:
        if modifier.type == 'ARMATURE' and modifier.object:
            arm_mods.append(modifier)

    # one armature case
    if len(arm_mods) == 1:
        modifier = arm_mods[0]
        if not modifier.show_viewport:
            log.warn(
                text.warn.object_arm_mod_disabled,
                object=bpy_obj.name,
                modifier=modifier.name
            )
        armature = modifier.object

    # many armatures
    elif len(arm_mods) > 1:

        # collect used armature modifiers
        used_mods = []
        for modifier in arm_mods:
            if modifier.show_viewport:
                used_mods.append(modifier)

        if len(used_mods) > 1:
            raise log.AppError(
                text.error.object_many_arms,
                log.props(
                    object=bpy_obj.name,
                    armature_objects=[mod.object.name for mod in used_mods],
                    armature_modifiers=[mod.name for mod in used_mods]
                )
            )
        else:
            armature = used_mods[0].object

    return armature


def apply_obj_modifier(mod, context=None):
    try:
        if context:
            bpy.ops.object.modifier_apply(context, modifier=mod.name)
        else:
            bpy.ops.object.modifier_apply(modifier=mod.name)

    except RuntimeError as err:
        # modifier is disabled, skipping apply
        pass
