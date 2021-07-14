import bpy


def PropSDKVersion():
    return bpy.props.EnumProperty(
        name='SDK Version',
        items=(
            ('soc', 'SoC', ''),
            ('cscop', 'CS/CoP', '')
        )
    )
