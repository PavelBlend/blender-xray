# standart modules
import time
import os

# blender modules
import bpy

# addon modules
from . import utility
from .. import utils
from .. import formats
from .. import text
from .. import ops


# details properties

class XRayObjectDetailsSlotsMeshesProperties(bpy.types.PropertyGroup):
    mesh_0 = bpy.props.StringProperty()
    mesh_1 = bpy.props.StringProperty()
    mesh_2 = bpy.props.StringProperty()
    mesh_3 = bpy.props.StringProperty()


class XRayObjectDetailsSlotsLightingProperties(bpy.types.PropertyGroup):
    format = bpy.props.EnumProperty(
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
    )
    lights_image = bpy.props.StringProperty()
    hemi_image = bpy.props.StringProperty()
    shadows_image = bpy.props.StringProperty()


class XRayObjectDetailsSlotsProperties(bpy.types.PropertyGroup):
    meshes = bpy.props.PointerProperty(
        type=XRayObjectDetailsSlotsMeshesProperties
    )
    ligthing = bpy.props.PointerProperty(
        type=XRayObjectDetailsSlotsLightingProperties
    )
    meshes_object = bpy.props.StringProperty()
    slots_base_object = bpy.props.StringProperty()
    slots_top_object = bpy.props.StringProperty()


def _update_detail_color_by_index(self, context):
    ob = context.active_object

    if not ob:
        return

    color_indices = formats.details.utility.generate_color_indices()
    xray = ob.xray
    xray.detail.model.color = color_indices[xray.detail.model.index][0 : 3]


class XRayObjectDetailsModelProperties(bpy.types.PropertyGroup):
    no_waving = bpy.props.BoolProperty(
        description='No Waving',
        options={'SKIP_SAVE'},
        default=False
    )
    min_scale = bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0)
    max_scale = bpy.props.FloatProperty(default=1.0, min=0.1, max=100.0)
    index = bpy.props.IntProperty(
        default=0,
        min=0,
        max=62,
        update=_update_detail_color_by_index
    )
    color = bpy.props.FloatVectorProperty(
        default=(1.0, 0.0, 0.0),
        max=1.0,
        min=0.0,
        subtype='COLOR_GAMMA',
        size=3
    )


class XRayObjectDetailsProperties(bpy.types.PropertyGroup):
    model = bpy.props.PointerProperty(type=XRayObjectDetailsModelProperties)
    slots = bpy.props.PointerProperty(type=XRayObjectDetailsSlotsProperties)


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
    obj = context.active_object
    xray = obj.xray

    if not xray.play_active_motion:
        return

    motion_index = xray.motions_collection_index
    motion_name = xray.motions_collection[motion_index].name

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
        act = bpy.data.actions[motion_name]

        start_frm = int(act.frame_range[0])
        end_frm = int(act.frame_range[1])

        scene.frame_start = start_frm
        scene.frame_end = end_frm
        scene.frame_set(start_frm)

        scene.use_preview_range = False

        dep_obj_name = xray.dependency_object
        if dep_obj_name:
            dep_obj = bpy.data.objects.get(dep_obj_name)
            if dep_obj:
                anim_data = dep_obj.animation_data_create()
                anim_data.action = act
        else:
            anim_data = arm_obj.animation_data_create()
            anim_data.action = act


def get_color_prop(name, size):
    return bpy.props.FloatVectorProperty(
        name=name,
        min=0.0,
        max=1.0,
        subtype='COLOR',
        size=size
    )


def _update_light_type_name(self, context):
    self.light_type = int(self.light_type_name)


def _update_controller_name(self, context):
    self.controller_id = int(self.controller_name)


object_type_items = (
    ('LEVEL', 'Level ', ''),
    ('VISUAL', 'Visual', ''),
    ('PORTAL', 'Portal', ''),
    ('LIGHT_DYNAMIC', 'Light', ''),
    ('CFORM', 'CForm', '')
)
visual_type_items = (
    ('NORMAL', 'Normal ', ''),
    ('HIERRARHY', 'Hierrarhy', ''),
    ('PROGRESSIVE', 'Progressive', ''),
    ('TREE_ST', 'Tree Static', ''),
    ('TREE_PM', 'Tree Progressive', ''),
    ('LOD', 'LoD', '')
)

