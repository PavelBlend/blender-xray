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
            if bpy.app.version >= (2, 80, 0):
                annotated: bpy.props.BoolProperty(name='Annotated')
            assigned = bpy.props.StringProperty(name='Assigned')

        io_scene_xray.utils.version.register_classes(XRAY_PG_registered_props)
        try:
            props = XRAY_PG_registered_props.bl_rna.properties
            self.assertIn('assigned', props)
            if bpy.app.version >= (2, 80, 0):
                self.assertIn('annotated', props)
        finally:
            bpy.utils.unregister_class(XRAY_PG_registered_props)
