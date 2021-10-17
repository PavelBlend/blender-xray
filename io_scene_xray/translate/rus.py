# blender modules
import bpy

# addon modules
from .. import text


default_context = bpy.app.translations.contexts.default
translations_table = (
    # errors

    # general
    (text.error.mat_no_img, 'материал не имеет изображения'),
    (text.error.mat_many_img, 'материал имеет больше одного изображения'),
    (text.error.mat_many_tex, 'материал имеет больше одной текстуры'),
    (text.error.obj_many_uv, 'объект имеет больше одной UV-карты'),
    (text.error.mat_not_use_nodes, 'материал не использует ноды'),
    (text.error.obj_empty_mat, 'объект использует пустой слот материала'),
    (text.error.obj_no_mat, 'объект не имеет материала'),
    (text.error.img_bad_image_path, 'изображение не находится в папке с текстурами'),
    (text.error.file_another_prog, 'невозможно записать файл. Файл открыт в другой программе'),
    (text.error.no_active_obj, 'нет активного объекта'),
    (text.error.is_not_arm, 'активный объект не является арматурой'),
    # anm export
    (text.error.anm_no_keys, 'анимация имеет ключи не для всех каналов'),
    # anm import
    (text.error.anm_unsupport_ver, 'файл имеет неподдерживаемую версию формата'),
    # details convert
    (text.error.details_light_1569, 'объект имеет некорректный формат освещения: "Builds 1096-1558". Должен быть "Builds 1569-CoP"'),
    (text.error.details_light_1096, 'объект имеет некорректный формат освещения: "Builds 1569-CoP". Должен быть "Builds 1096-1558"'),
    (text.error.details_slots_size, 'размер объекта "Slots Base" не равен размеру "Slots Top"'),
    (text.error.details_poly_count, 'объект слотов имеет некооректное количество полигонов'),
    (text.error.details_img_size, 'изображение имеет некорректный размер'),
    # details import
    (text.error.details_bad_header, 'некорректный details файл. Размер HEADER блока не равен 24'),
    (text.error.details_unsupport_ver, 'неподдерживаемая версия details формата'),
    (text.error.details_no_header, 'некорректный details файл. Не найден HEADER блок'),
    (text.error.details_no_meshes, 'некорректный details файл. Не найден MESHES блок'),
    (text.error.details_no_slots, 'некорректный details файл. Не найден SLOTS блок'),
    # details utility
    (text.error.details_has_no_img, 'level details объект не имеет свойство-изображение'),
    (text.error.details_has_no_obj, 'level details объект не имеет свойство-объект'),
    (text.error.details_cannot_find_img, 'не найдено изображение'),
    (text.error.details_cannot_find_obj, 'не найден объект'),
    (text.error.details_wrong_type, 'объект имеет неправильный тип'),
    # details write
    (text.error.details_no_children, 'объект details-мешей не имеет потомков'),
    (text.error.details_many_children, 'объект details-мешей имеет слишком много потомков'),
    (text.error.details_not_mesh, 'потомок объекта details-мешей не является мешем'),
    (text.error.details_bad_detail_index, 'объект имеет некорректный параметр "Detail Index"'),
    (text.error.details_no_model_index, 'не найден detail-меш для индекса'),
    (text.error.details_duplicate_model, 'найдены повторяющиеся индексы detail-мешей'),
    # dm create
    (text.error.dm_bad_indices, 'меш имеет некорректное количество индексов треугольников'),
    # dm export
    (text.error.dm_many_verts, 'меш-объект имеет слишком много вершин'),
    # dm validate
    (text.error.dm_no_uv, 'меш-объект не имеет UV-карту'),
    (text.error.dm_many_uv, 'меш-объект имеет более одной UV-карты'),
    (text.error.dm_many_mat, 'меш-объект имеет более одного материала'),
    (text.error.dm_no_tex, 'материал не имеет текстуры'),
    (text.error.dm_tex_type, 'текстура имеет некорректный тип'),
    # level cform import
    (text.error.cform_unsupport_ver, 'неподдерживаемая версия level cform формата'),
    # level export
    (text.error.level_no_lmap, 'не найдено изображение для карты освещения'),
    (text.error.level_has_children, 'Normal/Progressive объекты не должны иметь потомков'),
    # level import
    (text.error.level_unsupport_ver, 'неподдерживаемая версия game level формата'),
    # object export main
    (text.error.object_ungroupped_verts, 'меш-объект имеет вершины, которые не привязаны к экспортируемым костям'),
    (text.error.object_duplicate_bones, 'объект имеет дубликаты костей'),
    (text.error.object_many_arms, 'root-объект имеет более одной арматуры'),
    (text.error.object_no_meshes, 'root-объект не имеет мешей'),
    (text.error.object_skel_many_meshes, 'скелетный объект имеет больше одного меша'),
    (text.error.object_bad_boneparts, 'не все кости привязаны к bone parts'),
    (text.error.object_many_parents, 'объект-арматура имеет больше одной главной кости'),
    (text.error.object_bad_scale, 'объект-арматура имеет некорректный масштаб'),
    # object export mesh
    (text.error.object_no_uv, 'меш-объект не имеет UV-карты'),
    # object import bone
    (text.error.object_unsupport_bone_ver, 'неподдерживаемая версия формата костей'),
    # object import main
    (text.error.object_unsupport_format_ver, 'неподдерживаемая версия object формата'),
    (text.error.object_main_chunk, 'файл не имеет основного блока данных'),
    # object import mesh
    (text.error.object_unsupport_mesh_ver, 'неподдерживаемая версия меш-формата'),
    (text.error.object_bad_vmap, 'неподдерживаемый тип карты вершин'),
    (text.error.object_many_duplicated_faces, 'слишком много дублирующихся полигонов'),
    # ogf export
    (text.error.ogf_no_bone, 'кость не найдена в арматуре'),
    # ogf import
    (text.error.ogf_bad_ver, 'неподдерживаемая версия ogf формата'),
    (text.error.ogf_bad_vertex_fmt, 'неподдерживаемая версия формата ogf-вершин'),
    (text.error.ogf_bad_color_mode, 'неизвестный режим цвета ogf'),
    (text.error.ogf_bad_model_type, 'неподдерживаемый тип ogf модели'),
    # omf export
    (text.error.omf_empty, 'используйте другой режим экспорта. Этот omf файл пустой'),
    (text.error.omf_no_anims, 'omf файл не имеет блок анимаций'),
    (text.error.omf_no_params, 'omf файл не имеет блок параметров'),
    (text.error.omf_bone_no_group, 'не все кости арматуры имеют группу костей'),
    # omf import
    (text.error.omf_no_bone, 'арматура не имеет всех костей, которые есть в omf файле'),
    (text.error.omf_nothing, 'ничего не импортировано. Измените настройки импорта'),
    # scene import
    (text.error.scene_bad_file, 'недопустимый scene selection файл. Не найден "scene version" блок'),
    (text.error.scene_obj_tool_ver, 'неподдерживаемая версия "object tools"'),
    (text.error.scene_obj_count, 'недопустимый scene selection файл. Не найден "scene objects count" блок'),
    (text.error.scene_scn_objs, 'недопустимый scene selection файл. Не найден "scene objects" блок'),
    (text.error.scene_objs, 'недопустимый scene selection файл. Не найден "objects" блок'),
    (text.error.scene_no_ver, 'недопустимый scene selection файл. Не найден "version" блок'),
    (text.error.scene_ver_size, 'недопустимый scene selection файл. Размер "version" блока не равен 4'),
    (text.error.scene_ver, 'неподдерживаемая версия формата'),
    # motion
    (text.error.motion_shape, 'неподдерживаемая форма ключевого кадра'),
    (text.error.motion_ver, 'неподдерживаемая версия анимации'),
)
translation = {}
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
