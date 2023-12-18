# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import rw
from .. import text
from .. import formats
from .. import utils
from .. import log


class XRAY_UL_motions_list_item(bpy.types.UIList):
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

        # select
        row.prop(item, 'select', text='')

        row = utils.version.layout_split(row, 0.2)

        # frames count
        row.alignment = 'RIGHT'
        row.label(text=str(item.frames))

        # name
        row.alignment = 'LEFT'
        row.label(text=item.name)


class BaseBrowserOperator(utils.ie.BaseOperator):
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'


class XRAY_OT_close_motions_file(BaseBrowserOperator):
    '''Close animations list'''

    bl_idname = 'xray.close_motions_file'
    bl_label = 'Close File'

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
        browser = obj.xray.motions_browser

        anim_data = obj.animation_data
        if anim_data:
            act = anim_data.action
            obj.animation_data_clear()
            if not act.name in browser.exist_acts.keys():
                utils.version.remove_action(act)

        browser.animations.clear()
        browser.exist_acts.clear()
        browser.animations_index = 0
        browser.animations_prev_name = ''
        XRAY_OT_browse_motions_file.motions_file = None

        bpy.ops.screen.animation_cancel()
        utils.bone.reset_pose_bone_transforms(obj)
        utils.draw.redraw_areas()

        return {'FINISHED'}


@utils.set_cursor_state
def init_browser(self, context, filepath):
    browser = context.active_object.xray.motions_browser
    browser.animations.clear()
    browser.exist_acts.clear()

    if browser.file_format == 'SKLS':
        file = SklsFile(file_path=filepath)
    else:
        file = OmfFile(file_path=filepath)

    XRAY_OT_browse_motions_file.motions_file = file

    # collect available actions
    for action in bpy.data.actions:
        action_item = browser.exist_acts.add()
        action_item.name = action.name

    # fill list with animations names
    for name, (offset, length, index) in file.animations.items():
        anim = browser.animations.add()
        anim.name = name
        anim.frames = length

    report = getattr(self, 'report', None)
    if report:
        anims_count = len(file.animations)
        report(
            {'INFO'},
            text.get_text(text.warn.browser_done).format(anims_count)
        )


class SklsFile():
    '''
    Used to read animations from .skls file.
    Because .skls file can has big size and reading may take long time,
    so the animations cached by byte offset in file.
    Holds entire .skls file in memory as binary blob.
    '''

    __slots__ = 'reader', 'file_path', 'animations'

    def __init__(self, file_path):
        self.file_path = file_path
        # cached animations info (name: (file_offset, frames_count))
        self.animations = {}
        # read entire .skls file into memory
        file_data = rw.utils.read_file(file_path)
        self.reader = rw.read.PackedReader(file_data)
        self._index_animations()

    def _index_animations(self):
        '''
        Fills the cache (self.animations) by
        processing entire binary blob
        '''
        animations_count = self.reader.uint32()
        for anim_index in range(animations_count):
            # index animation
            # first byte of the animation name
            offset = self.reader.offset()
            # animation name
            name = self.reader.gets()
            offset_skip = self.reader.offset()
            frame_start, frame_end = self.reader.getf('<2I')
            length = int(frame_end - frame_start)
            self.animations[name] = (offset, length, anim_index)
            # skip the rest bytes of skl animation to the next animation
            self.reader.set_offset(offset_skip)
            skip = formats.motions.imp.skip_motion_rest(self.reader.getv(), 0)
            self.reader.skip(skip)


class OmfFile():
    __slots__ = (
        'reader',
        'file_path',
        'animations',
        'motions_params',
        'bone_names'
    )

    def __init__(self, file_path):
        self.file_path = file_path
        # cached animations info (name: (file_offset, frames_count))
        self.animations = {}
        # read entire .omf file into memory
        self._index_animations()

    def _index_animations(self):
        '''
        Fills the cache (self.animations) by
        processing entire binary blob
        '''

        obj = bpy.context.active_object

        imp_ctx = formats.omf.ops.ImportOmfContext()
        imp_ctx.import_bone_parts = False
        imp_ctx.import_motions = True
        imp_ctx.add_to_motion_list = False
        imp_ctx.bpy_arm_obj = obj

        file_data = rw.utils.read_file(self.file_path)
        chunks = rw.utils.get_chunks(file_data)

        params_data = chunks.pop(formats.ogf.fmt.Chunks_v4.S_SMPARAMS_1)
        params_chunk = 1
        self.motions_params, self.bone_names = formats.omf.imp.read_params(
            params_data,
            imp_ctx,
            params_chunk
        )

        motions_data = chunks.pop(formats.ogf.fmt.Chunks_v4.S_MOTIONS_2)
        self.reader = rw.read.PackedReader(motions_data)

        count_chunk, count_size, motions_count = self.reader.getf('<3I')

        for anim_index in range(motions_count):
            chunk_id, chunk_size = self.reader.getf('<2I')
            motion_id = chunk_id - 1
            # index animation
            # first byte of the animation name
            offset = self.reader.offset()

            # animation name
            try:
                name = self.reader.gets()
            except:
                name = None

            motion_params = None
            if name:
                motion_params = self.motions_params.by_dict.get(name, None)
            if not motion_params:
                motion_params = self.motions_params.by_list[motion_id]
                name = motion_params.name

            length = self.reader.uint32()
            self.animations[name] = (offset, length, motion_id)
            # skip the rest bytes of skl animation to the next animation
            formats.omf.imp.skip_motion(self.reader, self.bone_names, length)


