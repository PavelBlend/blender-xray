# standart modules
import time
import os

# blender modules
import bpy

# addon modules
from . import utility
from .. import utils
from .. import obj
from .. import details
from .. import text
from .. import version_utils
from .. import ops


# details properties

slots_meshes_props = {
    'mesh_0': bpy.props.StringProperty(),
    'mesh_1': bpy.props.StringProperty(),
    'mesh_2': bpy.props.StringProperty(),
    'mesh_3': bpy.props.StringProperty()
}


class XRayObjectDetailsSlotsMeshesProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in slots_meshes_props.items():
            exec('{0} = slots_meshes_props.get("{0}")'.format(prop_name))


slots_lighting_props = {
    'format': bpy.props.EnumProperty(
        name='Format',
        items=(
            (
                'builds_1569-cop',
                'Builds 1569-CoP',
                'level.details version 3 (builds 1569-CoP)'
            ),
            (
                'builds_1096-1558',
                'Builds 1096-1558',
                'level.details version 2 (builds 1096-1558)'
            )
        ),
        default='builds_1569-cop'
    ),
    'lights_image': bpy.props.StringProperty(),
    'hemi_image': bpy.props.StringProperty(),
    'shadows_image': bpy.props.StringProperty()
}


class XRayObjectDetailsSlotsLightingProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in slots_lighting_props.items():
            exec('{0} = slots_lighting_props.get("{0}")'.format(prop_name))


slots_props = {
    'meshes': bpy.props.PointerProperty(
        type=XRayObjectDetailsSlotsMeshesProperties
    ),
    'ligthing': bpy.props.PointerProperty(
        type=XRayObjectDetailsSlotsLightingProperties
    ),
    'meshes_object': bpy.props.StringProperty(),
    'slots_base_object': bpy.props.StringProperty(),
    'slots_top_object': bpy.props.StringProperty()
}


class XRayObjectDetailsSlotsProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in slots_props.items():
            exec('{0} = slots_props.get("{0}")'.format(prop_name))


def _update_detail_color_by_index(self, context):

    if hasattr(context.object, 'xray'):
        color_indices = details.utility.generate_color_indices()

        context.object.xray.detail.model.color = \
            color_indices[context.object.xray.detail.model.index][0 : 3]


model_props = {
    'no_waving': bpy.props.BoolProperty(
        description='No Waving',
        options={'SKIP_SAVE'},
        default=False
    ),
    'min_scale': bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0),
    'max_scale': bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0),
    'index': bpy.props.IntProperty(
        default=0,
        min=0,
        max=62,
        update=_update_detail_color_by_index
    ),
    'color': bpy.props.FloatVectorProperty(
        default=(1.0, 0.0, 0.0),
        max=1.0,
        min=0.0,
        subtype='COLOR_GAMMA',
        size=3
    )
}


class XRayObjectDetailsModelProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in model_props.items():
            exec('{0} = model_props.get("{0}")'.format(prop_name))


details_props = {
    'model': bpy.props.PointerProperty(type=XRayObjectDetailsModelProperties),
    'slots': bpy.props.PointerProperty(type=XRayObjectDetailsSlotsProperties)
}


class XRayObjectDetailsProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in details_props.items():
            exec('{0} = details_props.get("{0}")'.format(prop_name))


def _gen_time_prop(prop, description=''):
    fmt = '%Y.%m.%d %H:%M'
    fmt_day = '%Y.%m.%d'

    def getter(self):
        tval = getattr(self, prop)
        return time.strftime(fmt, time.localtime(tval)) if tval else ''

    def setter(self, value):
        value = value.strip()
        tval = 0
        if value:
            ptime = None
            try:
                ptime = time.strptime(value, fmt)
            except ValueError:
                try:
                    ptime = time.strptime(value, fmt_day)
                except ValueError:
                    pass
            if ptime:
                tval = time.mktime(ptime)
        setattr(self, prop, int(tval))

    return bpy.props.StringProperty(
        description=description,
        get=getter, set=setter,
        options={'SKIP_SAVE'}
    )


