# blender modules
import bpy

# addon modules
from .. import version_utils


mode_items = (
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', ''),
    ('ALL_DATA', 'All Data', '')
)
data_items = (
    ('OBJECTS', 'Objects', ''),
    ('MESHES', 'Meshes', ''),
    ('MATERIALS', 'Materials', ''),
    ('TEXTURES', 'Textures', ''),
    ('IMAGES', 'Images', ''),
    ('ARMATURES', 'Armatures', ''),
    ('ACTIONS', 'Actions', ''),
    ('ALL', 'All', '')
)
fake_items = (
    ('TRUE', 'True', ''),
    ('FALSE', 'False', ''),
    ('INVERT', 'Invert', '')
)
op_props = {
    'mode': bpy.props.EnumProperty(
        default='SELECTED_OBJECTS',
        items=mode_items
    ),
    'data': bpy.props.EnumProperty(
        default={'ALL'},
        items=data_items,
        options={'ENUM_FLAG'}
    ),
    'fake_user': bpy.props.EnumProperty(
        default='TRUE',
        items=fake_items
    )
}


class XRAY_OT_change_fake_user(bpy.types.Operator):
    bl_idname = 'io_scene_xray.change_fake_user'
    bl_label = 'Change Fake User'
    bl_options = {'REGISTER', 'UNDO'}

    props = op_props

    if not version_utils.IS_28:
        for prop_name, prop_value in props.items():
            exec('{0} = props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

        change_column = column.column(align=True)
        change_column.active = self.mode != 'ALL_DATA'
        change_column.label(text='Change:')
        change_column.prop(self, 'data', expand=True)

        column.label(text='Fake User:')
        column.row().prop(self, 'fake_user', expand=True)

    def set_fake_user(self, data_block):
        if self.fake_user == 'TRUE':
            data_block.use_fake_user = True
        elif self.fake_user == 'FALSE':
            data_block.use_fake_user = False
        else:
            data_block.use_fake_user = not data_block.use_fake_user

    def report_change(self, change_count):
        self.report({'INFO'}, 'Changed data blocks: {}'.format(change_count))

    def execute(self, context):
        input_objects = set()
        cycles_compatible_rends = (
            'CYCLES',
            'BLENDER_EEVEE',
            'BLENDER_WORKBENCH'
        )
        interal_compatible_rends = ('BLENDER_RENDER', 'BLENDER_GAME')
        rend = context.scene.render.engine
        change_data_blocks_count = 0

        if self.mode == 'ACTIVE_OBJECT':
            obj = context.object
            if obj:
                input_objects.add(obj)

        elif self.mode == 'SELECTED_OBJECTS':
            for obj in context.selected_objects:
                input_objects.add(obj)

        elif self.mode == 'ALL_OBJECTS':
            for obj in bpy.data.objects:
                input_objects.add(obj)

        else:
            data_collections = {
                bpy.data.objects,
                bpy.data.meshes,
                bpy.data.materials,
                bpy.data.images,
                bpy.data.armatures,
                bpy.data.actions
            }
            if rend in interal_compatible_rends:
                data_collections.add(bpy.data.textures)
            for data_collection in data_collections:
                for data_block in data_collection:
                    self.set_fake_user(data_block)
                    change_data_blocks_count += 1
            self.report_change(change_data_blocks_count)
            return {'FINISHED'}

        objects = set()
        meshes = set()
        materials = set()
        textures = set()
        images = set()
        armatures = set()
        actions = set()

        for obj in input_objects:
            # collect objects
            objects.add(obj)
            # collect meshes
            if obj.type == 'MESH':
                meshes.add(obj.data)
            # collect armatures
            elif obj.type == 'ARMATURE':
                armatures.add(obj.data)
            # collect actions
            for motion in obj.xray.motions_collection:
                action_name = motion.name
                action = bpy.data.actions.get(action_name)
                if action:
                    actions.add(action)
            # collect materials
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if mat:
                    materials.add(mat)
                    if rend in cycles_compatible_rends:
                        # collect images
                        for node in mat.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                img = node.image
                                if img:
                                    images.add(img)
                    elif rend in interal_compatible_rends:
                        # collect textures
                        for tex_slot in mat.texture_slots:
                            if tex_slot:
                                tex = tex_slot.texture
                                if tex:
                                    textures.add(tex)
                                    if tex.type == 'IMAGE':
                                        # collect images
                                        img = tex.image
                                        if img:
                                            images.add(img)

        data_blocks = set()

        if {'ALL', 'OBJECTS'} & self.data:
            data_blocks.update(objects)

        if {'ALL', 'MESHES'} & self.data:
            data_blocks.update(meshes)

        if {'ALL', 'MATERIALS'} & self.data:
            data_blocks.update(materials)

        if {'ALL', 'TEXTURES'} & self.data:
            data_blocks.update(textures)

        if {'ALL', 'IMAGES'} & self.data:
            data_blocks.update(images)

        if {'ALL', 'ARMATURES'} & self.data:
            data_blocks.update(armatures)

        if {'ALL', 'ACTIONS'} & self.data:
            data_blocks.update(actions)

        for data_block in data_blocks:
            self.set_fake_user(data_block)
            change_data_blocks_count += 1

        self.report_change(change_data_blocks_count)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register():
    version_utils.register_operators(XRAY_OT_change_fake_user)


def unregister():
    bpy.utils.unregister_class(XRAY_OT_change_fake_user)
