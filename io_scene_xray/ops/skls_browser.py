# blender modules
import bpy

# addon modules
from .. import xray_io
from .. import motions
from .. import text
from .. import skl
from .. import utils
from .. import log


class XRAY_UL_skls_list_item(bpy.types.UIList):
    def draw_item(
            self,
            context,
            layout,
            data,
            item,
            icon,
            active_data,
            active_propname
        ):
        row = layout.row()
        row = utils.version.layout_split(row, 0.2)
        row.alignment = 'RIGHT'
        row.label(text=str(item.frames))
        row.alignment = 'LEFT'
        row.label(text=item.name)


class BaseSklsBrowserOperator(bpy.types.Operator):
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'


class XRAY_OT_close_skls_file(BaseSklsBrowserOperator):
    '''Close *.skls animations list'''

    bl_idname = 'xray.close_skls_file'
    bl_label = 'Close Skls File'

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
        browser = obj.xray.skls_browser
        anim_data = obj.animation_data
        if anim_data:
            act = anim_data.action
            obj.animation_data_clear()
            utils.version.remove_action(act)
        browser.animations.clear()
        bpy.ops.screen.animation_cancel()
        utils.reset_pose_bone_transforms(obj)
        return {'FINISHED'}


@utils.set_cursor_state
def init_skls_browser(self, context, filepath):
    report = getattr(self, 'report', None)

    if report:
        report({'INFO'}, text.warn.browser_load.format(filepath))

    browser = context.object.xray.skls_browser
    browser.animations.clear()
    skls = SklsFile(file_path=filepath)
    XRAY_OT_browse_skls_file.skls_file = skls

    if report:
        anims_count = len(skls.animations)
        report({'INFO'}, text.warn.browser_done.format(anims_count))

    # fill list with animations names
    for name, (offset, length) in skls.animations.items():
        anim = browser.animations.add()
        # animation name
        anim.name = name
        # frames count
        anim.frames = length


class SklsFile():
    '''
    Used to read animations from .skls file.
    Because .skls file can has big size and reading may take long time,
    so the animations cached by byte offset in file.
    Holds entire .skls file in memory as binary blob.
    '''

    __slots__ = 'pr', 'file_path', 'animations'

    def __init__(self, file_path):
        self.file_path = file_path
        # cached animations info (name: (file_offset, frames_count))
        self.animations = {}
        # read entire .skls file into memory
        file_data = utils.read_file(file_path)
        self.pr = xray_io.PackedReader(file_data)
        self._index_animations()

    def _index_animations(self):
        'Fills the cache (self.animations) by processing entire binary blob'
        animations_count = self.pr.getf('I')[0]
        for anim_index in range(animations_count):
            # index animation
            # first byte of the animation name
            offset = self.pr.offset()
            # animation name
            name = self.pr.gets()
            offset_skip = self.pr.offset()
            frame_start, frame_end = self.pr.getf('<2I')
            length = int(frame_end - frame_start)
            self.animations[name] = (offset, length)
            # skip the rest bytes of skl animation to the next animation
            self.pr.set_offset(offset_skip)
            skip = motions.imp.skip_motion_rest(self.pr.getv(), 0)
            self.pr.skip(skip)


browse_props = {
    'filepath': bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'HIDDEN'}
    ),
    'filter_glob': bpy.props.StringProperty(
        default='*.skls',
        options={'HIDDEN'}
    )
}


