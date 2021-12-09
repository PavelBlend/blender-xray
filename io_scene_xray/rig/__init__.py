# addon modules
from . import connect_bones
from . import create_ik


modules = (
    connect_bones,
    create_ik
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