POINT_NAME = 'Point'
SPOT_NAME = 'Spot'
DIRECT_NAME = 'Directional'


class XRayObjectLevelProperties(bpy.types.PropertyGroup):
    # general
    object_type = bpy.props.EnumProperty(
        name='Type',
        items=object_type_items,
        default='VISUAL'
    )

    # level
    sectors_obj = bpy.props.StringProperty(name='Sectors Object')
    portals_obj = bpy.props.StringProperty(name='Portals Object')
    lights_obj = bpy.props.StringProperty(name='Lights Object')
    glows_obj = bpy.props.StringProperty(name='Glows Object')

    # visual
    visual_type = bpy.props.EnumProperty(
        name='Visual Type',
        items=visual_type_items,
        default='NORMAL'
    )
    use_fastpath = bpy.props.BoolProperty(
        name='Use Fastpath Geometry',
        default=True
    )

    # tree color scale
    color_scale_rgb = get_color_prop('Light', 3)
    color_scale_hemi = get_color_prop('Hemi', 3)
    color_scale_sun = get_color_prop('Sun', 3)

    # tree color bias
    color_bias_rgb = get_color_prop('Light', 3)
    color_bias_hemi = get_color_prop('Hemi', 3)
    color_bias_sun = get_color_prop('Sun', 3)

    # portal
    sector_front = bpy.props.StringProperty(name='Sector Front')
    sector_back = bpy.props.StringProperty(name='Sector Back')

    # light
    controller_id = bpy.props.IntProperty(name='Controller ID')
    controller_name = bpy.props.EnumProperty(
        name='Controller',
        items=(
            ('2', 'Static', ''),
            ('0', 'Hemi', ''),
            ('1', 'Sun', '')
        ),
        update=_update_controller_name
    )
    light_type = bpy.props.IntProperty(
        name='Light Type',
        default=1,
        min=1,
        max=3,
        soft_min=1,
        soft_max=3
    )
    light_type_name = bpy.props.EnumProperty(
        name='Light Type',
        items=(
            (str(formats.level.fmt.D3D_LIGHT_POINT), POINT_NAME, ''),
            (str(formats.level.fmt.D3D_LIGHT_SPOT), SPOT_NAME, ''),
            (str(formats.level.fmt.D3D_LIGHT_DIRECTIONAL), DIRECT_NAME, '')
        ),
        update=_update_light_type_name
    )
    diffuse = get_color_prop('Diffuse', size=4)
    specular = get_color_prop('Specular', size=4)
    ambient = get_color_prop('Ambient', size=4)
    range_ = bpy.props.FloatProperty(name='Cutoff Range')
    falloff = bpy.props.FloatProperty(name='Falloff')
    attenuation_0 = bpy.props.FloatProperty(name='Constant Attenuation')
    attenuation_1 = bpy.props.FloatProperty(name='Linear Attenuation')
    attenuation_2 = bpy.props.FloatProperty(name='Quadratic Attenuation')
    theta = bpy.props.FloatProperty(name='Inner Angle Theta')
    phi = bpy.props.FloatProperty(name='Outer Angle Phi')


class XRayObjectRevisionProperties(bpy.types.PropertyGroup):
    owner = bpy.props.StringProperty(name='owner')
    ctime = bpy.props.IntProperty(name='ctime')
    ctime_str = _gen_time_prop('ctime', description='Creation time')
    moder = bpy.props.StringProperty(name='moder')
    mtime = bpy.props.IntProperty(name='mtime')
    mtime_str = _gen_time_prop('mtime', description='Modified time')


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
    data = context.active_object.xray

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


def _get_motions_folder(prop):
    folders = utils.ie.get_pref_paths(prop)

    for folder in folders:

        if not folder:
            continue

        if not os.path.exists(folder):
            continue

        return folder