def update_motion_collection_index(self, context):
    scene = context.scene
    obj = context.object
    xray = obj.xray

    if not xray.play_active_motion:
        return

    motion_name = xray.motions_collection[xray.motions_collection_index].name

    if not bpy.data.actions.get(motion_name):
        return

    armatures = []

    def find_armature(obj):
        for child in obj.children:
            if child.type == 'ARMATURE':
                armatures.append(child)
            find_armature(child)

    arm_obj = None
    if obj.type != 'ARMATURE':
        find_armature(obj)
        if len(armatures) == 1:
            arm_obj = armatures[0]
    else:
        arm_obj = obj

    if arm_obj:
        motion = bpy.data.actions[motion_name]
        scene.frame_start = int(motion.frame_range[0])
        scene.frame_end = int(motion.frame_range[1])
        scene.frame_set(int(motion.frame_range[0]))

        if xray.dependency_object:
            dependency = bpy.data.objects.get(xray.dependency_object)
            if dependency:
                anim_data = dependency.animation_data_create()
                anim_data.action = motion
        else:
            anim_data = arm_obj.animation_data_create()
            anim_data.action = motion


object_type_items = (
    ('LEVEL', 'Level', ''),
    ('VISUAL', 'Visual', ''),
    ('PORTAL', 'Portal', ''),
    ('LIGHT_DYNAMIC', 'Light Dynamic', ''),
    ('CFORM', 'CForm', '')
)
visual_type_items = (
    ('NORMAL', 'Normal', ''),
    ('HIERRARHY', 'Hierrarhy', ''),
    ('PROGRESSIVE', 'Progressive', ''),
    ('TREE_ST', 'Tree Static', ''),
    ('TREE_PM', 'Tree Progressive', ''),
    ('LOD', 'LoD', '')
)


xray_object_level_properties = {
    'object_type': bpy.props.EnumProperty(name='Type', items=object_type_items, default='VISUAL'),
    'visual_type': bpy.props.EnumProperty(name='Visual Type', items=visual_type_items, default='NORMAL'),
    'source_path': bpy.props.StringProperty(name='Source Level Path', subtype='DIR_PATH'),
    # Tree Color Scale
    'color_scale_rgb': bpy.props.FloatVectorProperty(name='Light', min=0.0, max=1.0, subtype='COLOR'),
    'color_scale_hemi': bpy.props.FloatVectorProperty(name='Hemi', min=0.0, max=1.0, subtype='COLOR'),
    'color_scale_sun': bpy.props.FloatVectorProperty(name='Sun', min=0.0, max=1.0, subtype='COLOR'),
    # Tree Color Bias
    'color_bias_rgb': bpy.props.FloatVectorProperty(name='Light', min=0.0, max=1.0, subtype='COLOR'),
    'color_bias_hemi': bpy.props.FloatVectorProperty(name='Hemi', min=0.0, max=1.0, subtype='COLOR'),
    'color_bias_sun': bpy.props.FloatVectorProperty(name='Sun', min=0.0, max=1.0, subtype='COLOR'),
    # Portal Properties
    'sector_front': bpy.props.StringProperty(name='Sector Front'),
    'sector_back': bpy.props.StringProperty(name='Sector Back'),
    # Light Dynamic Properties
    'controller_id': bpy.props.IntProperty(name='Controller ID'),
    'light_type': bpy.props.IntProperty(name='Light Type'),
    'diffuse': bpy.props.FloatVectorProperty(
        name='Diffuse', min=0, max=1, subtype='COLOR', size=4
    ),
    'specular': bpy.props.FloatVectorProperty(
        name='Specular', min=0, max=1, subtype='COLOR', size=4
    ),
    'ambient': bpy.props.FloatVectorProperty(
        name='Ambient', min=0, max=1, subtype='COLOR', size=4
    ),
    'range_': bpy.props.FloatProperty(name='Range'),
    'falloff': bpy.props.FloatProperty(name='Falloff'),
    'attenuation_0': bpy.props.FloatProperty(name='Attenuation 0'),
    'attenuation_1': bpy.props.FloatProperty(name='Attenuation 1'),
    'attenuation_2': bpy.props.FloatProperty(name='Attenuation 2'),
    'theta': bpy.props.FloatProperty(name='Theta'),
    'phi': bpy.props.FloatProperty(name='Phi'),
    'use_fastpath': bpy.props.BoolProperty(name='Use Fastpath Geometry', default=True)
}


class XRayObjectLevelProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in xray_object_level_properties.items():
            exec('{0} = xray_object_level_properties.get("{0}")'.format(prop_name))


xray_object_revision_properties = {
    'owner': bpy.props.StringProperty(name='owner'),
    'ctime': bpy.props.IntProperty(name='ctime'),
    'ctime_str': _gen_time_prop('ctime', description='Creation time'),
    'moder': bpy.props.StringProperty(name='moder'),
    'mtime': bpy.props.IntProperty(name='mtime')
}


class XRayObjectRevisionProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in xray_object_revision_properties.items():
            exec('{0} = xray_object_revision_properties.get("{0}")'.format(prop_name))


def find_duplicate_name(motion, used_names):
    if used_names.count(motion.export_name):
        for name in used_names:
            if motion.export_name == name:
                if len(motion.export_name) >= 4:
                    if motion.export_name[-4] == '.' and motion.export_name[-3:].isdigit():
                        number = int(motion.export_name[-3 : ]) + 1
                        motion.export_name = motion.export_name[ : -3] + '{:0>3}'.format(number)
                    else:
                        motion.export_name += '.001'
                else:
                    motion.export_name += '.001'


def update_export_name(self, context):
    data = context.object.xray

    if not self.export_name:
        return

    used_names = []
    for motion in data.motions_collection:
        if motion != self:
            used_names.append(motion.export_name)

    find_duplicate_name(self, used_names)

    used_names = []
    for motion in data.motions_collection:
        if motion != self and not motion.export_name:
            used_names.append(motion.name)

    find_duplicate_name(self, used_names)


def load_motion_refs(self, context):
    if not self.load_active_motion_refs:
        return
    if self.motionrefs_collection:
        objects_folder = version_utils.get_preferences().objects_folder_auto
        motion_refs = self.motionrefs_collection[self.motionrefs_collection_index]
        file_path = os.path.join(objects_folder, motion_refs.name + os.extsep + 'skls')
        if os.path.exists(file_path):
            ops.skls_browser.init_skls_browser(self, context, file_path)
        else:
            message = text.get_text(text.error.file_not_found).capitalize()
            def show_motion_refs_error(self, context):
                self.layout.label(text=message + ':')
                self.layout.label(text=' ' * 4 + file_path)
            bpy.context.window_manager.popup_menu(
                show_motion_refs_error,
                title='Error',
                icon='ERROR'
            )


def update_load_active_motion_refs(self, context):
    if not context.active_object:
        return
    if not hasattr(context.active_object.data, 'bones'):
        return
    if not self.load_active_motion_refs:
        bpy.ops.xray.close_skls_file()


motion_ref_props = {
    'name': bpy.props.StringProperty(),
    'export_name': bpy.props.StringProperty(update=update_export_name)
}


