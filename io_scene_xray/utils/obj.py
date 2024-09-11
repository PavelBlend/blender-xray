# standart modules
import time
import platform
import getpass

# blender modules
import bpy

# addon modules
from . import version
from . import ie
from . import obj
from . import stats
from .. import log
from .. import text


HELPER_OBJECT_NAME_PREFIX = '.xray-helper--'

SOC_LEVEL_FOV = 67.5
COP_LEVEL_FOV = 55.0

SOC_HUD_FOV_FACTOR = 0.45
COP_HUD_FOV_FACTOR = SOC_HUD_FOV_FACTOR

SOC_HUD_FOV = SOC_LEVEL_FOV * SOC_HUD_FOV_FACTOR
COP_HUD_FOV = COP_LEVEL_FOV * COP_HUD_FOV_FACTOR


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


def get_revis(revision):
    # get revision data

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

    roots = set()    # root-objects

    # get root-objects
    for obj in objects:
        if obj.xray.isroot and obj.name in bpy.context.scene.objects:
            roots.add(obj)

    # get root-object by active object
    if not roots:
        active_obj = bpy.context.active_object

        if active_obj and active_obj.xray.isroot:
            roots = [active_obj, ]

    return list(roots)


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


def merge_meshes(mesh_objects, arm_obj):
    objects = []
    override = bpy.context.copy()

    for bpy_obj in mesh_objects:
        if not len(bpy_obj.data.uv_layers):
            raise log.AppError(
                text.error.no_uv,
                log.props(object=bpy_obj.name)
            )

        if len(bpy_obj.data.uv_layers) > 1:
            log.warn(
                text.warn.obj_many_uv,
                exported_uv=bpy_obj.data.uv_layers.active.name,
                mesh_object=bpy_obj.name
            )

        ie.validate_vertex_weights(bpy_obj, arm_obj)

        copy_obj = bpy_obj.copy()
        copy_mesh = bpy_obj.data.copy()
        copy_obj.data = copy_mesh

        # rename uv layers
        active_uv_name = copy_mesh.uv_layers.active.name
        index = 0
        for uv_layer in copy_mesh.uv_layers:
            if uv_layer.name == active_uv_name:
                continue
            uv_layer.name = str(index)
            index += 1

        copy_mesh.uv_layers.active.name = 'Texture'
        version.link_object(copy_obj)

        # apply modifiers
        override['active_object'] = copy_obj
        override['object'] = copy_obj
        for mod in copy_obj.modifiers:
            if mod.type == 'ARMATURE':
                continue
            if not mod.show_viewport:
                continue
            override['modifier'] = mod
            apply_obj_modifier(mod, context=override)
        objects.append(copy_obj)

        # apply shape keys
        if copy_mesh.shape_keys:
            copy_obj.shape_key_add(name='last_shape_key', from_mix=True)
            for shape_key in copy_mesh.shape_keys.key_blocks:
                copy_obj.shape_key_remove(shape_key)

    active_object = objects[0]
    override['active_object'] = active_object
    override['selected_objects'] = objects
    if version.IS_28:
        override['object'] = active_object
        override['selected_editable_objects'] = objects
    else:
        scene = bpy.context.scene
        override['selected_editable_bases'] = [
            scene.object_bases[ob.name]
            for ob in objects
        ]
    bpy.ops.object.join(override)

    # remove uvs
    uv_layers = [uv_layer.name for uv_layer in active_object.data.uv_layers]
    for uv_name in uv_layers:
        if uv_name == 'Texture':
            continue
        uv_layer = active_object.data.uv_layers[uv_name]
        active_object.data.uv_layers.remove(uv_layer)

    return active_object


def remove_merged_obj(merged_obj):
    if merged_obj:
        merged_mesh = merged_obj.data

        if version.IS_277:
            bpy.context.scene.objects.unlink(merged_obj)
            merged_obj.user_clear()
            bpy.data.objects.remove(merged_obj)

        else:
            bpy.data.objects.remove(merged_obj, do_unlink=True)

        bpy.data.meshes.remove(merged_mesh)
