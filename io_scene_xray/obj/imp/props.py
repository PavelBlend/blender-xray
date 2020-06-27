import bpy


def PropObjectMotionsImport():
    return bpy.props.BoolProperty(
        name='Import Motions',
        description='Import embedded motions as actions',
        default=True
    )


def PropObjectMeshSplitByMaterials():
    return bpy.props.BoolProperty(
        name='Split Mesh By Materials',
        description='Import each surface (material) as separate set of faces',
        default=False
    )


def PropObjectBonesCustomShapes():
    return bpy.props.BoolProperty(
        name='Custom Shapes For Bones',
        description='Use custom shapes for imported bones',
        default=True
    )


def PropObjectUseMotionPrefixName():
    return bpy.props.BoolProperty(default=False, name='Motion Prefix Name')