def load_motion_refs(self, context):
    if not self.load_active_motion_refs:
        return

    if self.motionrefs_collection:
        obj = context.active_object
        motion_refs = self.motionrefs_collection[self.motionrefs_collection_index]

        if obj.xray.motions_browser.file_format == 'SKLS':
            folder = _get_motions_folder('objects_folder')
            ext = os.extsep + 'skls'
            message = text.get_text(text.warn.objs_folder_not_spec)

        else:
            folder = _get_motions_folder('meshes_folder')
            ext = os.extsep + 'omf'
            message = text.get_text(text.warn.meshes_folder_not_spec)

        if not folder:
            utils.draw.show_message(
                message,
                (),
                text.get_text(text.error.error_title),
                'ERROR'
            )
            return

        file_path = os.path.join(folder, motion_refs.name + ext)

        if os.path.exists(file_path):
            ops.motions_browser.init_browser(self, context, file_path)
            return

        message = text.get_text(text.error.file_not_found)
        utils.draw.show_message(
            message,
            (file_path, ),
            text.get_text(text.error.error_title),
            'ERROR'
        )


def update_load_active_motion_refs(self, context):
    if not context.active_object:
        return
    if not hasattr(context.active_object.data, 'bones'):
        return
    if not self.load_active_motion_refs:
        bpy.ops.xray.close_motions_file()


