# blender modules
import bpy

# addon modules
from .. import formats
from .. import utils
from .. import text
from .. import rw


class XRAY_OT_add_all_actions(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.add_all_actions'
    bl_label = 'Add All Actions'
    bl_description = 'Add all actions to motion list'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self, context):
        ctx = formats.contexts.Context()
        root_obj = utils.obj.find_root(ctx, context.active_object)
        arm_obj = utils.ie.get_arm_obj(root_obj, self)

        if not arm_obj:
            return {'FINISHED'}

        # collect exportable bones
        exportable_bones = set()
        non_exportable_bones = set()
        for bone in arm_obj.data.bones:
            if bone.xray.exportable:
                exportable_bones.add(bone.name)
            else:
                non_exportable_bones.add(bone.name)

        added_count = 0
        path_pose = 'pose.bones["'
        path_loc = '"].location'
        path_euler = '"].rotation_euler'
        path_quat = '"].rotation_quaternion'
        path_angle = '"].rotation_axis_angle'

        for action in bpy.data.actions:
            action_bones = set()

            for fcurve in action.fcurves:
                path = fcurve.data_path

                if path.startswith(path_pose):
                    path = path[len(path_pose) : ]
                else:
                    continue

                if path.endswith(path_loc):
                    path = path[ : -len(path_loc)]

                elif path.endswith(path_euler):
                    path = path[ : -len(path_euler)]

                elif path.endswith(path_quat):
                    path = path[ : -len(path_quat)]

                elif path.endswith(path_angle):
                    path = path[ : -len(path_angle)]

                else:
                    continue

                action_bones.add(path)

            action_exportable_bones = action_bones - non_exportable_bones
            if not action_exportable_bones - exportable_bones:
                if not root_obj.xray.motions_collection.get(action.name):
                    motion = root_obj.xray.motions_collection.add()
                    motion.name = action.name
                    added_count += 1

        utils.draw.redraw_areas()
        self.report(
            {'INFO'},
            text.get_text(text.warn.added_motions) + ': ' + str(added_count)
        )

        return {'FINISHED'}


class XRAY_OT_remove_all_actions(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.remove_all_actions'
    bl_label = 'Remove All Actions'
    bl_description = 'Remove all actions'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return

        has_motions = bool(len(obj.xray.motions_collection))

        return has_motions

    def execute(self, context):
        obj = context.active_object
        obj.xray.motions_collection.clear()
        utils.draw.redraw_areas()
        return {'FINISHED'}


class XRAY_OT_clean_actions(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.clean_actions'
    bl_label = 'Clean Actions'
    bl_description = 'Remove non-existent actions'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self, context):
        obj = context.active_object

        remove = set()
        available = set()

        for motion_index, motion in enumerate(obj.xray.motions_collection):
            action = bpy.data.actions.get(motion.name)

            # non-existent action
            if not action:
                remove.add(motion_index)

            # duplicated action
            if motion.name in available:
                remove.add(motion_index)

            available.add(motion.name)

        remove = list(remove)
        remove.sort(reverse=True)

        for motion_index in remove:
            obj.xray.motions_collection.remove(motion_index)

        utils.draw.redraw_areas()
        return {'FINISHED'}


MOTION_NAME_PARAM = 'motion_name'
EXPORT_NAME_PARAM = 'export_name'


class XRAY_OT_copy_actions(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.copy_actions'
    bl_label = 'Copy Actions'
    bl_description = 'Copy actions list to clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self, context):
        obj = context.active_object

        lines = []
        saved_motions = set()

        for motion_index, motion in enumerate(obj.xray.motions_collection):
            if not motion.name:
                continue

            motion_key = (motion.name, motion.export_name)

            if motion_key in saved_motions:
                continue

            lines.append('[{}]\n{} = "{}"\n{} = "{}"\n'.format(
                motion_index,
                MOTION_NAME_PARAM,
                motion.name,
                EXPORT_NAME_PARAM,
                motion.export_name
            ))
            saved_motions.add(motion_key)

        bpy.context.window_manager.clipboard = '\n'.join(lines)

        return {'FINISHED'}


class XRAY_OT_paste_actions(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.paste_actions'
    bl_label = 'Past Actions'
    bl_description = 'Paste actions list from clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self, context):
        xray = context.active_object.xray

        ltx = rw.ltx.LtxParser()
        ltx.from_str(context.window_manager.clipboard)
        used_motions = [
            (motion.name, motion.export_name)
            for motion in xray.motions_collection
        ]
        use_custom_name = False

        for section_key, section in ltx.sections.items():
            motion_name = section.params.get(MOTION_NAME_PARAM, None)
            export_name = section.params.get(EXPORT_NAME_PARAM, None)

            if not motion_name:
                continue

            motion_key = (motion_name, export_name)

            if motion_key in used_motions:
                continue

            motion = xray.motions_collection.add()
            motion.name = motion_name

            if export_name:
                motion.export_name = export_name
                use_custom_name = True

        if use_custom_name:
            xray.use_custom_motion_names = True

        utils.draw.redraw_areas()

        return {'FINISHED'}


class XRAY_OT_sort_actions(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.sort_actions'
    bl_label = 'Sort Motions'
    bl_description = 'Sort motions list'
    bl_options = {'UNDO'}

    sort_by = bpy.props.EnumProperty(
        items=(
            ('NAME', 'Action Name', ''),
            ('EXPORT', 'Export Name', ''),
            ('LENGTH', 'Action Length', '')
        )
    )
    sort_reverse = bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):    # pragma: no cover
        lay = self.layout
        lay.label(text='Sort by:')
        lay.prop(self, 'sort_by', expand=True)
        lay.prop(self, 'sort_reverse', text='Reverse Sort', toggle=True)

    def execute(self, context):
        motions = context.active_object.xray.motions_collection

        if self.sort_by in ('NAME', 'LENGTH'):
            sort_fun = lambda i: i[0]
        else:
            sort_fun = lambda i: i[2]

        used_motions = []

        if self.sort_by == 'LENGTH':
            motions_length = {}
            for motion in motions:
                act = bpy.data.actions.get(motion.name)

                if act:
                    start, end = act.frame_range
                    length = int(round(end - start, 0))
                else:
                    length = -1

                motions_length.setdefault(length, []).append((
                    motion.name,
                    motion.export_name,
                    None
                ))

            length_keys = list(motions_length.keys())
            length_keys.sort()
            for key in length_keys:
                key_motions = motions_length[key]
                key_motions.sort(key=sort_fun)
                for name, exp, _ in key_motions:
                    used_motions.append((name, exp, _))

        else:
            for motion in motions:
                if motion.export_name:
                    exp = motion.export_name
                else:
                    exp = motion.name
                used_motions.append((motion.name, motion.export_name, exp))
            used_motions.sort(key=sort_fun)

        if self.sort_reverse:
            used_motions.reverse()

        motions.clear()

        for name, exp, _ in used_motions:
            elem = motions.add()
            elem.name = name
            elem.export_name = exp

        utils.draw.redraw_areas()

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    XRAY_OT_add_all_actions,
    XRAY_OT_remove_all_actions,
    XRAY_OT_clean_actions,
    XRAY_OT_copy_actions,
    XRAY_OT_paste_actions,
    XRAY_OT_sort_actions
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
