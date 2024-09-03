# addon modules
from .. import text
from .. import log


@log.with_context('armature')
def check_bone_names(armature_object):

    # collect bone names
    bone_names = {}
    for bpy_bone in armature_object.data.bones:
        name = bpy_bone.name
        name_lower = name.lower()
        bone_names.setdefault(name_lower, []).append(name)

    # search bone duplicates
    bone_duplicates = []
    for bones in bone_names.values():
        if len(bones) > 1:
            bones.sort()
            bone_duplicates.append(bones)
    bone_duplicates.sort()

    # report error
    if bone_duplicates:
        log.update(object=armature_object.name)
        raise log.AppError(
            text.error.object_duplicate_bones,
            log.props(
                count=str(sum(map(len, bone_duplicates))),
                bones=bone_duplicates
            )
        )
