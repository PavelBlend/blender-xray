# blender modules
import bpy

# addon modules
from .. import plugin_prefs


class XRAY_OT_FbxExport(bpy.types.Operator):
    bl_idname = 'io_scene_xray.export_fbx'
    bl_label = 'Export FBX'

    def execute(self, context):
        if hasattr(bpy.types, 'EXPORT_SCENE_OT_fbx'):
            prefs = plugin_prefs.get_preferences()
            # set object properties
            for obj in context.selected_objects:
                xray = obj.xray
                obj[prefs.fbx_object_flags] = xray.flags
                obj[prefs.fbx_object_userdata] = xray.userdata
                obj[prefs.fbx_object_lod_reference] = xray.lodref
                obj[prefs.fbx_object_owner_name] = xray.revision.owner
                obj[prefs.fbx_object_creation_time] = xray.revision.ctime
                obj[prefs.fbx_object_modif_name] = xray.revision.moder
                obj[prefs.fbx_object_modified_time] = xray.revision.mtime
                motion_refs = []
                for motion_ref in xray.motionrefs_collection:
                    motion_refs.append(motion_ref.name)
                obj[prefs.fbx_object_motion_references] = '\n'.join(motion_refs)
            # run fbx export
            bpy.ops.export_scene.fbx('INVOKE_DEFAULT')
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, 'The FBX addon is not activated.')
            return {'CANCELLED'}
