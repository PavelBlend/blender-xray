# blender modules
import bpy

# addon modules
from ... import contexts


class Level(object):
    def __init__(self):
        self.name = None
        self.active_material_index = 0

        self.visuals = []
        self.vbs_offsets = []
        self.ibs_offsets = []
        self.fp_vbs_offsets = []
        self.fp_ibs_offsets = []

        self.materials = {}
        self.saved_visuals = {}
        self.visuals_bbox = {}
        self.visuals_center = {}
        self.visuals_radius = {}
        self.sectors_indices = {}
        self.cform_objects = {}

        self.visuals_cache = VisualsCache()


class VertexBuffer(object):
    def __init__(self):
        self.vertex_count = 0
        self.vertex_format = None

        self.position = bytearray()
        self.normal = bytearray()
        self.tangent = bytearray()
        self.binormal = bytearray()
        self.color_hemi = bytearray()
        self.color_light = bytearray()
        self.color_sun = bytearray()
        self.uv = bytearray()
        self.uv_fix = bytearray()
        self.uv_lmap = bytearray()
        self.shader_data = bytearray()


class Visual(object):
    def __init__(self):
        self.shader_index = None


class VisualsCache:
    def __init__(self):
        self.bounds = {}
        self.children = {}

        # search children
        for obj in bpy.data.objects:
            if obj.name in bpy.context.scene.objects:
                self.children[obj.name] = []

        for child_obj in bpy.data.objects:
            if child_obj.name in bpy.context.scene.objects:
                parent = child_obj.parent

                if parent and parent.name in bpy.context.scene.objects:
                    self.children[parent.name].append(child_obj.name)


class ExportLevelContext(contexts.ExportMeshContext):
    def __init__(self):
        super().__init__()
