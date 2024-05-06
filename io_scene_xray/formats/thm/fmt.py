class ThmChunks:
    VERSION = 0x0810
    DATA = 0x0811
    TYPE = 0x0813


class ThmTextureChunks:
    TEXTURE_PARAM = 0x0812
    TEXTURE_TYPE = 0x0814
    DETAIL_EXT = 0x0815
    MATERIAL = 0x0816
    BUMP = 0x0817
    EXT_NORMALMAP = 0x0818
    FADE_DELAY = 0x0819


class ThmType:
    OBJECT = 0
    TEXTURE = 1
    SOUND = 2
    GROUP = 3


class ThmVersion:
    OBJECT = 18
    TEXTURE = 18
    SOUND = 20
    GROUP =  1
