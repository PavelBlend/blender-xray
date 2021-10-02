# blender modules
import bpy

# addon modules
from .. import text


default_context = bpy.app.translations.contexts.default
translations_table = (
    (text.error.mat_no_img, 'материал не имеет изображения'),
    (text.error.mat_many_img, 'материал имеет больше одного изображения'),
    (text.error.mat_many_tex, 'материал имеет больше одной текстуры'),
    (text.error.obj_many_uv, 'объект имеет больше одной UV-карты'),
    (text.error.mat_not_use_nodes, 'материал не использует ноды'),
    (text.error.obj_empty_mat, 'объект использует пустой слот материала'),
    (text.error.obj_no_mat, 'объект не имеет материала'),
    (text.error.img_bad_image_path, 'изображение не находится в папке с текстурами'),
    (text.error.file_another_prog, 'невозможно записать файл. Файл открыт в другой программе'),
    (text.error.anm_no_keys, 'анимация имеет ключи не для всех каналов'),
    (text.error.anm_unsupport_ver, 'файл имеет неподдерживаемую версию формата')
)
translation = {}
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
