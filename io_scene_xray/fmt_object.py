class Chunks:
    class Object:
        MAIN = 0x7777
        VERSION = 0x0900
        SURFACES2 = 0x0907
        MESHES = 0x0910
        BONES1 = 0x0921

    class Mesh:
        VERSION = 0x1000
        MESHNAME = 0x1001
        VERTS = 0x1005
        FACES = 0x1006
        VMREFS = 0x1008
        SFACE = 0x1009
        VMAPS2 = 0x1012
        SG = 0x1013

    class Bone:
        VERSION = 0x0001
        DEF = 0x0002
        BIND_POSE = 0x0003
