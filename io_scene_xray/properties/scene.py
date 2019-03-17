
import bpy

from .. import registry
from .. import plugin_prefs


@registry.requires('ImportSkls')
class XRaySceneProperties(bpy.types.PropertyGroup):
    class ImportSkls(bpy.types.PropertyGroup):
        motion_index = bpy.props.IntProperty()

    b_type = bpy.types.Scene
    export_root = bpy.props.StringProperty(
        name='Export Root',
        description='The root folder for export',
        subtype='DIR_PATH',
    )
    fmt_version = plugin_prefs.PropSDKVersion()
    object_export_motions = plugin_prefs.PropObjectMotionsExport()
    object_texture_name_from_image_path = plugin_prefs.PropObjectTextureNamesFromPath()
    materials_colorize_random_seed = bpy.props.IntProperty(min=0, max=255, options={'SKIP_SAVE'})
    materials_colorize_color_power = bpy.props.FloatProperty(
        default=0.5, min=0.0, max=1.0,
        options={'SKIP_SAVE'},
    )
    import_skls = bpy.props.PointerProperty(type=ImportSkls)
