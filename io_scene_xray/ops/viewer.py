# standart modules
import os
import time

# blender modules
import bpy

# addon modules
from .. import log
from .. import utils
from .. import text


KB = 1024
MB = KB ** 2


class XRAY_UL_viewer_list_item(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item.is_dir:
            layout.label(text=item.name, icon='FILE_FOLDER')
        else:
            row = layout.row()
            if not item.select:
                row.active = False
            row.prop(item, 'select', text='')
            row.label(text=item.name, icon='FILE')

            if context.scene.xray.viewer.show_size:
                row = row.row()
                row.alignment = 'RIGHT'
                if item.size > MB:
                    row.label(text='{:.1f} MB'.format(item.size / MB))
                elif item.size > KB:
                    row.label(text='{:.1f} KB'.format(item.size / KB))
                else:
                    row.label(text='{} Bytes'.format(item.size))

            if context.scene.xray.viewer.show_date:
                row = row.row()
                row.alignment = 'RIGHT'
                row.label(text=item.date)


def get_current_objects():
    objs = set()
    for obj in bpy.data.objects:
        objs.add(obj.name)
    return objs


def remove_preview_data():
    scene = bpy.context.scene
    imported_objects = scene.get('imported_objects')
    materials = set()
    images = set()
    textures = set()
    actions = set()
    meshes = set()
    armatures = set()
    if imported_objects:
        for obj_name in imported_objects:
            obj = bpy.data.objects.get(obj_name)
            if obj:
                if obj.type == 'MESH':
                    mesh = obj.data
                    meshes.add(mesh)
                    for material in mesh.materials:
                        if material:
                            materials.add(material)
                            if utils.version.IS_28:
                                for node in material.node_tree.nodes:
                                    if node.type == 'TEX_IMAGE':
                                        image = node.image
                                        if image:
                                            images.add(image)
                            else:
                                for texture_slot in material.texture_slots:
                                    if not texture_slot:
                                        continue
                                    texture = texture_slot.texture
                                    textures.add(texture)
                                    if texture.type == 'IMAGE':
                                        image = texture.image
                                        if image:
                                            images.add(image)
                elif obj.type == 'ARMATURE':
                    armature = obj.data
                    armatures.add(armature)
                    for motion in obj.xray.motions_collection:
                        action = bpy.data.actions.get(motion.name)
                        if action:
                            actions.add(action)
                bpy.data.objects.remove(obj)
    data_list = (
        (bpy.data.meshes, meshes),
        (bpy.data.materials, materials),
        (bpy.data.textures, textures),
        (bpy.data.images, images),
        (bpy.data.armatures, armatures)
    )
    for bpy_data, data_set in data_list:
        for data in data_set:
            if not data.users:
                bpy_data.remove(data)
    used_actions = set()
    for obj in bpy.data.objects:
        for motion in obj.xray.motions_collection:
            action = bpy.data.actions.get(motion.name)
            if action:
                used_actions.add(action.name)
    for action in actions:
        if not action.name in used_actions:
            utils.version.remove_action(action)


def import_file(file):
    scene = bpy.context.scene
    viewer = scene.xray.viewer
    path = file.path
    directory = os.path.dirname(path)
    prefs = utils.version.get_preferences()
    log_prev_text = log.create_bpy_text
    log.create_bpy_text = False

    if not os.path.isfile(path):
        return

    if path.endswith('.object'):
        bpy.ops.xray_import.object(
            directory=directory,
            files=[{'name': file.name}],
            import_motions=viewer.import_motions,
            mesh_split_by_materials=prefs.object_mesh_split_by_mat,
            fmt_version=prefs.sdk_version
        )

    elif path.endswith('.ogf'):
        bpy.ops.xray_import.ogf(
            directory=directory,
            files=[{'name': file.name}],
            import_motions=viewer.import_motions
        )

    elif path.endswith('.dm'):
        bpy.ops.xray_import.dm(
            directory=directory,
            files=[{'name': file.name}],
        )

    elif path.endswith('.details'):
        bpy.ops.xray_import.details(
            directory=directory,
            files=[{'name': file.name}],
            details_models_in_a_row=True,
            load_slots=False
        )

    else:
        if viewer.ignore_ext:
            imported = False

            # try *.object import
            try:
                bpy.ops.xray_import.object(
                    directory=directory,
                    files=[{'name': file.name}],
                    import_motions=viewer.import_motions,
                    mesh_split_by_materials=prefs.object_mesh_split_by_mat,
                    fmt_version=prefs.sdk_version
                )
                imported = True
            except:
                pass

            # try *.ogf import
            if not imported:
                try:
                    bpy.ops.xray_import.ogf(
                        directory=directory,
                        files=[{'name': file.name}],
                        import_motions=viewer.import_motions
                    )
                    imported = True
                except:
                    pass

            # try *.dm import
            if not imported:
                try:
                    bpy.ops.xray_import.dm(
                        directory=directory,
                        files=[{'name': file.name}],
                    )
                    imported = True
                except:
                    pass

            # try *.details import
            if not imported:
                try:
                    bpy.ops.xray_import.details(
                        directory=directory,
                        files=[{'name': file.name}],
                        details_models_in_a_row=True,
                        load_slots=False
                    )
                    imported = True
                except:
                    pass

    log.create_bpy_text = log_prev_text


ext_ignore = [
    '.dds',
    '.tga',
    '.thm',
    '.ogm',
    '.wav',
    '.ogg',
    '.spawn',
    '.graph',
    '.ai'
]


def update_file(self, context):
    scene = context.scene
    viewer = scene.xray.viewer
    files_count = len(viewer.files)
    if viewer.files_index >= files_count:
        return
    file = viewer.files[viewer.files_index]
    if file.is_dir or viewer.is_preview_folder_mode:
        if viewer.is_preview_folder_mode:
            viewer.is_preview_folder_mode = False
        else:
            scene.xray.viewer.folder = file.path
            update_file_list(scene.xray.viewer.folder)
            viewer.is_preview_folder_mode = True
            viewer.files_index = 0
        return
    ext = os.path.splitext(file.name)[-1]
    if ext in ext_ignore:
        return
    remove_preview_data()
    old_objects = get_current_objects()
    import_file(file)
    new_objects = get_current_objects()
    imported_objects = old_objects ^ new_objects
    scene['imported_objects'] = list(imported_objects)
    bpy.ops.object.select_all(action='DESELECT')
    utils.version.set_mesh_objects_select(imported_objects, True)
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx = bpy.context.copy()
            ctx['area'] = area
            ctx['region'] = area.regions[-1]
            bpy.ops.view3d.view_selected(ctx)
    utils.version.set_mesh_objects_select(imported_objects, False)


def update_file_list(directory, active_folder=None):
    scene = bpy.context.scene
    viewer = scene.xray.viewer
    viewer.files.clear()
    viewer_files = viewer.files
    dirs = []
    files = []
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if not os.path.isfile(file_path):
            dirs.append((file_name, file_path))
        else:
            _, ext = os.path.splitext(file_name)
            ext = ext.lower()
            if viewer.ignore_ext:
                added_file = True
            elif ext == '.object' and viewer.use_object:
                added_file = True
            elif ext == '.ogf' and viewer.use_ogf:
                added_file = True
            elif ext == '.dm' and viewer.use_dm:
                added_file = True
            elif ext == '.details' and viewer.use_details:
                added_file = True
            else:
                added_file = False
            if added_file:
                files.append((file_name, file_path))
    is_dir = (True, False)
    file_groups = {}
    for index, file_list in enumerate((dirs, files)):
        for file_name, file_path in file_list:
            is_directory = is_dir[index]
            size = os.path.getsize(file_path)
            create_time = os.path.getctime(file_path)
            local_time = time.localtime(create_time)
            time_str = time.strftime('%Y.%m.%d %H:%M:%S', local_time)
            if is_directory:
                ext = ''
            else:
                ext = os.path.splitext(file_name)[-1]
                if not ext:
                    ext = '.'
            if not viewer.group_by_ext:
                file_groups.setdefault(is_directory, []).append((
                    file_name,
                    file_path,
                    is_directory,
                    size,
                    time_str
                ))
            else:
                file_groups.setdefault(ext, []).append((
                    file_name,
                    file_path,
                    is_directory,
                    size,
                    time_str
                ))
    file_index = 0
    sort_by_name = lambda item: item[0]
    if viewer.sort == 'NAME':
        key = sort_by_name
    elif viewer.sort == 'SIZE':
        key = lambda item: item[3]
    elif viewer.sort == 'DATE':
        key = lambda item: item[4]
    groups_keys = list(file_groups.keys())
    if True in file_groups:
        dir_index = groups_keys.index(True)
        groups_keys.pop(dir_index)
        groups_keys.insert(0, True)
    for group_key in groups_keys:
        files_list = file_groups[group_key]
        if group_key:    # folders
            files_list.sort(key=sort_by_name, reverse=viewer.sort_reverse)
        else:
            files_list.sort(key=key, reverse=viewer.sort_reverse)
        for file_name, file_path, is_directory, size, date in files_list:
            file = viewer_files.add()
            file.name = file_name
            file.path = file_path
            file.size = size
            file.date = date
            file.is_dir = is_directory
            if is_directory:
                if active_folder:
                    if file_name == active_folder:
                        viewer.files_index = file_index
            file_index += 1


def update_file_list_ext(self, context):
    scene = context.scene
    update_file_list(scene.xray.viewer.folder)


op_props = {
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE', 'HIDDEN'}
    ),
}


