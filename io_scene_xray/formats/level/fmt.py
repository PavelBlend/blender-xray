# header chunk id
HEADER = 0x1


class Chunks13:
    SHADERS = 0x2
    VISUALS = 0x3
    PORTALS = 0x4
    LIGHT_DYNAMIC = 0x6
    GLOWS = 0x7
    SECTORS = 0x8
    VB = 0x9
    IB = 0xa
    SWIS = 0xb


class Chunks12:
    SHADERS = 0x2
    VISUALS = 0x3
    PORTALS = 0x4
    LIGHT_DYNAMIC = 0x6
    GLOWS = 0x7
    SECTORS = 0x8
    IB = 0x9
    VB = 0xa
    SWIS = 0xb


class Chunks10:
    SHADERS = 0x2
    VISUALS = 0x3
    PORTALS = 0x4
    LIGHT_DYNAMIC = 0x6
    GLOWS = 0x7
    SECTORS = 0x8
    IB = 0x9
    VB = 0xa


class Chunks9:
    SHADERS = 0x2
    VISUALS = 0x3
    VB_OLD = 0x4
    CFORM = 0x5
    PORTALS = 0x6
    SHADER_CONSTANT = 0x7
    LIGHT_DYNAMIC = 0x8
    GLOWS = 0x9
    SECTORS = 0xa
    IB = 0xb
    VB = 0xc


class Chunks8:
    SHADERS = 0x2
    VISUALS = 0x3
    VB = 0x4
    CFORM = 0x5
    PORTALS = 0x6
    LIGHT_DYNAMIC = 0x7
    GLOWS = 0x9
    SECTORS = 0xa


class Chunks5:
    TEXTURES = 0x2
    SHADERS = 0x3
    VISUALS = 0x4
    VB = 0x5
    CFORM = 0x6
    PORTALS = 0x7
    LIGHT_DYNAMIC = 0x8
    LIGHT_KEY_FRAMES = 0x9
    GLOWS = 0xa
    SECTORS = 0xb


class Chunks4:
    TEXTURES = 0x2
    SHADERS = 0x3
    VISUALS = 0x4
    VB = 0x5
    CFORM = 0x6
    PORTALS = 0x7
    LIGHT_DYNAMIC = 0x8
    LIGHT_KEY_FRAMES = 0x9
    GLOWS = 0xa
    SECTORS = 0xb


class SectorChunks:
    PORTALS = 0x1
    ROOT = 0x2


INDEX_SIZE = 2
PORTAL_SIZE = 80
PORTAL_VERTEX_COUNT = 6
GLOW_SIZE_V12 = 18
GLOW_SIZE_V5 = 24

# light constants
LIGHT_DYNAMIC_SIZE_V9 = 108
LIGHT_DYNAMIC_SIZE_V8 = 176
LIGHT_DYNAMIC_SIZE_V5 = 124
LIGHT_V8_NAME_LEN = 64

# light controllers
CONTROLLER_STATIC = 2
CONTROLLER_SUN = 1
CONTROLLER_HEMI = 0

# d3d light types
D3D_LIGHT_POINT = 1
D3D_LIGHT_SPOT = 2
D3D_LIGHT_DIRECTIONAL = 3
D3D_LIGHT_FORCE_DWORD = 0x7fffffff

# light version 8 flags
FLAG_AFFECT_STATIC = 1
FLAG_AFFECT_DYNAMIC = 1 << 1
FLAG_PROCEDURAL = 1 << 2

VERSION_14 = 14
VERSION_13 = 13
VERSION_12 = 12
VERSION_11 = 11
VERSION_10 = 10
VERSION_9 = 9
VERSION_8 = 8
VERSION_5 = 5
VERSION_4 = 4

SUPPORTED_VERSIONS = (
    VERSION_14,
    VERSION_13,
    VERSION_12,
    VERSION_11,
    VERSION_10,
    VERSION_9,
    VERSION_8,
    VERSION_5,
    VERSION_4
)

# vertex buffer type names
FLOAT2 = 'FLOAT2'
FLOAT3 = 'FLOAT3'
FLOAT4 = 'FLOAT4'
D3DCOLOR = 'D3DCOLOR'
SHORT2 = 'SHORT2'
SHORT4 = 'SHORT4'
UNUSED = 'UNUSED'

# vertex buffer method names
DEFAULT = 'DEFAULT'
PARTIALU = 'PARTIALU'
PARTIALV = 'PARTIALV'
CROSSUV = 'CROSSUV'
UV = 'UV'

# vertex buffer usage names
POSITION = 'POSITION'
BLENDWEIGHT = 'BLENDWEIGHT'
BLENDINDICES = 'BLENDINDICES'
NORMAL = 'NORMAL'
PSIZE = 'PSIZE'
TEXCOORD = 'TEXCOORD'
TANGENT = 'TANGENT'
BINORMAL = 'BINORMAL'
TESSFACTOR = 'TESSFACTOR'
POSITIONT = 'POSITIONT'
COLOR = 'COLOR'
FOG = 'FOG'
DEPTH = 'DEPTH'
SAMPLE = 'SAMPLE'

