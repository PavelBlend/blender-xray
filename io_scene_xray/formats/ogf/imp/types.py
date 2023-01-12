class Visual(object):
    def __init__(self):
        self.file_path = None
        self.visual_id = None
        self.format_version = None
        self.model_type = None
        self.shader_id = None
        self.texture_id = None
        self.name = None
        self.vertices = []
        self.normals = []
        self.uvs = []
        self.uvs_lmap = None
        self.triangles = []
        self.indices_count = None
        self.indices = None
        self.weights = []
        self.hemi = None
        self.sun = None
        self.light = None
        self.fastpath = False
        self.vb_index = None
        self.is_root = None
        self.bpy_material = None
        self.arm_obj = None
        self.root_obj = None
        self.bones = []
        self.deform_bones = None
        self.motion_refs = None
        self.create_name = None
        self.create_time = None
        self.modif_name = None
        self.modif_time = None
        self.user_data = None
        self.lod = None
        self.bpy_image = None


class HierrarhyVisual(object):
    def __init__(self):
        self.index = None
        self.children = []
        self.children_count = None
