# blender modules
import bpy

# addon modules
from .. import text


default_context = bpy.app.translations.contexts.default
translations_table = (
    (text.error.obj, 'объект'),
    (text.error.me, 'меш'),
    (text.error.mat, 'материал'),
    (text.error.img, 'изображение'),
    (text.error.no_img, 'не имеет изображения'),
    (text.error.many_img, 'имеет больше одного изображения'),
    (text.error.many_tex, 'имеет больше одной текстуры'),
    (text.error.obj_many_uv, 'имеет больше одной UV-карты'),
    (text.error.not_use_nodes, 'не использует ноды'),
    (text.error.empty_mat, 'имеет пустой слот материала'),
    (text.error.no_mat, 'не имеет материала'),
    (text.error.bad_image_path, 'не находится в папке с текстурами'),
    (text.error.another_prog, 'Невозможно записать файл: {}. Файл открыт в другой программе.'),
)
translation = {}
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
