# standart modules
import os

# blender modules
import bpy

# addon modules
from .. import utils


class XRAY_OT_remove_all_motion_refs(bpy.types.Operator):
    bl_idname = 'io_scene_xray.remove_all_motion_refs'
    bl_label = 'Remove All'
    bl_description = 'Remove all motion references'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        data = obj.xray
        refs_count = len(data.motionrefs_collection)
        return bool(refs_count)

    def execute(self, context):
        obj = context.active_object
        obj.xray.motionrefs_collection.clear()
        utils.draw.redraw_areas()
        return {'FINISHED'}


class XRAY_OT_copy_motion_refs_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_motion_refs_list'
    bl_label = 'Copy Motion References'
    bl_description = 'Copy motion references list to clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.active_object
        lines = []
        saved_refs = set()
        for ref in obj.xray.motionrefs_collection:
            name = ref.name
            if not name:
                continue
            if name in saved_refs:
                continue
            unique_chars = set(name)
            if unique_chars == {' ', }:
                continue
            lines.append(name)
            saved_refs.add(name)
        bpy.context.window_manager.clipboard = '\n'.join(lines)
        return {'FINISHED'}


class XRAY_OT_paste_motion_refs_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.paste_motion_refs_list'
    bl_label = 'Past Motion References'
    bl_description = 'Paste motion references list from clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.active_object
        refs = obj.xray.motionrefs_collection
        used_refs = {ref.name for ref in obj.xray.motionrefs_collection}
        refs_data = bpy.context.window_manager.clipboard
        for line in refs_data.split('\n'):
            if not line:
                continue
            if line in used_refs:
                continue
            unique_chars = set(line)
            if unique_chars == {' ', }:
                continue
            ref = refs.add()
            ref.name = line
        utils.draw.redraw_areas()
        return {'FINISHED'}


class XRAY_OT_sort_motion_refs_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.sort_motion_refs_list'
    bl_label = 'Sort Motion References'
    bl_description = 'Sort motion references list'
    bl_options = {'UNDO'}

    sort_reverse = bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def draw(self, context):
        lay = self.layout
        lay.prop(self, 'sort_reverse', text='Reverse Sort', toggle=True)

    def execute(self, context):
        obj = context.active_object
        refs = obj.xray.motionrefs_collection

        used_refs = [ref.name for ref in refs]
        used_refs.sort()

        if self.sort_reverse:
            used_refs.reverse()

        refs.clear()

        for ref in used_refs:
            elem = refs.add()
            elem.name = ref

        utils.draw.redraw_areas()

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class XRAY_OT_add_motion_ref_from_file(bpy.types.Operator):
    bl_idname = 'io_scene_xray.add_motion_ref_from_file'
    bl_label = 'Add Motion Reference'
    bl_description = 'Add motion reference from file path'
    bl_options = {'UNDO'}

    init = False

    filter_glob = bpy.props.StringProperty(
        default='*.omf',
        options={'HIDDEN'}
    )
    directory = bpy.props.StringProperty(
        subtype='DIR_PATH',
        options={'SKIP_SAVE'}
    )
    files = bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        return True

    def draw(self, context):
        if not self.init:
            self.init = True
            space = context.space_data
            params = space.params
            prefs = utils.version.get_preferences()
            meshes_folders = utils.ie.get_pref_paths('meshes_folder')

            for mshs_folder in meshes_folders:
                if mshs_folder and os.path.exists(mshs_folder):

                    if isinstance(params.directory, bytes):
                        mshs_folder = bytes(mshs_folder, encoding='utf-8')

                    if not params.directory.startswith(mshs_folder):
                        params.directory = mshs_folder

    def execute(self, context):
        obj = context.active_object
        refs = obj.xray.motionrefs_collection
        meshes_folders = utils.ie.get_pref_paths('meshes_folder')

        mshs_folder = None
        for val in meshes_folders:
            if val:
                mshs_folder = val

        if not mshs_folder:
            self.report({'WARNING'}, 'Meshes folder not specified!')
            return {'FINISHED'}

        fail_count = 0
        for file in self.files:
            if not file.name.endswith('.omf'):
                continue
            file_path = os.path.join(self.directory, file.name)
            if not file_path.startswith(mshs_folder):
                fail_count += 1
                continue
            relative_path = file_path[len(mshs_folder) : ]
            motion_ref = os.path.splitext(relative_path)[0]
            if not motion_ref in refs:
                ref = refs.add()
                ref.name = motion_ref

        if fail_count:
            self.report(
                {'WARNING'},
                'Could not add {} references!'.format(fail_count)
            )

        utils.draw.redraw_areas()

        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    XRAY_OT_remove_all_motion_refs,
    XRAY_OT_copy_motion_refs_list,
    XRAY_OT_paste_motion_refs_list,
    XRAY_OT_sort_motion_refs_list,
    XRAY_OT_add_motion_ref_from_file
)


def register():
    utils.version.register_classes(classes)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
