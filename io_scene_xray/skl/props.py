import bpy


def prop_skl_add_actions_to_motion_list():
    return bpy.props.BoolProperty(default=True, name='Add Actions to Motion List')
