# header chunk id
HEADER = 0x1


class Chunks_v4:
    TEXTURE = 0x2
    VERTICES = 0x3
    INDICES = 0x4
    SWIDATA = 0x6
    VCONTAINER = 0x7
    ICONTAINER = 0x8
    CHILDREN = 0x9
    CHILDREN_L = 0xa
    LODDEF2 = 0xb
    TREEDEF2 = 0xc
    S_BONE_NAMES = 0xd
    S_MOTIONS = 0xe
    S_SMPARAMS = 0xf
    S_IKDATA = 0x10
    S_USERDATA = 0x11
    S_DESC = 0x12
    S_MOTION_REFS_0 = 0x13
    SWICONTAINER = 0x14
    GCONTAINER = 0x15
    FASTPATH = 0x16


class Chunks_v3:
    TEXTURE = 0x2
    TEXTURE_L = 0x3
    CHILD_REFS = 0x5
    BBOX = 0x6
    VERTICES = 0x7
    INDICES = 0x8
    LODDATA = 0x9    # not sure
    VCONTAINER = 0xa
    BSPHERE = 0xb
    CHILDREN_L = 0xc
    S_BONE_NAMES = 0xd
    S_MOTIONS = 0xe    # build 1469 - 1580
    DPATCH = 0xf    # guessed name
    LODS = 0x10    # guessed name
    CHILDREN = 0x11
    S_SMPARAMS = 0x12    # build 1469
    ICONTAINER = 0x13    # build 1865
    S_SMPARAMS_NEW = 0x14    # build 1472 - 1865
    LODDEF2 = 0x15    # build 1865
    TREEDEF2 = 0x16    # build 1865
    S_IKDATA_0 = 0x17    # build 1475 - 1580
    S_USERDATA = 0x18    # build 1537 - 1865
    S_IKDATA = 0x19    # build 1616 - 1829, 1844
    S_MOTIONS_NEW = 0x1a    # build 1616 - 1865
    S_DESC = 0x1b    # build 1844
    S_IKDATA_2 = 0x1c    # build 1842 - 1865
    S_MOTION_REFS = 0x1D    # build 1842


class ModelType_v4:
    NORMAL = 0x0
    HIERRARHY = 0x1
    PROGRESSIVE = 0x2
    SKELETON_ANIM = 0x3
    SKELETON_GEOMDEF_PM = 0x4
    SKELETON_GEOMDEF_ST = 0x5
    LOD = 0x6
    TREE_ST = 0x7
    PARTICLE_EFFECT = 0x8
    PARTICLE_GROUP = 0x9
    SKELETON_RIGID = 0xa
    TREE_PM = 0xb


class ModelType_v3:
    NORMAL = 0x0    # Fvisual
    HIERRARHY = 0x1    # FHierrarhyVisual
    PROGRESSIVE = 0x2    # FProgressiveFixedVisual
    SKELETON_GEOMDEF_PM = 0x3    # CSkeletonX_PM
    SKELETON_ANIM = 0x4    # CKinematics
    DETAIL_PATCH = 0x6    # FDetailPatch
    SKELETON_GEOMDEF_ST = 0x7    # CSkeletonX_ST
    CACHED = 0x8    # FCached
    PARTICLE = 0x9    # CPSVisual
    PROGRESSIVE2 = 0xa    # FProgressive
    LOD = 0xb    # FLOD build 1472 - 1865
    TREE = 0xc    # FTreeVisual build 1472 - 1865
    UNUSED_0 = 0xd    # CParticleEffect 1844
    UNUSED_1 = 0xe    # CParticleGroup 1844
    SKELETON_RIGID = 0xf    # CSkeletonRigid 1844


class VertexFormat:
    FVF_1L = 1 * 0x12071980
    FVF_2L = 2 * 0x12071980
    FVF_1L_CS = 0x1
    FVF_2L_CS = 0x2
    FVF_3L_CS = 0x3
    FVF_4L_CS = 0x4


FORMAT_VERSION_4 = 4
FORMAT_VERSION_3 = 3
SUPPORT_FORMAT_VERSIONS = (FORMAT_VERSION_4, FORMAT_VERSION_3)
