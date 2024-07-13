# blender modules
import bpy

# addon modules
from .. import ops
from .. import formats
from .. import utils


class XRaySceneProps(bpy.types.PropertyGroup):
    b_type = bpy.types.Scene

    viewer = bpy.props.PointerProperty(type=ops.viewer.XRayViewerProps)
    merge_omf = bpy.props.PointerProperty(
        type=formats.omf.merge.XRayMergeOmfProps
    )


classes = (
    formats.omf.merge.XRAY_UL_merge_omf_list_item,
    formats.omf.merge.XRayMergeOmfFile,
    formats.omf.merge.XRayMergeOmfProps,
    XRaySceneProps
)


def register():
    utils.version.register_classes(classes)


def unregister():
    utils.version.unregister_prop_groups(classes)
