# blender modules
import bpy


# import props
def prop_details_models_in_a_row():
    return bpy.props.BoolProperty(name='Details Models in a Row', default=True)


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


# export props
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
