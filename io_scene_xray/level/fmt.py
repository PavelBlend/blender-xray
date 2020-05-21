class Chunks:
    HEADER = 0x1
    SHADERS = 0x2
    VISUALS = 0x3
    PORTALS = 0x4
    LIGHT_DYNAMIC = 0x6
    GLOWS = 0x7
    SECTORS = 0x8
    VB = 0x9
    IB = 0xa
    SWIS = 0xb


class SectorChunks:
    PORTALS = 0x1
    ROOT = 0x2


SECTOR_PORTAL_SIZE = 2
PORTAL_SIZE = 80
PORTAL_VERTEX_COUNT = 6
GLOW_SIZE = 18
LIGHT_DYNAMIC_SIZE = 108

VERSION_14 = 14
VERSION_13 = 13
SUPPORTED_VERSIONS = (VERSION_14, VERSION_13)

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
    12: SAMPLE
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
    SAMPLE: 12    # ???
}

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

# version 13
VERTEX_TYPE_COLOR_13 = [
    (usage_values[POSITION], types_values[FLOAT3]),
    (usage_values[NORMAL], types_values[D3DCOLOR]),
    (usage_values[TANGENT], types_values[D3DCOLOR]),
    (usage_values[BINORMAL], types_values[D3DCOLOR]),
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

UV_COEFFICIENT = 1024
UV_COEFFICIENT_2 = 2048
LIGHT_MAP_UV_COEFFICIENT = 2 ** 15 - 1

# cform
CFORM_VERSION_4 = 4
CFORM_SUPPORT_VERSIONS = (CFORM_VERSION_4, )
