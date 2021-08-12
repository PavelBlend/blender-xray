# plugin modules
from . import details
from . import dm
from . import err
from . import scene
from . import obj
from . import anm
from . import skl
from . import bones
from . import ogf
from . import level
from . import omf


modules = (
    details.ops,
    obj.imp.ops,
    obj.exp.ops,
    anm.ops,
    dm.ops,
    bones.ops,
    ogf.ops,
    skl.ops,
    omf.ops,
    scene.ops,
    level.ops,
    err.ops
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
