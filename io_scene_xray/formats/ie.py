# blender modules
import bpy


# import-export properties


def prop_tex_from_path():
    return bpy.props.BoolProperty(
        name='Texture Names from Image Paths',
        description=
            'Generate texture names from image paths '
            '(by subtract <gamedata/textures> prefix and '
            '<file-extension> suffix)',
        default=True
    )


def prop_sdk_ver():
    return bpy.props.EnumProperty(
        name='SDK Version',
        items=(
            ('soc', 'SoC', ''),
            ('cscop', 'CS/CoP', '')
        )
    )


def prop_exp_motions():
    return bpy.props.BoolProperty(
        name='Export Motions',
        description='Export armatures actions as embedded motions',
        default=True
    )


def prop_exp_paths():
    return bpy.props.BoolProperty(
        name='Use Export Paths',
        description=
            'Append the Object.ExportPath to the '
            'export directory for each object',
        default=False
    )


items = (
    ('SHARP_EDGES', 'Edges', ''),
    ('SPLIT_NORMALS', 'Normals', '')
)


def prop_smooth():
    return bpy.props.EnumProperty(
        name='Smoothing Out of',
        description='',
        default='SHARP_EDGES',
        items=items
    )


def prop_imp_motions():
    return bpy.props.BoolProperty(
        name='Import Motions',
        description='Import embedded motions as actions',
        default=True
    )


def prop_split_by_mats():
    return bpy.props.BoolProperty(
        name='Split Mesh by Materials',
        description='Import each surface (material) as separate set of faces',
        default=False
    )


def prop_add_acts_to_list():
    return bpy.props.BoolProperty(
        default=True,
        name='Add Actions to Motion List'
    )


def prop_camera_anim():
    return bpy.props.BoolProperty(
        name='Create Linked Camera',
        description='Create animated camera object (linked to "empty"-object)',
        default=True
    )


def prop_anm_ver():
    return bpy.props.EnumProperty(
        name='Format Version',
        items=(
            ('3', '3', ''),
            ('4', '4', ''),
            ('5', '5', '')
        ),
        default='5'
    )


def prop_imp_bone_props():
    return bpy.props.BoolProperty(name='Import Bone Properties', default=True)


def prop_exp_bone_props():
    return bpy.props.BoolProperty(name='Export Bone Properties', default=True)


def prop_models_in_row():
    return bpy.props.BoolProperty(name='Models in Row', default=True)


def prop_load_slots():
    return bpy.props.BoolProperty(name='Import Slots', default=True)


def prop_details_fmt():
    return bpy.props.EnumProperty(
        name='Details Format',
        items=(
            ('builds_1096-1230', 'Builds 1096-1230', ''),
            ('builds_1233-1558', 'Builds 1233-1558', '')
        )
    )


def prop_details_ver():
    return bpy.props.EnumProperty(
        name='Format',
        items=(
            ('builds_1569-cop', 'Builds 1569-CoP', ''),
            ('builds_1233-1558', 'Builds 1233-1558', ''),
            ('builds_1096-1230', 'Builds 1096-1230', '')
        ),
        default='builds_1569-cop'
    )


def prop_imp_bone_parts():
    return bpy.props.BoolProperty(name='Import Bone Parts', default=False)


def prop_exp_bone_parts():
    return bpy.props.BoolProperty(name='Export Bone Parts', default=False)


export_mode_items = (
    ('OVERWRITE', 'Overwrite', ''),
    ('ADD', 'Add', ''),
    ('REPLACE', 'Replace', '')
)


def prop_exp_mode():
    return bpy.props.EnumProperty(name='Export Mode', items=export_mode_items)


def prop_high_qual():
    return bpy.props.BoolProperty(name='High Quality Motions', default=False)