class MotionRef(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    export_name = bpy.props.StringProperty(update=update_export_name)


def get_isroot(self):
    if not self.root:
        return False
    if utils.obj.is_helper_object(self.id_data):
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


class XRayObjectProperties(utility.InitPropGroup):
    b_type = bpy.types.Object

    # default=True - to backward compatibility
    root = bpy.props.BoolProperty(default=True)
    isroot = bpy.props.BoolProperty(
        get=get_isroot,
        set=set_isroot,
        options={'SKIP_SAVE'}
    )
    is_details = bpy.props.BoolProperty(default=False)
    is_level = bpy.props.BoolProperty(default=False)
    version = bpy.props.IntProperty()

    flags = bpy.props.IntProperty(name='flags')
    flags_force_custom = bpy.props.BoolProperty(options={'SKIP_SAVE'})
    flags_use_custom = bpy.props.BoolProperty(
        options={'SKIP_SAVE'},
        get=lambda self: self.flags_force_custom or not (self.flags & ~0x40 in _flags_simple_map)
    )
    flags_custom_type = bpy.props.EnumProperty(
        name='Custom Object Type',
        items=(
            ('st', 'Static', ''),
            ('dy', 'Dynamic', '')
        ),
        options={'SKIP_SAVE'},
        get=lambda self: self.flags & 0x1, set=set_custom_type
    )
    flags_custom_progressive = utility.gen_flag_prop(
        mask=0x02,
        description='Make Progressive',
        custom_prop='flags_force_custom'
    )
    flags_custom_lod = utility.gen_flag_prop(
        mask=0x04,
        description='Using LOD',
        custom_prop='flags_force_custom'
    )
    flags_custom_hom = utility.gen_flag_prop(
        mask=0x08,
        description='Hierarchical Occlusion Mapping',
        custom_prop='flags_force_custom'
    )
    flags_custom_musage = utility.gen_flag_prop(
        mask=0x10,
        custom_prop='flags_force_custom'
    )
    flags_custom_soccl = utility.gen_flag_prop(
        mask=0x20,
        custom_prop='flags_force_custom'
    )
    flags_custom_hqexp = utility.gen_flag_prop(
        mask=0x40,
        description='HQ Geometry',
        custom_prop=''
    )
    flags_simple = bpy.props.EnumProperty(
        name='Object Type',
        items=(
            (formats.obj.fmt.CM, formats.obj.fmt.type_names[formats.obj.fmt.CM], ''),
            (formats.obj.fmt.SO, formats.obj.fmt.type_names[formats.obj.fmt.SO], ''),
            (formats.obj.fmt.MU, formats.obj.fmt.type_names[formats.obj.fmt.MU], ''),
            (formats.obj.fmt.HO, formats.obj.fmt.type_names[formats.obj.fmt.HO], 'Hierarchical Occlusion Mapping'),
            (formats.obj.fmt.PD, formats.obj.fmt.type_names[formats.obj.fmt.PD], ''),
            (formats.obj.fmt.DY, formats.obj.fmt.type_names[formats.obj.fmt.DY], ''),
            (formats.obj.fmt.ST, formats.obj.fmt.type_names[formats.obj.fmt.ST], '')
        ),
        options={'SKIP_SAVE'},
        get=flags_simple_get,
        set=flags_simple_set
    )

    lodref = bpy.props.StringProperty(name='LOD Reference')
    userdata = bpy.props.StringProperty(name='userdata', update=userdata_update)
    show_userdata = bpy.props.BoolProperty(description='View user data', options={'SKIP_SAVE'})
    revision = bpy.props.PointerProperty(type=XRayObjectRevisionProperties)
    load_active_motion_refs = bpy.props.BoolProperty(
        name='Load Active Motion Refs',
        default=False,
        update=update_load_active_motion_refs
    )
    motionrefs = bpy.props.StringProperty(
        description='!Legacy: use \'motionrefs_collection\' instead'
    )
    motionrefs_collection = bpy.props.CollectionProperty(type=MotionRef)
    motionrefs_collection_index = bpy.props.IntProperty(
        options={'SKIP_SAVE'},
        update=load_motion_refs
    )
    show_motionsrefs = bpy.props.BoolProperty(
        description='View motion refs',
        options={'SKIP_SAVE'}
    )

    motions = bpy.props.StringProperty(
        description='!Legacy: use \'motions_collection\' instead'
    )
    motions_collection = bpy.props.CollectionProperty(type=MotionRef)
    motions_collection_index = bpy.props.IntProperty(
        options={'SKIP_SAVE'},
        update=update_motion_collection_index
    )
    show_motions = bpy.props.BoolProperty(
        description='View motions',
        options={'SKIP_SAVE'}
    )
    play_active_motion = bpy.props.BoolProperty(
        name='Play Active Motion',
        default=False
    )
    show_motions_names = bpy.props.EnumProperty(
        name='Show Motions Names',
        items=(
            ('ACTION', 'Action', ''),
            ('EXPORT', ' Export ', ''),
            ('BOTH', 'Both', '')
        ),
        default='ACTION'
    )
    dependency_object = bpy.props.StringProperty(
        name='Dependency',
        default=''
    )
    use_custom_motion_names = bpy.props.BoolProperty(
        name='Custom Names',
        default=False
    )
    helper_data = bpy.props.StringProperty()
    export_path = bpy.props.StringProperty(
        name='Export Path',
        description='Path relative to the root export folder'
    )
    detail = bpy.props.PointerProperty(type=XRayObjectDetailsProperties)
    motions_browser = bpy.props.PointerProperty(
        type=ops.motions_browser.XRayMotionsBrowserProps
    )
    level = bpy.props.PointerProperty(type=XRayObjectLevelProperties)

    # transforms utils properties
    position = bpy.props.FloatVectorProperty(
        name='Position',
        precision=3,
        subtype='TRANSLATION'
    )
    orientation = bpy.props.FloatVectorProperty(
        name='Orientation',
        precision=3,
        subtype='EULER'
    )

    def _during_creation(self):
        obj = self.id_data
        self.root = obj.type == 'MESH'

        if obj.type == 'ARMATURE':
            obj.data.xray.joint_limits_type = 'XRAY'


prop_groups = (
    XRayObjectDetailsSlotsMeshesProperties,
    XRayObjectDetailsSlotsLightingProperties,
    XRayObjectDetailsSlotsProperties,
    XRayObjectDetailsModelProperties,
    XRayObjectDetailsProperties,
    XRayObjectLevelProperties,
    XRayObjectRevisionProperties,
    MotionRef,
    XRayObjectProperties
)


def register():
    utils.version.register_classes(prop_groups)


def unregister():
    utils.version.unregister_prop_groups(prop_groups)
