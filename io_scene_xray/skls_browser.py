# blender modules
import bpy

# addon modules
from . import xray_io
from . import xray_motions
from . import skl
from . import version_utils


class UI_UL_SklsList_item(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row()
        row = version_utils.layout_split(row, 0.30)
        row.alignment = 'RIGHT'
        row.label(text=str(item.frames))
        row.alignment = 'LEFT'
        row.label(text=item.name)


class OpCloseSklsFile(bpy.types.Operator):
    'Close *.skls animations list'
    bl_idname = 'xray.close_skls_file'
    bl_label = 'Close Skls File'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and hasattr(context.active_object.data, 'bones')

    def execute(self, context):
        context.window.cursor_set('WAIT')
        ob = context.active_object
        sk = ob.xray.skls_browser
        if ob.animation_data:
            act = ob.animation_data.action
            ob.animation_data_clear()
            act.user_clear()
            bpy.data.actions.remove(action=act)
        sk.animations.clear()
        bpy.ops.screen.animation_cancel()
        # reset transforms
        for bone in ob.pose.bones:
            bone.location = (0, 0, 0)
            bone.rotation_euler = (0, 0, 0)
            bone.rotation_quaternion = (1, 0, 0, 0)
            bone.scale = (1, 1, 1)
        context.window.cursor_set('DEFAULT')
        return {'FINISHED'}


def init_skls_browser(self, context, filepath):
    if getattr(self, 'report', None):
        self.report({'INFO'}, 'Loading animations from .skls file: "{}"'.format(filepath))
    context.window.cursor_set('WAIT')
    sk = context.object.xray.skls_browser
    sk.animations.clear()
    OpBrowseSklsFile.skls_file = OpBrowseSklsFile.SklsFile(file_path=filepath)
    if getattr(self, 'report', None):
        self.report({'INFO'}, 'Done: {} animation(s)'.format(len(OpBrowseSklsFile.skls_file.animations)))
    # fill list with animations names
    for name, offset_frames in OpBrowseSklsFile.skls_file.animations.items():
        newitem = sk.animations.add()
        newitem.name = name    # animation name
        newitem.frames = offset_frames[1]    # frames count
    context.window.cursor_set('DEFAULT')


op_browse_skls_file_props = {
    'filepath': bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN'}),
    'filter_glob': bpy.props.StringProperty(default='*.skls', options={'HIDDEN'})
}


class OpBrowseSklsFile(bpy.types.Operator):
    'Shows file open dialog, reads .skls file to buffer, clears & populates animations list'
    bl_idname = 'xray.browse_skls_file'
    bl_label = 'Open .skls file'
    bl_description = 'Opens .skls file with collection of animations. Used to import X-Ray engine animations.'+\
        ' To import select object with X-Ray struct of bones'

    if not version_utils.IS_28:
        for prop_name, prop_value in op_browse_skls_file_props.items():
            exec('{0} = op_browse_skls_file_props.get("{0}")'.format(prop_name))

    class SklsFile():
        '''
        Used to read animations from .skls file.
        Because .skls file can has big size and reading may take long time, so the animations
        cached by byte offset in file.
        Holds entire .skls file in memory as binary blob.
        '''
        __slots__ = 'pr', 'file_path', 'animations'

        def __init__(self, file_path):
            self.file_path = file_path
            self.animations = {} # cached animations info (name: (file_offset, frames_count))
            with open(file_path, mode='rb') as f:
                # read entire .skls file into memory
                self.pr = xray_io.PackedReader(f.read())
            self._index_animations()

        def _index_animations(self):
            'Fills the cache (self.animations) by processing entire binary blob'
            animations_count = self.pr.getf('I')[0]
            for _ in range(animations_count):
                # index animation
                offset = self.pr.offset() # first byte of the animation name
                name = self.pr.gets() # animation name
                offset2 = self.pr.offset()
                frames_range = self.pr.getf('II')
                self.animations[name] = (offset, int(frames_range[1] - frames_range[0]))
                # skip the rest bytes of skl animation to the next animation
                self.pr.set_offset(offset2)
                skip = xray_motions.skip_motion_rest(self.pr.getv(), 0)
                self.pr.skip(skip)

    skls_file = None    # pure python hold variable of .skls file buffer instance

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and hasattr(context.active_object.data, 'bones')

    def execute(self, context):
        init_skls_browser(self, context, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(operator=self)
        return {'RUNNING_MODAL'}


def skls_animations_index_changed(self, context):
    'Selected animation changed in .skls list'

    # get new animation name
    if not OpBrowseSklsFile.skls_file:
        # .skls file not loaded
        return
    sk = context.object.xray.skls_browser
    animation_name = sk.animations[sk.animations_index].name
    if animation_name == sk.animations_prev_name:
        return # repeat animation selection

    # try to cancel & unlink old animation
    try:
        bpy.ops.screen.animation_cancel()
    except:
        pass
    try:
        # it can happened that unlink action is inaccessible
        bpy.ops.action.unlink()
    except:
        pass

    # remove previous animation if need
    ob = context.active_object
    if ob.animation_data:
        # need to remove previous animation to free the memory since .skls can contains thousand animations
        act = ob.animation_data.action
        ob.animation_data_clear()
        act.user_clear()
        bpy.data.actions.remove(action=act)

    # delete from xray property group
    try:
        ob.xray.motions_collection.remove(ob.xray.motions_collection.keys().index(sk.animations_prev_name))
    except ValueError:
        pass

    # import animation
    if animation_name not in bpy.data.actions:
        # animation not imported yet # import & create animation to bpy.data.actions
        context.window.cursor_set('WAIT')
        # import animation
        OpBrowseSklsFile.skls_file.pr.set_offset(OpBrowseSklsFile.skls_file.animations[animation_name][0])
        # bpy_armature = context.armature
        bonesmap = {b.name.lower(): b for b in ob.data.bones}    # used to bone's reference detection
        reported = set()    # bones names that has problems while import
        import_context = skl.imp.ImportSklContext()
        import_context.bpy_arm_obj=ob
        import_context.motions_filter=xray_motions.MOTIONS_FILTER_ALL
        import_context.use_motion_prefix_name=False
        import_context.filename=OpBrowseSklsFile.skls_file.file_path
        xray_motions.import_motion(OpBrowseSklsFile.skls_file.pr, import_context, bonesmap, reported)
        sk.animations_prev_name = animation_name
        context.window.cursor_set('DEFAULT')
        # try to find DopeSheet editor & set action to play
        try:
            ds = [i for i in context.screen.areas if i.type=='DOPESHEET_EDITOR']
            if ds and not ds[0].spaces[0].action:
                ds.spaces[0].action = bpy.data.actions[animation_name]
        except AttributeError:
            pass

    # assign & play a new animation
    # bpy.data.armatures[0].pose_position='POSE'
    try:
        act = bpy.data.actions[animation_name]
        if not ob.animation_data:
            ob.animation_data_create()
        ob.animation_data.action = act
    except:
        pass
    else:
        # play an action from first to last frames in cycle
        try:
            context.scene.frame_start = act.frame_range[0]
            context.scene.frame_current = act.frame_range[0]
            context.scene.frame_end = act.frame_range[1]
            bpy.ops.screen.animation_play()
        except:
            pass


xray_skls_animation_properties_props = {
    'name': bpy.props.StringProperty(name='Name'),    # animation name in .skls file
    'frames': bpy.props.IntProperty(name='Frames')
}


class XRaySklsAnimationProperties(bpy.types.PropertyGroup):
    'Contains animation properties in animations list of .skls file'

    if not version_utils.IS_28:
        for prop_name, prop_value in xray_skls_animation_properties_props.items():
            exec('{0} = xray_skls_animation_properties_props.get("{0}")'.format(prop_name))


xray_object_skls_browser_properties_props = {
    'animations': bpy.props.CollectionProperty(type=XRaySklsAnimationProperties),
    'animations_index': bpy.props.IntProperty(update=skls_animations_index_changed),
    'animations_prev_name': bpy.props.StringProperty()
}


class XRayObjectSklsBrowserProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in xray_object_skls_browser_properties_props.items():
            exec('{0} = xray_object_skls_browser_properties_props.get("{0}")'.format(prop_name))


classes = (
    (UI_UL_SklsList_item, None),
    (XRaySklsAnimationProperties, xray_skls_animation_properties_props),
    (XRayObjectSklsBrowserProperties, xray_object_skls_browser_properties_props),
    (OpBrowseSklsFile, op_browse_skls_file_props),
    (OpCloseSklsFile, None)
)


def register():
    for clas, props in classes:
        if props:
            version_utils.assign_props([(props, clas), ])
        bpy.utils.register_class(clas)


def unregister():
    for clas, props in reversed(classes):
        bpy.utils.unregister_class(clas)
