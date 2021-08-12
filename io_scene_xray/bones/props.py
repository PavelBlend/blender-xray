# blender modules
import bpy


# import props
def prop_import_bone_properties():
    return bpy.props.BoolProperty(
        name='Import Bone Properties', default=True
    )


# export props
def prop_export_bone_properties():
    return bpy.props.BoolProperty(
        name='Export Bone Properties', default=True
    )
