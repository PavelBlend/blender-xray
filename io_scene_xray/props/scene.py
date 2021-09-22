# blender modules
import bpy

# addon modules
from .. import version_utils
from .. import plugin_props
from .. import viewer


import_motion_props = {
    'motion_index': bpy.props.IntProperty(),
}


class ImportSkls(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in import_motion_props.items():
            exec('{0} = import_motion_props.get("{0}")'.format(prop_name))


class ImportOmf(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in import_motion_props.items():
            exec('{0} = import_motion_props.get("{0}")'.format(prop_name))


convert_materials_mode_items = (
    ('ACTIVE_MATERIAL', 'Active Material', ''),
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_MATERIALS', 'All Materials', '')
)
convert_materials_shader_type_items = (
    ('PRINCIPLED', 'Principled', ''),
    ('DIFFUSE', 'Diffuse', ''),
    ('EMISSION', 'Emission', '')
)

xray_scene_properties = {
    'export_root': bpy.props.StringProperty(
        name='Export Root',
        description='The root folder for export',
        subtype='DIR_PATH',
    ),
    'fmt_version': plugin_props.PropSDKVersion(),
    'object_export_motions': plugin_props.PropObjectMotionsExport(),
    'object_texture_name_from_image_path': plugin_props.PropObjectTextureNamesFromPath(),
    'import_skls': bpy.props.PointerProperty(type=ImportSkls),
    'import_omf': bpy.props.PointerProperty(type=ImportOmf),
    # material utils parameters
    'convert_materials_mode': bpy.props.EnumProperty(
        name='Mode', items=convert_materials_mode_items, default='ACTIVE_MATERIAL'
    ),
    'convert_materials_shader_type': bpy.props.EnumProperty(
        name='Shader', items=convert_materials_shader_type_items, default='PRINCIPLED'
    ),
    'materials_set_alpha_mode': bpy.props.BoolProperty(name='Use Alpha', default=True),
    'change_materials_alpha': bpy.props.BoolProperty(name='Change Alpha', default=True),
    'shader_specular_value': bpy.props.FloatProperty(
        name='Specular', default=0.0, min=0.0, max=1.0, subtype='FACTOR'
    ),
    'change_specular': bpy.props.BoolProperty(name='Change Specular', default=True),
    'shader_roughness_value': bpy.props.FloatProperty(
        name='Roughness', default=0.0, min=0.0, max=1.0, subtype='FACTOR'
    ),
    'change_roughness': bpy.props.BoolProperty(name='Change Roughness', default=True),
    'viewport_roughness_value': bpy.props.FloatProperty(
        name='Viewport Roughness', default=0.0, min=0.0, max=1.0, subtype='FACTOR'
    ),
    'change_viewport_roughness': bpy.props.BoolProperty(name='Change Viewport Roughness', default=True),

    # internal properties
    'change_shadeless': bpy.props.BoolProperty(name='Change Shadeless', default=True),
    'use_shadeless': bpy.props.BoolProperty(name='Shadeless', default=True),

    'change_diffuse_intensity': bpy.props.BoolProperty(
        name='Change Diffuse Intensity', default=True
    ),
    'diffuse_intensity': bpy.props.FloatProperty(
        name='Diffuse Intensity', default=1.0,
        min=0.0, max=1.0, subtype='FACTOR'
    ),

    'change_specular_intensity': bpy.props.BoolProperty(
        name='Change Specular Intensity', default=True
    ),
    'specular_intensity': bpy.props.FloatProperty(
        name='Specular Intensity', default=1.0,
        min=0.0, max=1.0, subtype='FACTOR'
    ),

    'change_specular_hardness': bpy.props.BoolProperty(
        name='Change Specular Hardness', default=True
    ),
    'specular_hardness': bpy.props.IntProperty(
        name='Specular Hardness', default=50,
        min=1, max=511
    ),

    'change_use_transparency': bpy.props.BoolProperty(
        name='Change Transparency', default=True
    ),
    'use_transparency': bpy.props.BoolProperty(
        name='Transparency', default=True
    ),

    'change_transparency_alpha': bpy.props.BoolProperty(
        name='Change Transparency Alpha', default=True
    ),
    'transparency_alpha': bpy.props.FloatProperty(
        name='Transparency Alpha', default=1.0,
        min=0.0, max=1.0, subtype='FACTOR'
    ),
    'viewer': bpy.props.PointerProperty(type=viewer.XRaySceneViewerProperties),
}


class XRaySceneProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Scene

    if not version_utils.IS_28:
        for prop_name, prop_value in xray_scene_properties.items():
            exec('{0} = xray_scene_properties.get("{0}")'.format(prop_name))


prop_groups = (
    (ImportSkls, import_motion_props, False),
    (ImportOmf, import_motion_props, False),
    (XRaySceneProperties, xray_scene_properties, True)
)


def register():
    for prop_group, props, is_group in prop_groups:
        version_utils.assign_props([
            (props, prop_group),
        ])
        bpy.utils.register_class(prop_group)
        if is_group:
            prop_group.b_type.xray = bpy.props.PointerProperty(type=prop_group)


def unregister():
    for prop_group, props, is_group in reversed(prop_groups):
        if is_group:
            del prop_group.b_type.xray
        bpy.utils.unregister_class(prop_group)
