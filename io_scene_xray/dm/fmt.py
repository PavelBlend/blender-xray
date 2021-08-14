class DetailMesh:
    def __init__(self):
        self.vertices_count = None
        self.indices_count = None
        self.uv_map_name = 'Texture'
        self.bpy_mesh = None
        self.bpy_material = None


class DetailModel:
    def __init__(self):
        self.shader = None
        self.texture = None
        self.mode = None
        self.mesh = DetailMesh()


VERTICES_COUNT_LIMIT = 0x10000