class MotionRef(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in motion_ref_props.items():
            exec('{0} = motion_ref_props.get("{0}")'.format(prop_name))


def get_isroot(self):
    if not self.root:
        return False
    if utils.is_helper_object(self.id_data):
        return False
    if self.id_data.parent:
        return not self.id_data.parent.xray.isroot
    return True


def set_isroot(self, value):
    if self.id_data.parent:
        self.id_data.parent.xray.isroot = not value
    self.root = value


def set_custom_type(self, value):
    self.flags = self.flags | 0x1 if value else self.flags & ~0x1
    self.flags_force_custom = True


def userdata_update(self, context):
    if self.userdata == '':
        self.show_userdata = False


_flags_simple_inv_map = [
    None,  # other
    0x20,  # sound occluder
    0x14,  # multi. usage
    0x08,  # hom
    0x03,  # dynamic progressive
    0x01,  # dynamic
    0x00   # static
]
_flags_simple_map = {v: k for k, v in enumerate(_flags_simple_inv_map)}


def flags_simple_get(self):
    if self.flags_force_custom:
        return 0
    return _flags_simple_map.get(self.flags & ~0x40, 0)


def flags_simple_set(self, value):
    self.flags_force_custom = value == 0
    if value != 0:  # !custom
        if self.flags_custom_hqexp:
            self.flags = _flags_simple_inv_map[value] | 0x40
        else:
            self.flags = _flags_simple_inv_map[value] & ~0x40


xray_object_properties = {
    'root': bpy.props.BoolProperty(default=True),    # default=True - to backward compatibility
    'isroot': bpy.props.BoolProperty(get=get_isroot, set=set_isroot, options={'SKIP_SAVE'}),
    'is_details': bpy.props.BoolProperty(default=False),
    'is_level': bpy.props.BoolProperty(default=False),
    'version': bpy.props.IntProperty(),
    'flags': bpy.props.IntProperty(name='flags'),
    'flags_force_custom': bpy.props.BoolProperty(options={'SKIP_SAVE'}),
    'flags_use_custom': bpy.props.BoolProperty(
        options={'SKIP_SAVE'},
        get=lambda self: self.flags_force_custom or not (self.flags & ~0x40 in _flags_simple_map)
    ),
    'flags_custom_type': bpy.props.EnumProperty(
        name='Custom Object Type',
        items=(
            ('st', 'Static', ''),
            ('dy', 'Dynamic', '')
        ),
        options={'SKIP_SAVE'},
        get=lambda self: self.flags & 0x1, set=set_custom_type
    ),
    'flags_custom_progressive': utility.gen_flag_prop(
        mask=0x02,
        description='Make Progressive',
        customprop='flags_force_custom'
    ),
    'flags_custom_lod': utility.gen_flag_prop(
        mask=0x04,
        description='Using LOD',
        customprop='flags_force_custom'
    ),
    'flags_custom_hom': utility.gen_flag_prop(
        mask=0x08,
        description='Hierarchical Occlusion Mapping',
        customprop='flags_force_custom'
    ),
    'flags_custom_musage': utility.gen_flag_prop(
        mask=0x10,
        customprop='flags_force_custom'
    ),
    'flags_custom_soccl': utility.gen_flag_prop(
        mask=0x20,
        customprop='flags_force_custom'
    ),
    'flags_custom_hqexp': utility.gen_flag_prop(
        mask=0x40,
        description='HQ Geometry',
        customprop=''
    ),
    'flags_simple': bpy.props.EnumProperty(name='Object Type', items=(
        (obj.fmt.CM, obj.fmt.type_names[obj.fmt.CM], ''),
        (obj.fmt.SO, obj.fmt.type_names[obj.fmt.SO], ''),
        (obj.fmt.MU, obj.fmt.type_names[obj.fmt.MU], ''),
        (obj.fmt.HO, obj.fmt.type_names[obj.fmt.HO], 'Hierarchical Occlusion Mapping'),
        (obj.fmt.PD, obj.fmt.type_names[obj.fmt.PD], ''),
        (obj.fmt.DY, obj.fmt.type_names[obj.fmt.DY], ''),
        (obj.fmt.ST, obj.fmt.type_names[obj.fmt.ST], '')
    ), options={'SKIP_SAVE'}, get=flags_simple_get, set=flags_simple_set),
    'lodref': bpy.props.StringProperty(name='LOD Reference'),
    'userdata': bpy.props.StringProperty(name='userdata', update=userdata_update),
    'show_userdata': bpy.props.BoolProperty(description='View user data', options={'SKIP_SAVE'}),
    'revision': bpy.props.PointerProperty(type=XRayObjectRevisionProperties),
    'load_active_motion_refs': bpy.props.BoolProperty(
        name='Load Active Motion Refs', default=False,
        update=update_load_active_motion_refs
    ),
    'motionrefs': bpy.props.StringProperty(
        description='!Legacy: use \'motionrefs_collection\' instead'
    ),
    'motionrefs_collection': bpy.props.CollectionProperty(type=MotionRef),
    'motionrefs_collection_index': bpy.props.IntProperty(
        options={'SKIP_SAVE'}, update=load_motion_refs
    ),
    'show_motionsrefs': bpy.props.BoolProperty(description='View motion refs', options={'SKIP_SAVE'}),

    'motions': bpy.props.StringProperty(
        description='!Legacy: use \'motions_collection\' instead'
    ),
    'motions_collection': bpy.props.CollectionProperty(type=MotionRef),
    'motions_collection_index': bpy.props.IntProperty(
        options={'SKIP_SAVE'}, update=update_motion_collection_index
    ),
    'show_motions': bpy.props.BoolProperty(description='View motions', options={'SKIP_SAVE'}),
    'play_active_motion': bpy.props.BoolProperty(name='Play Active Motion', default=False),
    'dependency_object': bpy.props.StringProperty(name='Dependency', default=''),
    'use_custom_motion_names': bpy.props.BoolProperty(name='Custom Names', default=False),
    'helper_data': bpy.props.StringProperty(),
    'export_path': bpy.props.StringProperty(
        name='Export Path',
        description='Path relative to the root export folder'
    ),
    'detail': bpy.props.PointerProperty(
        type=XRayObjectDetailsProperties
    ),
    'skls_browser': bpy.props.PointerProperty(type=ops.skls_browser.XRayObjectSklsBrowserProperties),
    'level': bpy.props.PointerProperty(type=XRayObjectLevelProperties),
    # transforms utils properties
    'position': bpy.props.FloatVectorProperty(
        name='Position', precision=3, subtype='TRANSLATION'
    ),
    'orientation': bpy.props.FloatVectorProperty(
        name='Orientation', precision=3, subtype='EULER'
    )
}


class XRayObjectProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Object

    if not version_utils.IS_28:
        for prop_name, prop_value in xray_object_properties.items():
            exec('{0} = xray_object_properties.get("{0}")'.format(prop_name))

    def initialize(self, context):
        if not self.version:
            if context.operation == 'LOADED':
                self.version = -1
            elif context.operation == 'CREATED':
                self.version = context.plugin_version_number
                self.root = context.thing.type == 'MESH'
                if context.thing.type == 'ARMATURE':
                    context.thing.data.xray.joint_limits_type = 'XRAY'


prop_groups = (
    (XRayObjectDetailsSlotsMeshesProperties, slots_meshes_props, False),
    (XRayObjectDetailsSlotsLightingProperties, slots_lighting_props, False),
    (XRayObjectDetailsSlotsProperties, slots_props, False),
    (XRayObjectDetailsModelProperties, model_props, False),
    (XRayObjectDetailsProperties, details_props, False),
    (XRayObjectLevelProperties, xray_object_level_properties, False),
    (XRayObjectRevisionProperties, xray_object_revision_properties, False),
    (MotionRef, motion_ref_props, False),
    (XRayObjectProperties, xray_object_properties, True)
)


def register():
    for prop_group, props, is_group in prop_groups:
        version_utils.assign_props([
            (props, prop_group),
        ])
        bpy.utils.register_class(prop_group)
        if is_group:
            prop_group.b_type.xray = bpy.props.PointerProperty(type=prop_group)


def unregister():
    for prop_group, props, is_group in reversed(prop_groups):
        if is_group:
            del prop_group.b_type.xray
        bpy.utils.unregister_class(prop_group)