types = {
    1: FLOAT2,
    2: FLOAT3,
    3: FLOAT4,
    4: D3DCOLOR,
    6: SHORT2,
    7: SHORT4,
    17: UNUSED
}

types_struct = {
    1: '2f',    # FLOAT2
    2: '3f',    # FLOAT3
    3: '4f',    # FLOAT4
    4: '4B',    # D3DCOLOR
    6: '2h',    # SHORT2
    7: '2h2H'    # SHORT4
}

types_values = {
    FLOAT2: 1,
    FLOAT3: 2,
    FLOAT4: 3,
    D3DCOLOR: 4,
    SHORT2: 6,
    SHORT4: 7,
    UNUSED: 17
}

methods = {
    0: DEFAULT,
    1: PARTIALU,
    2: PARTIALV,
    3: CROSSUV,
    4: UV
}

usage = {
    0: POSITION,
    1: BLENDWEIGHT,
    2: BLENDINDICES,
    3: NORMAL,
    4: PSIZE,
    5: TEXCOORD,
    6: TANGENT,
    7: BINORMAL,
    8: TESSFACTOR,
    9: POSITIONT,
    10: COLOR,
    11: FOG,
    12: DEPTH,
    13: SAMPLE
}

usage_values = {
    POSITION: 0,
    BLENDWEIGHT: 1,
    BLENDINDICES: 2,
    NORMAL: 3,
    PSIZE: 4,
    TEXCOORD: 5,
    TANGENT: 6,
    BINORMAL: 7,
    TESSFACTOR: 8,
    POSITIONT: 9,
    COLOR: 10,
    FOG: 11,
    DEPTH: 12,
    SAMPLE: 13    # ???
}

UV_COEFFICIENT = 1024
UV_COEFFICIENT_2 = 2048
LIGHT_MAP_UV_COEFFICIENT = 2 ** 15 - 1

# cform
CFORM_VERSION_4 = 4
CFORM_VERSION_3 = 3
CFORM_VERSION_2 = 2
CFORM_SUPPORT_VERSIONS = (CFORM_VERSION_4, CFORM_VERSION_3, CFORM_VERSION_2)

# vertex types
VERTEX_TYPE_TREE = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[TANGENT], types_values[D3DCOLOR]),
    (usage_values[BINORMAL], types_values[D3DCOLOR]),
    (usage_values[TEXCOORD], types_values[SHORT4])
]

# version 14
VERTEX_TYPE_BRUSH_14 = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[TANGENT], types_values[D3DCOLOR]),
    (usage_values[BINORMAL], types_values[D3DCOLOR]),
    (usage_values[TEXCOORD], types_values[SHORT2]),
    (usage_values[TEXCOORD], types_values[SHORT2])
]

# version 13
VERTEX_TYPE_BRUSH_13 = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[TANGENT], types_values[D3DCOLOR]),
    (usage_values[BINORMAL], types_values[D3DCOLOR]),
    (usage_values[TEXCOORD], types_values[FLOAT2]),
    (usage_values[TEXCOORD], types_values[SHORT2])
]
# version 12
VERTEX_TYPE_BRUSH_12 = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[TEXCOORD], types_values[FLOAT2]),
    (usage_values[TEXCOORD], types_values[SHORT2])
]

# version 13
VERTEX_TYPE_COLOR_13 = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[TANGENT], types_values[D3DCOLOR]),
    (usage_values[BINORMAL], types_values[D3DCOLOR]),
    (usage_values[COLOR], types_values[D3DCOLOR]),
    (usage_values[TEXCOORD], types_values[FLOAT2])
]
# version 12
VERTEX_TYPE_COLOR_12 = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[COLOR], types_values[D3DCOLOR]),
    (usage_values[TEXCOORD], types_values[FLOAT2])
]

# version 14
VERTEX_TYPE_COLOR_14 = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[TANGENT], types_values[D3DCOLOR]),
    (usage_values[BINORMAL], types_values[D3DCOLOR]),
    (usage_values[COLOR], types_values[D3DCOLOR]),
    (usage_values[TEXCOORD], types_values[SHORT2])
]
# version 14
VERTEX_TYPE_FASTPATH = [
    (usage_values[POSITION], types_values[FLOAT3]),
]

# directx 3d 7 vertex formats
class D3D7FVF:
    POSITION_MASK = 0x00e
    XYZ = 0x002    # x, y, z

    NORMAL = 0x010    # not used
    DIFFUSE = 0x040    # quantized normal
    SPECULAR = 0x080    # not used
    NC_MASK = 0x0f0    # not used

    TEX1 = 0x100    # base texture
    TEX2 = 0x200    # base texture + light map
    TEXCOUNT_MASK = 0xf00
    TEXCOUNT_SHIFT = 8


# directx 3d 9 vertex formats
class D3D9FVF:
    XYZ = 0x002    # x, y, z
    NORMAL = 0x010
    TEXCOUNT_SHIFT = 8


# ogf vertex format without skeleton (normal or progressive)
FVF_OGF = D3D9FVF.XYZ | D3D9FVF.NORMAL | (1 << D3D9FVF.TEXCOUNT_SHIFT)