class XRAY_OT_browse_skls_file(BaseSklsBrowserOperator):
    '''
    Shows file open dialog, reads .skls file to buffer,
    clears & populates animations list
    '''

    bl_idname = 'xray.browse_skls_file'
    bl_label = 'Open .skls file'
    bl_description = \
        'Opens .skls file with collection of animations. ' \
        'Used to import X-Ray engine animations. ' \
        'To import select object with X-Ray struct of bones'

    if not utils.version.IS_28:
        for prop_name, prop_value in browse_props.items():
            exec('{0} = browse_props.get("{0}")'.format(prop_name))

    # pure python hold variable of .skls file buffer instance
    skls_file = None

    def execute(self, context):
        init_skls_browser(self, context, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(operator=self)
        return {'RUNNING_MODAL'}


@utils.set_cursor_state
def skls_animations_index_changed(self, context):
    '''Selected animation changed in .skls list'''

    report = lambda error, text: None
    logger = utils.Logger(report)
    log.__logger__[0] = logger

    skls = XRAY_OT_browse_skls_file.skls_file

    # get new animation name
    if not skls:
        # .skls file not loaded
        return

    browser = context.object.xray.skls_browser
    animation_name = browser.animations[browser.animations_index].name

    if animation_name == browser.animations_prev_name:
        # repeat animation selection
        return

    try:
        # it can happened that unlink action is inaccessible
        bpy.ops.action.unlink()
    except:
        pass

    # remove previous animation if need
    obj = context.active_object
    if obj.animation_data:
        # need to remove previous animation to free the memory since .skls
        # can contains thousand animations
        act = obj.animation_data.action
        obj.animation_data_clear()
        if act:
            utils.version.remove_action(act)

    # delete from xray property group
    motion_name = browser.animations_prev_name
    motion_names = obj.xray.motions_collection.keys()
    try:
        motion_index = motion_names.index(motion_name)
        obj.xray.motions_collection.remove(motion_index)
    except ValueError:
        pass

    # import animation
    if not animation_name in bpy.data.actions:
        offset, length = skls.animations[animation_name]
        skls.pr.set_offset(offset)

        # used to bone's reference detection
        bones_map = {bone.name.lower(): bone for bone in obj.data.bones}

        # bones names that has problems while import
        reported = set()

        import_context = skl.imp.ImportSklContext()
        import_context.bpy_arm_obj = obj
        import_context.motions_filter = motions.utilites.MOTIONS_FILTER_ALL
        import_context.filename = skls.file_path

        # import
        motions.imp.import_motion(
            skls.pr,
            import_context,
            bones_map,
            reported
        )

        browser.animations_prev_name = animation_name
        act = bpy.data.actions[animation_name]

        # assign new animation
        if not obj.animation_data:
            obj.animation_data_create()
        obj.animation_data.action = act

        # set action frame range
        frame_start, frame_end = act.frame_range
        context.scene.frame_start = int(frame_start)
        context.scene.frame_current = int(frame_start)
        context.scene.frame_end = int(frame_end)

    else:
        act = bpy.data.actions[animation_name]

        # try to find DopeSheet editor & set action
        dope_sheets = [
            area
            for area in context.screen.areas
                if area.type == 'DOPESHEET_EDITOR'
        ]
        for dope_sheet in dope_sheets:
            if not dope_sheet.spaces[0].action:
                dope_sheet.spaces[0].action = act


anim_props = {
    # animation name in .skls file
    'name': bpy.props.StringProperty(name='Name'),
    'frames': bpy.props.IntProperty(name='Frames')
}


class XRaySklsAnimationProperties(bpy.types.PropertyGroup):
    '''Contains animation properties in animations list of .skls file'''

    if not utils.version.IS_28:
        for prop_name, prop_value in anim_props.items():
            exec('{0} = anim_props.get("{0}")'.format(prop_name))


skls_browser_props = {
    'animations': bpy.props.CollectionProperty(
        type=XRaySklsAnimationProperties
    ),
    'animations_index': bpy.props.IntProperty(
        update=skls_animations_index_changed
    ),
    'animations_prev_name': bpy.props.StringProperty()
}


class XRayObjectSklsBrowserProperties(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in skls_browser_props.items():
            exec('{0} = skls_browser_props.get("{0}")'.format(prop_name))


classes = (
    (XRAY_UL_skls_list_item, None),
    (XRaySklsAnimationProperties, anim_props),
    (XRayObjectSklsBrowserProperties, skls_browser_props),
    (XRAY_OT_browse_skls_file, browse_props),
    (XRAY_OT_close_skls_file, None)
)


def register():
    for clas, props in classes:
        if props:
            utils.version.assign_props([(props, clas), ])
        bpy.utils.register_class(clas)


def unregister():
    for clas, props in reversed(classes):
        bpy.utils.unregister_class(clas)