class XRAY_OT_browse_motions_file(BaseBrowserOperator):
    '''
    Shows file open dialog, reads .skls/.omf file to buffer,
    clears & populates animations list
    '''

    bl_idname = 'xray.browse_motions_file'
    bl_label = 'Open file'
    bl_description = \
        'Opens .skls/.omf file with collection of animations. ' \
        'Used to import X-Ray engine animations. ' \
        'To import select object with X-Ray struct of bones'

    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'HIDDEN'}
    )
    filter_glob = bpy.props.StringProperty(
        default='*.*',
        options={'HIDDEN'}
    )

    # pure python hold variable of .skls/.omf file buffer instance
    motions_file = None

    def execute(self, context):
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, 'File not found: {}'.format(self.filepath))
            return {'CANCELLED'}

        if os.path.isdir(self.filepath):
            self.report(
                {'ERROR'},
                'Is a folder, not a file: {}'.format(self.filepath)
            )
            return {'CANCELLED'}

        init_browser(self, context, self.filepath)
        utils.draw.redraw_areas()
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        browser = context.active_object.xray.motions_browser

        if browser.file_format == 'SKLS':
            self.filter_glob = '*.skls'
        else:
            self.filter_glob = '*.omf'

        context.window_manager.fileselect_add(operator=self)
        return {'RUNNING_MODAL'}


def import_anim(obj, file, animation_name):
    browser = obj.xray.motions_browser
    offset, length, motion_id = file.animations[animation_name]
    file.reader.set_offset(offset)

    # used to bone's reference detection
    bones_map = {bone.name.lower(): bone for bone in obj.data.bones}

    # bones names that has problems while import
    reported = set()

    if browser.file_format == 'SKLS':
        # *.skls
        imp_ctx = formats.skl.imp.ImportSklContext()
        imp_ctx.bpy_arm_obj = obj
        imp_ctx.motions_filter = formats.motions.imp.MOTIONS_FILTER_ALL
        imp_ctx.filename = file.file_path

        # import
        formats.motions.imp.import_motion(
            file.reader,
            imp_ctx,
            bones_map,
            reported
        )

    else:
        # *.omf
        imp_ctx = formats.omf.ops.ImportOmfContext()
        imp_ctx.import_bone_parts = False
        imp_ctx.import_motions = True
        imp_ctx.add_to_motion_list = False
        imp_ctx.bpy_arm_obj = obj
        imp_ctx.filepath = file.file_path
        imp_ctx.selected_names = None

        # import
        formats.omf.imp.read_motion(
            motion_id,
            file.reader,
            imp_ctx,
            file.motions_params,
            file.bone_names,
            2    # version
        )

    browser.animations_prev_name = animation_name
    act = bpy.data.actions[animation_name]

    # assign new animation
    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = act

    # set action frame range
    frame_start, frame_end = act.frame_range
    bpy.context.scene.frame_start = int(frame_start)
    bpy.context.scene.frame_current = int(frame_start)
    bpy.context.scene.frame_end = int(frame_end)