class XRAY_OT_viewer_open_folder(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.viewer_open_folder'
    bl_label = 'Open Folder'
    bl_options = {'REGISTER'}

    if not utils.version.IS_28:
        for prop_name, prop_value in op_props.items():
            exec('{0} = op_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        scene = context.scene
        scene.xray.viewer.folder = self.directory
        update_file_list(scene.xray.viewer.folder)
        utils.draw.redraw_areas()
        self.report({'INFO'}, text.get_text(text.warn.ready))
        return {'FINISHED'}

    def invoke(self, context, event):    # pragma: no cover
        wm = context.window_manager
        wm.fileselect_add(operator=self)
        return {'RUNNING_MODAL'}


class XRAY_OT_viewer_open_current_folder(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.viewer_open_current_folder'
    bl_label = 'Open Current Folder'
    bl_options = {'REGISTER'}

    @utils.set_cursor_state
    def execute(self, context):
        scene = context.scene
        folder = scene.xray.viewer.folder
        folder = os.path.realpath(folder)
        os.startfile(folder)
        return {'FINISHED'}


class XRAY_OT_viewer_close_folder(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.viewer_close_folder'
    bl_label = 'Close Folder'
    bl_options = {'REGISTER'}

    @utils.set_cursor_state
    def execute(self, context):
        scene = context.scene
        remove_preview_data()
        scene.xray.viewer.folder = ''
        scene.xray.viewer.files.clear()
        utils.draw.redraw_areas()
        return {'FINISHED'}


class XRAY_OT_viewer_preview_folder(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.viewer_preview_folder'
    bl_label = 'Preview Folder'
    bl_options = {'REGISTER'}

    @utils.set_cursor_state
    def execute(self, context):
        scene = context.scene
        viewer_folder = scene.xray.viewer.folder
        if viewer_folder:
            if viewer_folder[-1] == os.sep:
                viewer_folder = viewer_folder[0 : -1]
            active_folder = os.path.basename(viewer_folder)
            viewer_folder = os.path.dirname(viewer_folder)
            scene.xray.viewer.folder = viewer_folder
            scene.xray.viewer.is_preview_folder_mode = True
            update_file_list(scene.xray.viewer.folder, active_folder)
            remove_preview_data()
        return {'FINISHED'}


op_import_items = (
    ('IMPORT_ALL', 'Import All', ''),
    ('IMPORT_SELECTED', 'Import Selected', ''),
    ('IMPORT_ACTIVE', 'Import Active', '')
)
op_import_props = {
    'mode': bpy.props.EnumProperty(name='Mode', items=op_import_items),
}


class XRAY_OT_viewer_import_files(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.viewer_import_files'
    bl_label = 'Import Files'
    bl_options = {'REGISTER'}

    if not utils.version.IS_28:
        for prop_name, prop_value in op_import_props.items():
            exec('{0} = op_import_props.get("{0}")'.format(prop_name))

    @utils.set_cursor_state
    def execute(self, context):
        scene = context.scene
        viewer = scene.xray.viewer
        remove_preview_data()
        count = 0
        if self.mode == 'IMPORT_SELECTED':
            for file in viewer.files:
                if file.select:
                    import_file(file)
                    count += 1
        elif self.mode == 'IMPORT_ALL':
            for file in viewer.files:
                import_file(file)
                count += 1
        elif self.mode == 'IMPORT_ACTIVE':
            file = viewer.files[viewer.files_index]
            import_file(file)
            count += 1
        if scene.get('imported_objects'):
            scene['imported_objects'].clear()
            del scene['imported_objects']
        self.report(
            {'INFO'},
            '{0}: {1}'.format(text.get_text(text.warn.imported), count)
        )
        return {'FINISHED'}


op_select_items = (
    ('SELECT_ALL', 'Select All', ''),
    ('DESELECT_ALL', 'Deselect All', ''),
    ('INVERT_SELECTION', 'Invert Selection', '')
)
op_select_props = {
    'mode': bpy.props.EnumProperty(name='Mode', items=op_select_items),
}


class XRAY_OT_viewer_select_files(utils.ie.BaseOperator):
    bl_idname = 'io_scene_xray.viewer_select_files'
    bl_label = 'Select'
    bl_options = {'REGISTER'}

    if not utils.version.IS_28:
        for prop_name, prop_value in op_select_props.items():
            exec('{0} = op_select_props.get("{0}")'.format(prop_name))

    def execute(self, context):
        scene = context.scene
        files = scene.xray.viewer.files
        count = 0
        if self.mode == 'SELECT_ALL':
            for file in files:
                file.select = True
                count += 1
        elif self.mode == 'DESELECT_ALL':
            for file in files:
                file.select = False
                count += 1
        elif self.mode == 'INVERT_SELECTION':
            for file in files:
                file.select = not file.select
                count += 1
        self.report(
            {'INFO'},
            '{0}: {1}'.format(text.get_text(text.warn.сhanged), count)
        )
        return {'FINISHED'}


viewer_file_props = {
    'name': bpy.props.StringProperty(name='Name'),
    'path': bpy.props.StringProperty(name='Path'),
    'select': bpy.props.BoolProperty(name='Select', default=True),
    'is_dir': bpy.props.BoolProperty(name='Directory'),
    'size': bpy.props.IntProperty(name='Size'),
    'date': bpy.props.StringProperty(name='Date')
}


class XRayViwerFileProperties(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in viewer_file_props.items():
            exec('{0} = viewer_file_props.get("{0}")'.format(prop_name))


sort_items = (
    ('NAME', 'Name', ''),
    ('SIZE', 'Size', ''),
    ('DATE', 'Date', '')
)
scene_viewer_props = {
    'files': bpy.props.CollectionProperty(type=XRayViwerFileProperties),
    'files_index': bpy.props.IntProperty(update=update_file),
    'folder': bpy.props.StringProperty(),
    'is_preview_folder_mode': bpy.props.BoolProperty(default=False),
    'import_motions': bpy.props.BoolProperty(
        default=False,
        name='Import Motions'
    ),
    'ignore_ext': bpy.props.BoolProperty(
        default=False,
        name='Ignore Extension',
        update=update_file_list_ext
    ),
    'show_size': bpy.props.BoolProperty(default=False, name='Show Size'),
    'show_date': bpy.props.BoolProperty(default=False, name='Show Date'),
    'sort': bpy.props.EnumProperty(
        name='Sort',
        items=sort_items,
        update=update_file_list_ext,
        default='NAME'
    ),
    'group_by_ext': bpy.props.BoolProperty(
        default=False,
        name='Group by Extension',
        update=update_file_list_ext
    ),
    'sort_reverse': bpy.props.BoolProperty(
        default=False,
        name='Reverse Sort',
        update=update_file_list_ext
    ),
    'use_object': bpy.props.BoolProperty(
        default=True,
        name='Object',
        update=update_file_list_ext
    ),
    'use_ogf': bpy.props.BoolProperty(
        default=True,
        name='Ogf',
        update=update_file_list_ext
    ),
    'use_dm': bpy.props.BoolProperty(
        default=True,
        name='Dm',
        update=update_file_list_ext
    ),
    'use_details': bpy.props.BoolProperty(
        default=True,
        name='Details',
        update=update_file_list_ext
    )
}


class XRaySceneViewerProperties(bpy.types.PropertyGroup):
    if not utils.version.IS_28:
        for prop_name, prop_value in scene_viewer_props.items():
            exec('{0} = scene_viewer_props.get("{0}")'.format(prop_name))


classes = (
    (XRAY_UL_viewer_list_item, None),
    (XRayViwerFileProperties, viewer_file_props),
    (XRaySceneViewerProperties, scene_viewer_props),
    (XRAY_OT_viewer_close_folder, None),
    (XRAY_OT_viewer_preview_folder, None),
    (XRAY_OT_viewer_open_folder, op_props),
    (XRAY_OT_viewer_open_current_folder, None),
    (XRAY_OT_viewer_import_files, op_import_props),
    (XRAY_OT_viewer_select_files, op_select_props)
)


def register():
    for operator, props in classes:
        if props:
            utils.version.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
