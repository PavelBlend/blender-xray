import bpy


def PropObjectMotionsExport():
    return bpy.props.BoolProperty(
        name='Export Motions',
        description='Export armatures actions as embedded motions',
        default=True
    )


def PropObjectTextureNamesFromPath():
    return bpy.props.BoolProperty(
        name='Texture Names From Image Paths',
        description='Generate texture names from image paths ' \
        + '(by subtract <gamedata/textures> prefix and <file-extension> suffix)',
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
