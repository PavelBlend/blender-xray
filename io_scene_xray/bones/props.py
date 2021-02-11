import bpy


# import props
def prop_import_bone_properties():
    return bpy.props.BoolProperty(
        name='Import Bone Properties', default=True
    )