@utils.set_cursor_state
def anim_index_changed(self, context):
    '''Selected animation changed in .skls/.omf list'''

    report = lambda error, text: None
    logger = log.Logger(report)
    log.set_logger(logger)

    obj = context.active_object
    file = XRAY_OT_browse_motions_file.motions_file

    # get new animation name
    if not file:
        # file not loaded
        return

    browser = obj.xray.motions_browser
    if not browser.animations.keys():
        return

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
    if obj.animation_data:
        # need to remove previous animation to free
        # the memory since .skls/.omf
        # can contains thousand animations
        act = obj.animation_data.action
        obj.animation_data_clear()
        if act:
            if not act.name in browser.exist_acts.keys():
                utils.version.remove_action(act)

    # delete from xray property group
    motion_name = browser.animations_prev_name
    if not motion_name in browser.exist_acts.keys():
        motion_names = obj.xray.motions_collection.keys()
        try:
            motion_index = motion_names.index(motion_name)
            obj.xray.motions_collection.remove(motion_index)
        except ValueError:
            pass

    # import animation
    if not animation_name in bpy.data.actions:
        import_anim(obj, file, animation_name)
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


class XRAY_OT_motions_browser_select(BaseBrowserOperator):
    bl_idname = 'xray.motions_browser_select'
    bl_label = 'Select Animation'

    mode = bpy.props.EnumProperty(
        items=(
            ('ALL', 'All', ''),
            ('NONE', 'None', ''),
            ('INVERT', 'Invert', '')
        ),
        name='Mode',
        default='ALL'
    )

    @utils.set_cursor_state
    def execute(self, context):
        obj = context.active_object
        browser = obj.xray.motions_browser

        if self.mode in ('ALL', 'NONE'):
            if self.mode == 'ALL':
                select_state = True
            else:
                select_state = False

            for anim in browser.animations:
                anim.select = select_state

        elif self.mode == 'INVERT':
            for anim in browser.animations:
                anim.select = not anim.select

        return {'FINISHED'}


class XRAY_OT_motions_browser_import(BaseBrowserOperator):
    bl_idname = 'xray.motions_browser_import'
    bl_label = 'Select Animation'

    mode = bpy.props.EnumProperty(
        items=(
            ('ACTIVE', 'Active', ''),
            ('SELECTED', 'Selected', ''),
            ('ALL', 'All', '')
        ),
        name='Mode',
        default='SELECTED'
    )

    @utils.set_cursor_state
    @utils.stats.execute_with_stats
    def execute(self, context):
        obj = context.active_object
        browser = obj.xray.motions_browser
        file = XRAY_OT_browse_motions_file.motions_file
        anims = []

        # collect animations names
        if self.mode in ('SELECTED'):
            for anim in browser.animations:
                if anim.select:
                    anims.append(anim.name)
        elif self.mode in ('ALL'):
            for anim in browser.animations:
                anims.append(anim.name)
        elif self.mode in ('ACTIVE'):
            anim = browser.animations[browser.animations_index]
            anims.append(anim.name)

        # import animations
        count = 0
        for anim_name in anims:
            if not anim_name in obj.xray.motions_collection:
                motion = obj.xray.motions_collection.add()
                motion.name = anim_name
            available_act = browser.exist_acts.add()
            available_act.name = anim_name
            if anim_name in bpy.data.actions:
                continue
            import_anim(obj, file, anim_name)
            count += 1

        self.report(
            {'INFO'},
            text.get_text(text.warn.browser_import) + ': ' + str(count)
        )

        return {'FINISHED'}


class XRayMotionsAnimationProps(bpy.types.PropertyGroup):
    '''
    Contains animation properties in animations
    list of .skls/.omf file
    '''

    # animation name in .skls/.omf file
    name = bpy.props.StringProperty(name='Name')
    frames = bpy.props.IntProperty(name='Frames')
    select = bpy.props.BoolProperty(name='Select', default=True)


class XRayMotionsExistingActs(bpy.types.PropertyGroup):
    '''Contains available actions before importing new'''

    name = bpy.props.StringProperty(name='Name')


class XRayMotionsBrowserProps(bpy.types.PropertyGroup):
    animations = bpy.props.CollectionProperty(type=XRayMotionsAnimationProps)
    animations_index = bpy.props.IntProperty(update=anim_index_changed)
    animations_prev_name = bpy.props.StringProperty()
    exist_acts = bpy.props.CollectionProperty(type=XRayMotionsExistingActs)
    file_format = bpy.props.EnumProperty(
        name='Format',
        items=(('SKLS', 'Skls', ''), ('OMF', 'Omf', ''))
    )


classes = (
    # lists
    XRAY_UL_motions_list_item,

    # props
    XRayMotionsAnimationProps,
    XRayMotionsExistingActs,
    XRayMotionsBrowserProps,

    # operators
    XRAY_OT_browse_motions_file,
    XRAY_OT_close_motions_file,
    XRAY_OT_motions_browser_select,
    XRAY_OT_motions_browser_import
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
