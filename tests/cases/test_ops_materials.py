import os
import bpy
import tests


class TestOpsMaterials(tests.utils.XRayTestCase):

    def test_switch_render_general(self):
        if bpy.app.version >= (2, 80, 0):
            return

        objs = self.create_objects()

        bpy.ops.io_scene_xray.switch_render(mode='ACTIVE_MATERIAL')
        bpy.ops.io_scene_xray.switch_render(mode='ACTIVE_OBJECT')
        bpy.ops.io_scene_xray.switch_render(mode='SELECTED_OBJECTS')
        bpy.ops.io_scene_xray.switch_render(mode='ALL_OBJECTS')
        bpy.ops.io_scene_xray.switch_render(mode='ALL_MATERIALS')

    def test_switch_render_without_materials(self):
        if bpy.app.version >= (2, 80, 0):
            return

        objs = self.create_objects_without_materials()

        bpy.ops.io_scene_xray.switch_render(mode='ACTIVE_MATERIAL')
        bpy.ops.io_scene_xray.switch_render(mode='ACTIVE_OBJECT')
        bpy.ops.io_scene_xray.switch_render(mode='SELECTED_OBJECTS')
        bpy.ops.io_scene_xray.switch_render(mode='ALL_OBJECTS')
        bpy.ops.io_scene_xray.switch_render(mode='ALL_MATERIALS')

    def test_switch_render_without_objects(self):
        if bpy.app.version >= (2, 80, 0):
            return

        bpy.ops.io_scene_xray.switch_render(mode='ACTIVE_MATERIAL')
        bpy.ops.io_scene_xray.switch_render(mode='ACTIVE_OBJECT')
        bpy.ops.io_scene_xray.switch_render(mode='SELECTED_OBJECTS')
        bpy.ops.io_scene_xray.switch_render(mode='ALL_OBJECTS')
        bpy.ops.io_scene_xray.switch_render(mode='ALL_MATERIALS')

    def convert_to_internal_or_cycles(self):
        bpy.ops.io_scene_xray.convert_to_internal(mode='ACTIVE_MATERIAL')
        bpy.ops.io_scene_xray.convert_to_cycles(mode='ACTIVE_MATERIAL')

        bpy.ops.io_scene_xray.convert_to_internal(mode='ACTIVE_OBJECT')
        bpy.ops.io_scene_xray.convert_to_cycles(mode='ACTIVE_OBJECT')

        bpy.ops.io_scene_xray.convert_to_internal(mode='SELECTED_OBJECTS')
        bpy.ops.io_scene_xray.convert_to_cycles(mode='SELECTED_OBJECTS')

        bpy.ops.io_scene_xray.convert_to_internal(mode='ALL_OBJECTS')
        bpy.ops.io_scene_xray.convert_to_cycles(mode='ALL_OBJECTS')

        bpy.ops.io_scene_xray.convert_to_internal(mode='ALL_MATERIALS')
        bpy.ops.io_scene_xray.convert_to_cycles(mode='ALL_MATERIALS')

    def test_convert_general(self):
        if bpy.app.version >= (2, 80, 0):
            return

        objs = self.create_objects()

        self.convert_to_internal_or_cycles()

    def test_convert_without_materials(self):
        if bpy.app.version >= (2, 80, 0):
            return

        objs = self.create_objects_without_materials()

        self.convert_to_internal_or_cycles()

    def test_convert_without_objects(self):
        if bpy.app.version >= (2, 80, 0):
            return

        self.convert_to_internal_or_cycles()

    def test_create_material(self):
        mat = bpy.data.materials.new('test')

        bpy.ops.io_scene_xray.create_material(
            material_name=mat.name,
            filepath=os.path.join('test', 'folder', 'tex.dds')
        )

    def create_objects(self):
        objs = []
        bpy.context.scene.render.engine = 'CYCLES'

        for i in range(3):
            name = 'test_{}'.format(i)

            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)
            mat_1 = bpy.data.materials.new(name)
            mat_2 = bpy.data.materials.new(name)

            tests.utils.link_object(obj)
            obj.location.x = i * 4
            mesh.from_pydata(
                ((1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)),
                (),
                ((0, 1, 2, 3), )
            )
            mesh.materials.append(mat_1)
            mesh.materials.append(mat_2)

            objs.append(obj)

            for mat in (mat_1, mat_2):
                mat.use_nodes = True

                node_tree = mat.node_tree
                nodes = node_tree.nodes
                nodes.clear()

                image = bpy.data.images.new(name, 0, 0)
                image.source = 'FILE'

                image_node = nodes.new('ShaderNodeTexImage')
                shader_node = nodes.new('ShaderNodeBsdfDiffuse')
                output_node = nodes.new('ShaderNodeOutputMaterial')

                image_node.image = image

                node_tree.links.new(image_node.outputs['Color'], shader_node.inputs['Color'])
                node_tree.links.new(shader_node.outputs['BSDF'], output_node.inputs['Surface'])

        tests.utils.set_active_object(objs[0])
        tests.utils.select_object(objs[0])
        tests.utils.select_object(objs[1])

        bpy.ops.object.material_slot_add()

        return objs

    def create_objects_without_materials(self):
        objs = []

        for i in range(3):
            name = 'test'
            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)
            tests.utils.link_object(obj)
            objs.append(obj)

        tests.utils.set_active_object(objs[0])
        tests.utils.select_object(objs[0])
        tests.utils.select_object(objs[1])

        bpy.ops.object.material_slot_add()

        return objs
