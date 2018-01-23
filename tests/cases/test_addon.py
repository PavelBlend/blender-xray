from tests import utils

import bpy
import io_scene_xray


class TestAddon(utils.XRayTestCase):
    def test_blinfo(self):
        self.assertIsNotNone(io_scene_xray.bl_info)

    def test_enabled(self):
        self.assertIn('io_scene_xray', bpy.context.user_preferences.addons)

    def test_registry_register_bad_thing(self):
        from io_scene_xray import registry
        try:
            registry.register_thing(self)
            self.fail('Should fail with an exception')
        except Exception as ex:
            self.assertIn('Unsupported thing', str(ex))

    def test_registry_unregister_nonexistent_thing(self):
        from io_scene_xray import registry
        try:
            registry.unregister_thing(self)
            self.fail('Should fail with an exception')
        except Exception as ex:
            self.assertIn('is not registered', str(ex))

    def test_registry_unregister_nonown_thing(self):
        from io_scene_xray import registry
        try:
            thing = _Thing()
            registry.register_thing(thing, user='some-user')
            registry.unregister_thing(thing)
            self.fail('Should fail with an exception')
        except Exception as ex:
            self.assertIn('is not registered', str(ex))

class _Thing:
    def register(self):
        pass
