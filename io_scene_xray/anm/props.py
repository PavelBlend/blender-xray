# blender modules
import bpy


def PropAnmCameraAnimation():
    return bpy.props.BoolProperty(
        name='Create Linked Camera',
        description='Create animated camera object (linked to "empty"-object)',
        default=True
    )
