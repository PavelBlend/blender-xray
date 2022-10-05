# standart modules
import math

# blender modules
import bpy

# addon modules
from .. import utils


SOC_HUD_FOV = 30.5


class XRAY_OT_add_camera(bpy.types.Operator):
    bl_idname = 'io_scene_xray.add_camera'
    bl_label = 'Add X-Ray Camera'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # set object mode
        if context.object:
            bpy.ops.object.mode_set(mode='OBJECT')
        # create camera
        camera = bpy.data.cameras.new('xray-camera')
        camera_obj = bpy.data.objects.new('xray-camera', camera)
        # link and select
        bpy.ops.object.select_all(action='DESELECT')
        utils.version.link_object(camera_obj)
        utils.version.select_object(camera_obj)
        utils.version.set_active_object(camera_obj)
        # set camera object transforms
        camera_obj.location = (0, 0, 0)
        camera_obj.rotation_mode = 'XYZ'
        camera_obj.rotation_euler = (math.pi / 2, 0, 0)
        camera_obj.scale = (1, 1, 1)
        # set camera settings
        if utils.version.IS_28:
            camera.display_size = 0.1
        else:
            camera.draw_size = 0.1
        camera.clip_start = 0.2
        camera.lens_unit = 'FOV'
        camera.sensor_fit = 'VERTICAL'
        camera.angle = math.radians(SOC_HUD_FOV)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(XRAY_OT_add_camera)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_add_camera)
