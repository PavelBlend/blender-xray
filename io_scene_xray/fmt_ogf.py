class Chunks:
    HEADER = 0x1
    TEXTURE = 0x2
    VERTICES = 0x3
    INDICES = 0x4
    SWIDATA = 0x6
    CHILDREN = 0x9
    S_BONE_NAMES = 0xd
    S_MOTIONS = 0xe
    S_SMPARAMS = 0xf
    S_IKDATA = 0x10
    S_USERDATA = 0x11
    S_DESC = 0x12
    S_MOTION_REFS_0 = 0x13


class ModelType:
    SKELETON_ANIM = 0x3
    SKELETON_GEOMDEF_ST = 0x5
    SKELETON_RIGID = 0xa


class VertexFormat:
    FVF_1L = 0x12071980
    FVF_2L = 0x240e3300
    FVF_1L_CS = 0x1
    FVF_2L_CS = 0x2
    FVF_3L_CS = 0x3
    FVF_4L_CS = 0x4
