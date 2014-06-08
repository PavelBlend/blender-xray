class Chunks:
    class Object:
        MAIN = 0x7777
        VERSION = 0x0900
        FLAGS = 0x0903
        SURFACES2 = 0x0907
        MESHES = 0x0910
        USERDATA = 0x0912
        BONES1 = 0x0921
        REVISION = 0x0922
        LOD_REF = 0x0925

    class Mesh:
        VERSION = 0x1000
        MESHNAME = 0x1001
        FLAGS = 0x1002
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
        MATERIAL = 0x0004
        SHAPE = 0x0005
        IK_JOINT = 0x0006
        MASS_PARAMS = 0x0007
        IK_FLAGS = 0x0008
        BREAK_PARAMS = 0x0009
        FRICTION = 0x0010
