# chunks

class ToolsChunks:
    GUID = 0x7000
    DATA = 0x8000


class SceneChunks:
    LEVEL_TAG = 0x7777


class CustomObjectsChunks:
    VERSION = 1
    OBJECT_COUNT = 2
    OBJECTS = 3
    FLAGS = 4


class CustomObjectChunks:
    CLASS = 0x7703
    BODY = 0x7777


class ObjectChunks:
    PARAMS = 0xf900
    LOCK = 0xf902
    TRANSFORM = 0xf903
    GROUP = 0xf904
    MOTION = 0xf905
    FLAGS = 0xf906
    NAME = 0xf907
    MOTION_PARAM = 0xf908


class SceneObjectChunks:
    VERSION = 0x0900
    REFERENCE = 0x0902
    PLACEMENT = 0x0904
    FLAGS = 0x0905


class ObjectToolsChunks:
    VERSION = 0x1001
    APPEND_RANDOM = 0x1002
    FLAGS = 0x1003


# flags
class AppendRandomFlags:
    UpdateProps = 1<<27
    ScaleProportional = 1<<28
    AppendRandom = 1<<29
    RandomScale = 1<<30
    RandomRotation = 1<<31


class CustomObjectFlags:
    SELECTED = 1<<0
    VISIBLE = 1<<1
    LOCKED = 1<<2
    MOTION = 1<<3
    AUTO_KEY = 1<<30
    CAMERA_VIEW = 1<<31


# classes
class ClassID:
    OBJECT = 2


# versions
OBJECT_TOOLS_VERSION = 0
SCENE_OBJECT_VERSION = 17
