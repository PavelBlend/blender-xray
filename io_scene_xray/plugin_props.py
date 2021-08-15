# blender modules
import bpy


class BaseOperator(bpy.types.Operator):
    report_catcher = None

    def __getattribute__(self, item):
        if (item == 'report') and (self.report_catcher is not None):
            return self.report_catcher
        return super().__getattribute__(item)


def PropObjectTextureNamesFromPath():
    return bpy.props.BoolProperty(
        name='Texture Names from Image Paths',
        description='Generate texture names from image paths ' \
        + '(by subtract <gamedata/textures> prefix and <file-extension> suffix)',
        default=True
    )


def PropSDKVersion():
    return bpy.props.EnumProperty(
        name='SDK Version',
        items=(
            ('soc', 'SoC', ''),
            ('cscop', 'CS/CoP', '')
        )
    )


def PropObjectMotionsExport():
    return bpy.props.BoolProperty(
        name='Export Motions',
        description='Export armatures actions as embedded motions',
        default=True
    )


def PropUseExportPaths():
    return bpy.props.BoolProperty(
        name='Use Export Paths',
        description='Append the Object.ExportPath to the export directory for each object',
        default=True
    )


items = (
    ('SHARP_EDGES', 'Sharp Edges', ''),
    ('SPLIT_NORMALS', 'Split Normals', '')
)


def prop_smoothing_out_of():
    return bpy.props.EnumProperty(
        name='Smoothing Out of',
        description='',
        default='SHARP_EDGES',
        items=items
    )


def PropObjectMotionsImport():
    return bpy.props.BoolProperty(
        name='Import Motions',
        description='Import embedded motions as actions',
        default=True
    )


def PropObjectMeshSplitByMaterials():
    return bpy.props.BoolProperty(
        name='Split Mesh by Materials',
        description='Import each surface (material) as separate set of faces',
        default=False
    )


def PropObjectBonesCustomShapes():
    return bpy.props.BoolProperty(
        name='Custom Shapes for Bones',
        description='Use custom shapes for imported bones',
        default=True
    )


def PropObjectUseMotionPrefixName():
    return bpy.props.BoolProperty(default=False, name='Motion Prefix Name')


def prop_skl_add_actions_to_motion_list():
    return bpy.props.BoolProperty(default=True, name='Add Actions to Motion List')


def PropAnmCameraAnimation():
    return bpy.props.BoolProperty(
        name='Create Linked Camera',
        description='Create animated camera object (linked to "empty"-object)',
        default=True
    )


def prop_import_bone_properties():
    return bpy.props.BoolProperty(
        name='Import Bone Properties', default=True
    )


def prop_export_bone_properties():
    return bpy.props.BoolProperty(
        name='Export Bone Properties', default=True
    )


def prop_details_models_in_a_row():
    return bpy.props.BoolProperty(name='Models in Row', default=True)


def prop_details_load_slots():
    return bpy.props.BoolProperty(name='Load Slots', default=True)


def prop_details_format():
    return bpy.props.EnumProperty(
        name='Details Format',
        items=(
            ('builds_1096-1230', 'Builds 1096-1230', ''),
            ('builds_1233-1558', 'Builds 1233-1558', '')
        )
    )


def prop_details_format_version():
    return bpy.props.EnumProperty(
        name='Format',
        items=(
            ('builds_1569-cop', 'Builds 1569-CoP', ''),
            ('builds_1233-1558', 'Builds 1233-1558', ''),
            ('builds_1096-1230', 'Builds 1096-1230', '')
        ),
        default='builds_1569-cop'
    )


def prop_import_bone_parts():
    return bpy.props.BoolProperty(
        name='Import Bone Parts', default=False
    )


def prop_export_bone_parts():
    return bpy.props.BoolProperty(
        name='Export Bone Parts', default=False
    )


export_mode_items = (
    ('OVERWRITE', 'Overwrite', ''),
    ('ADD', 'Add', ''),
    ('REPLACE', 'Replace', '')
)


def prop_omf_export_mode():
    return bpy.props.EnumProperty(
        name='Export Mode', items=export_mode_items
    )
