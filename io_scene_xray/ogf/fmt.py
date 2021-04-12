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


class Chunks_v2:
    TEXTURE_L = 0x3
    BBOX = 0x6
    INDICES = 0x8
    VCONTAINER = 0xb
    ICONTAINER = 0xffff    # 0xffff - unknown value (replace)
    BSPHERE = 0xc
    CHILDREN_L = 0xd


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
    UNKNOWN_0xC = 0xc


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


class ModelType_v2:
    NORMAL = 0x0
    HIERRARHY = 0x1


class VertexFormat:
    FVF_1L = 1 * 0x12071980
    FVF_2L = 2 * 0x12071980
    FVF_1L_CS = 0x1
    FVF_2L_CS = 0x2
    FVF_3L_CS = 0x3
    FVF_4L_CS = 0x4


FORMAT_VERSION_4 = 4
FORMAT_VERSION_3 = 3
FORMAT_VERSION_2 = 2
SUPPORT_FORMAT_VERSIONS = (FORMAT_VERSION_4, FORMAT_VERSION_3, FORMAT_VERSION_2)

# chunk names
chunks_names_v4 = {
    Chunks_v4.TEXTURE: 'TEXTURE',
    Chunks_v4.VERTICES: 'VERTICES',
    Chunks_v4.INDICES: 'INDICES',
    Chunks_v4.SWIDATA: 'SWIDATA',
    Chunks_v4.VCONTAINER: 'VCONTAINER',
    Chunks_v4.ICONTAINER: 'ICONTAINER',
    Chunks_v4.CHILDREN: 'CHILDREN',
    Chunks_v4.CHILDREN_L: 'CHILDREN_L',
    Chunks_v4.LODDEF2: 'LODDEF2',
    Chunks_v4.TREEDEF2: 'TREEDEF2',
    Chunks_v4.S_BONE_NAMES: 'S_BONE_NAMES',
    Chunks_v4.S_MOTIONS: 'S_MOTIONS',
    Chunks_v4.S_SMPARAMS: 'S_SMPARAMS',
    Chunks_v4.S_IKDATA: 'S_IKDATA',
    Chunks_v4.S_USERDATA: 'S_USERDATA',
    Chunks_v4.S_DESC: 'S_DESC',
    Chunks_v4.S_MOTION_REFS_0: 'S_MOTION_REFS_0',
    Chunks_v4.SWICONTAINER: 'SWICONTAINER',
    Chunks_v4.GCONTAINER: 'GCONTAINER',
    Chunks_v4.FASTPATH: 'FASTPATH'
}
chunks_names_v3 = {
    Chunks_v3.TEXTURE: 'TEXTURE',
    Chunks_v3.TEXTURE_L: 'TEXTURE_L',
    Chunks_v3.CHILD_REFS: 'CHILD_REFS',
    Chunks_v3.BBOX: 'BBOX',
    Chunks_v3.VERTICES: 'VERTICES',
    Chunks_v3.INDICES: 'INDICES',
    Chunks_v3.LODDATA: 'LODDATA',
    Chunks_v3.VCONTAINER: 'VCONTAINER',
    Chunks_v3.BSPHERE: 'BSPHERE',
    Chunks_v3.CHILDREN_L: 'CHILDREN_L',
    Chunks_v3.S_BONE_NAMES: 'S_BONE_NAMES',
    Chunks_v3.S_MOTIONS: 'S_MOTIONS',
    Chunks_v3.DPATCH: 'DPATCH',
    Chunks_v3.LODS: 'LODS',
    Chunks_v3.CHILDREN: 'CHILDREN',
    Chunks_v3.S_SMPARAMS: 'S_SMPARAMS',
    Chunks_v3.ICONTAINER: 'ICONTAINER',
    Chunks_v3.S_SMPARAMS_NEW: 'S_SMPARAMS_NEW',
    Chunks_v3.LODDEF2: 'LODDEF2',
    Chunks_v3.TREEDEF2: 'TREEDEF2',
    Chunks_v3.S_IKDATA_0: 'S_IKDATA_0',
    Chunks_v3.S_USERDATA: 'S_USERDATA',
    Chunks_v3.S_IKDATA: 'S_IKDATA',
    Chunks_v3.S_MOTIONS_NEW: 'S_MOTIONS_NEW',
    Chunks_v3.S_DESC: 'S_DESC',
    Chunks_v3.S_IKDATA_2: 'S_IKDATA_2',
    Chunks_v3.S_MOTION_REFS: 'S_MOTION_REFS'
}
chunks_names_v2 = {
    Chunks_v2.TEXTURE_L: 'TEXTURE_L',
    Chunks_v2.BBOX: 'BBOX',
    Chunks_v2.INDICES: 'INDICES',
    Chunks_v2.VCONTAINER: 'VCONTAINER',
    Chunks_v2.ICONTAINER: 'ICONTAINER',
    Chunks_v2.BSPHERE: 'BSPHERE',
    Chunks_v2.CHILDREN_L: 'CHILDREN_L'
}

# model type names
model_type_names_v4 = {
    ModelType_v4.NORMAL: 'NORMAL',
    ModelType_v4.HIERRARHY: 'HIERRARHY',
    ModelType_v4.PROGRESSIVE: 'PROGRESSIVE',
    ModelType_v4.SKELETON_ANIM: 'SKELETON_ANIM',
    ModelType_v4.SKELETON_GEOMDEF_PM: 'SKELETON_GEOMDEF_PM',
    ModelType_v4.SKELETON_GEOMDEF_ST: 'SKELETON_GEOMDEF_ST',
    ModelType_v4.LOD: 'LOD',
    ModelType_v4.TREE_ST: 'TREE_ST',
    ModelType_v4.PARTICLE_EFFECT: 'PARTICLE_EFFECT',
    ModelType_v4.PARTICLE_GROUP: 'PARTICLE_GROUP',
    ModelType_v4.SKELETON_RIGID: 'SKELETON_RIGID',
    ModelType_v4.TREE_PM: 'TREE_PM',
    ModelType_v4.UNKNOWN_0xC: 'UNKNOWN_0xC'
}
model_type_names_v3 = {
    ModelType_v3.NORMAL: 'NORMAL',
    ModelType_v3.HIERRARHY: 'HIERRARHY',
    ModelType_v3.PROGRESSIVE: 'PROGRESSIVE',
    ModelType_v3.SKELETON_GEOMDEF_PM: 'SKELETON_GEOMDEF_PM',
    ModelType_v3.SKELETON_ANIM: 'SKELETON_ANIM',
    ModelType_v3.DETAIL_PATCH: 'DETAIL_PATCH',
    ModelType_v3.SKELETON_GEOMDEF_ST: 'SKELETON_GEOMDEF_ST',
    ModelType_v3.CACHED: 'CACHED',
    ModelType_v3.PARTICLE: 'PARTICLE',
    ModelType_v3.PROGRESSIVE2: 'PROGRESSIVE2',
    ModelType_v3.LOD: 'LOD',
    ModelType_v3.TREE: 'TREE',
    ModelType_v3.UNUSED_0: 'UNUSED_0',
    ModelType_v3.UNUSED_1: 'UNUSED_1',
    ModelType_v3.SKELETON_RIGID: 'SKELETON_RIGID'
}
model_type_names_v2 = {
    ModelType_v2.NORMAL: 'NORMAL',
    ModelType_v2.HIERRARHY: 'HIERRARHY'
}
