# blender modules
import bpy


# import props
def prop_import_bone_parts():
    return bpy.props.BoolProperty(
        name='Import Bone Parts', default=False
    )


# export props
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
