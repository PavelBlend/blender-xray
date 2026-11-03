import bpy
import io_scene_xray
import tests


class TestAddon(tests.utils.XRayTestCase):
    def test_blinfo(self):
        self.assertIsNotNone(io_scene_xray.bl_info)

    def test_enabled(self):
        if bpy.app.version >= (2, 80, 0):
            self.assertIn('io_scene_xray', bpy.context.preferences.addons)
        else:
            self.assertIn('io_scene_xray', bpy.context.user_preferences.addons)

    def test_registered_properties(self):
        class XRAY_PG_registered_props(bpy.types.PropertyGroup):
            foo = bpy.props.StringProperty(name='Foo')

        io_scene_xray.utils.version.register_classes(XRAY_PG_registered_props)
        try:
            self.assertIn('foo', XRAY_PG_registered_props.bl_rna.properties)
        finally:
            bpy.utils.unregister_class(XRAY_PG_registered_props)
