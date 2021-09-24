# standart modules
import os

# blender modules
import bpy

# addon props
from . import version_utils


class XRAY_UL_viewer_list_item(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item.is_dir:
            icon = 'FILE_FOLDER'
        else:
            icon = 'FILE'
        layout.label(text=item.name, icon=icon)


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
                            if version_utils.IS_28:
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
            bpy.data.actions.remove(action)


def update_file(self, context):
    scene = context.scene
    viewer = scene.xray.viewer
    file = viewer.files[viewer.files_index]
    if file.is_dir:
        scene.xray.viewer.folder = file.path
        update_file_list(scene.xray.viewer.folder)
    remove_preview_data()
    path = file.path
    directory = os.path.dirname(path)
    old_objects = get_current_objects()
    if path.endswith('.object'):
        bpy.ops.xray_import.object(
            directory=directory,
            files=[{'name': file.name}],
        )
    elif path.endswith('.ogf'):
        bpy.ops.xray_import.ogf(
            directory=directory,
            files=[{'name': file.name}],
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
            load_slots=False
        )
    new_objects = get_current_objects()
    imported_objects = old_objects ^ new_objects
    scene['imported_objects'] = list(imported_objects)
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx = bpy.context.copy()
            ctx['area'] = area
            ctx['region'] = area.regions[-1]
            bpy.ops.view3d.view_all(ctx, center=False) 


ext_list = ['.ogf', '.object', '.dm', '.details']


def update_file_list(directory):
    scene = bpy.context.scene
    scene.xray.viewer.files.clear()
    viewer_files = scene.xray.viewer.files
    dirs = []
    files = []
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if not os.path.isfile(file_path):
            dirs.append((file_name, file_path))
        else:
            _, ext = os.path.splitext(file_name)
            if not (ext in ext_list):
                continue
            files.append((file_name, file_path))
    dirs.sort()
    files.sort()
    is_dir = (True, False)
    for index, file_list in enumerate((dirs, files)):
        for file_name, file_path in file_list:
            file = viewer_files.add()
            file.name = file_name
            file.path = file_path
            file.is_dir = is_dir[index]


op_props = {
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE', 'HIDDEN'}
    ),
}


class XRAY_OT_viewer_open_folder(bpy.types.Operator):
    bl_idname = 'io_scene_xray.viewer_open_folder'
    bl_label = 'Open Folder'
    bl_options = {'REGISTER'}

    if not version_utils.IS_28:
        for prop_name, prop_value in op_props.items():
            exec('{0} = op_props.get("{0}")'.format(prop_name))

    def execute(self, context):
        scene = context.scene
        scene.xray.viewer.folder = self.directory
        update_file_list(scene.xray.viewer.folder)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(operator=self)
        return {'RUNNING_MODAL'}


class XRAY_OT_viewer_close_folder(bpy.types.Operator):
    bl_idname = 'io_scene_xray.viewer_close_folder'
    bl_label = 'Close Folder'
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        scene.xray.viewer.folder = ''
        scene.xray.viewer.files.clear()
        return {'FINISHED'}


class XRAY_OT_viewer_preview_folder(bpy.types.Operator):
    bl_idname = 'io_scene_xray.viewer_preview_folder'
    bl_label = 'Preview Folder'
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        viewer_folder = scene.xray.viewer.folder
        if viewer_folder:
            if viewer_folder[-1] == os.sep:
                viewer_folder = viewer_folder[0 : -1]
            viewer_folder = os.path.dirname(viewer_folder)
            scene.xray.viewer.folder = viewer_folder
            update_file_list(scene.xray.viewer.folder)
            remove_preview_data()
        return {'FINISHED'}


viewer_file_props = {
    'name': bpy.props.StringProperty(name='Name'),
    'path': bpy.props.StringProperty(name='Path'),
    'is_dir': bpy.props.BoolProperty(name='Directory')
}


class XRayViwerFileProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in viewer_file_props.items():
            exec('{0} = viewer_file_props.get("{0}")'.format(prop_name))


scene_viewer_props = {
    'files': bpy.props.CollectionProperty(type=XRayViwerFileProperties),
    'files_index': bpy.props.IntProperty(update=update_file),
    'folder': bpy.props.StringProperty()
}


class XRaySceneViewerProperties(bpy.types.PropertyGroup):
    if not version_utils.IS_28:
        for prop_name, prop_value in scene_viewer_props.items():
            exec('{0} = scene_viewer_props.get("{0}")'.format(prop_name))


classes = (
    (XRAY_UL_viewer_list_item, None),
    (XRayViwerFileProperties, viewer_file_props),
    (XRaySceneViewerProperties, scene_viewer_props),
    (XRAY_OT_viewer_close_folder, None),
    (XRAY_OT_viewer_preview_folder, None),
    (XRAY_OT_viewer_open_folder, op_props)
)


def register():
    for operator, props in classes:
        if props:
            version_utils.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
