# blender modules
import bpy

# addon modules
from .. import error


translations_table = (
    # general
    (error.error_title, 'ошибка'),
    (error.mat_no_img, 'материал не имеет изображения'),
    (error.mat_many_img, 'материал имеет больше одного изображения'),
    (error.mat_many_tex, 'материал имеет больше одной текстуры'),
    (error.obj_many_uv, 'объект имеет больше одной UV-карты'),
    (error.no_uv, 'меш-объект не имеет UV-карту'),
    (error.mat_not_use_nodes, 'материал не использует ноды'),
    (error.obj_empty_mat, 'объект использует пустой слот материала'),
    (error.no_tex, 'материал не имеет текстуры'),
    (error.obj_no_mat, 'объект не имеет материала'),
    (error.many_mat, 'меш-объект имеет более одного материала'),
    (error.file_another_prog, 'невозможно записать файл. Файл открыт в другой программе'),
    (error.no_active_obj, 'нет активного объекта'),
    (error.no_selected_obj, 'нет выделенных объектов'),
    (error.no_blend_obj, 'текущий blend-файл не имеет объектов'),
    (error.is_not_arm, 'активный объект не является арматурой'),
    (error.file_not_found, 'файл не найден'),
    (error.file_folder_not_found, 'файл или папка не найден(а)'),
    (error.ltx_invalid_syntax, 'ошибка синтаксиса ltx файла'),
    # anm export
    (error.anm_no_keys, 'анимация имеет ключи не для всех каналов'),
    # anm import
    (error.anm_unsupport_ver, 'файл имеет неподдерживаемую версию формата'),
    (error.anm_has_no_chunk, 'файл не имеет основного блока данных'),
    # details convert
    (error.details_light_1569, 'объект имеет некорректный формат освещения: "Builds 1096-1558". Должен быть "Builds 1569-CoP"'),
    (error.details_light_1096, 'объект имеет некорректный формат освещения: "Builds 1569-CoP". Должен быть "Builds 1096-1558"'),
    (error.details_slots_size, 'размер объекта "Slots Base" не равен размеру "Slots Top"'),
    (error.details_poly_count, 'объект слотов имеет некооректное количество полигонов'),
    (error.details_img_size, 'изображение имеет некорректный размер'),
    # details import
    (error.details_bad_header, 'некорректный details файл. Размер HEADER блока не равен 24'),
    (error.details_unsupport_ver, 'неподдерживаемая версия details формата'),
    (error.details_no_header, 'некорректный details файл. Не найден HEADER блок'),
    (error.details_no_meshes, 'некорректный details файл. Не найден MESHES блок'),
    (error.details_no_slots, 'некорректный details файл. Не найден SLOTS блок'),
    # details utility
    (error.details_has_no_img, 'level details объект не имеет свойство-изображение'),
    (error.details_has_no_obj, 'level details объект не имеет свойство-объект'),
    (error.details_cannot_find_img, 'не найдено изображение'),
    (error.details_cannot_find_obj, 'не найден объект'),
    (error.details_wrong_type, 'объект имеет неправильный тип'),
    # details write
    (error.details_no_children, 'объект details-мешей не имеет потомков'),
    (error.details_many_children, 'объект details-мешей имеет слишком много потомков'),
    (error.details_not_mesh, 'потомок объекта details-мешей не является мешем'),
    (error.details_bad_detail_index, 'объект имеет некорректный параметр "Detail Index"'),
    (error.details_no_model_index, 'не найден detail-меш для индекса'),
    (error.details_duplicate_model, 'найдены повторяющиеся индексы detail-мешей'),
    # dm create
    (error.dm_bad_indices, 'меш имеет некорректное количество индексов треугольников'),
    # dm export
    (error.dm_many_verts, 'меш-объект имеет слишком много вершин'),
    # dm validate
    (error.dm_many_uv, 'меш-объект имеет более одной UV-карты'),
    (error.dm_tex_type, 'текстура имеет некорректный тип'),
    # level cform import
    (error.cform_unsupport_ver, 'неподдерживаемая версия level cform формата'),
    # level export
    (error.level_no_lmap, 'не найдено изображение для карты освещения'),
    (error.level_has_children, 'Normal/Progressive объекты не должны иметь потомков'),
    (error.level_bad_portal, 'меш-объект портала имеет меньше 3 вершин'),
    (error.level_bad_glow, 'glow меш-объект не имеет полигонов'),
    (error.level_bad_glow_radius, 'glow объект имеет близкий к нулю радиус'),
    (error.level_lmap_no_dds, 'некорректный формат карты освещения (должен быть *.dds)'),
    # level cform export
    (error.level_bad_cform_type, 'cform-объект не является мешем'),
    (error.level_cform_no_geom, 'cform-объект не имеет полигонов'),
    # level import
    (error.level_unsupport_ver, 'неподдерживаемая версия game level формата'),
    # object export main
    (error.object_ungroupped_verts, 'меш-объект имеет вершины, которые не привязаны к экспортируемым костям'),
    (error.object_duplicate_bones, 'объект имеет дубликаты костей'),
    (error.object_many_arms, 'root-объект имеет более одной арматуры'),
    (error.object_no_meshes, 'root-объект не имеет мешей'),
    (error.object_skel_many_meshes, 'скелетный объект имеет больше одного меша'),
    (error.object_bad_boneparts, 'не все кости привязаны к bone parts'),
    (error.object_many_parents, 'объект-арматура имеет больше одной главной кости'),
    (error.object_bad_scale, 'объект-арматура имеет некорректный масштаб'),
    # object export mesh
    (error.object_no_uv, 'меш-объект не имеет UV-карты'),
    # object import bone
    (error.object_unsupport_bone_ver, 'неподдерживаемая версия формата костей'),
    # object import main
    (error.object_unsupport_format_ver, 'неподдерживаемая версия object формата'),
    (error.object_main_chunk, 'файл не имеет основного блока данных'),
    # object import mesh
    (error.object_unsupport_mesh_ver, 'неподдерживаемая версия меш-формата'),
    (error.object_bad_vmap, 'неподдерживаемый тип карты вершин'),
    (error.object_many_duplicated_faces, 'слишком много дублирующихся полигонов'),
    # ogf import
    (error.ogf_bad_ver, 'неподдерживаемая версия ogf формата'),
    (error.ogf_bad_vertex_fmt, 'неподдерживаемая версия формата ogf-вершин'),
    (error.ogf_bad_color_mode, 'неизвестный режим цвета ogf'),
    (error.ogf_bad_model_type, 'неподдерживаемый тип ogf модели'),
    # ogf export
    (error.ogf_has_no_arm, 'скелетный меш-объект не имеет арматуры'),
    # omf export
    (error.omf_empty, 'используйте другой режим экспорта. Этот omf файл пустой'),
    (error.omf_no_anims, 'omf файл не имеет блок анимаций'),
    (error.omf_no_params, 'omf файл не имеет блок параметров'),
    (error.omf_bone_no_group, 'не все кости арматуры имеют группу костей (bone part)'),
    # omf import
    (error.omf_no_bone, 'арматура не имеет всех костей, которые есть в omf файле'),
    (error.omf_nothing, 'ничего не импортировано. Измените настройки импорта'),
    # scene import
    (error.scene_bad_file, 'недопустимый scene selection файл. Не найден "scene version" блок'),
    (error.scene_obj_tool_ver, 'неподдерживаемая версия "object tools"'),
    (error.scene_obj_count, 'недопустимый scene selection файл. Не найден "scene objects count" блок'),
    (error.scene_scn_objs, 'недопустимый scene selection файл. Не найден "scene objects" блок'),
    (error.scene_objs, 'недопустимый scene selection файл. Не найден "objects" блок'),
    (error.scene_no_ver, 'недопустимый scene selection файл. Не найден "version" блок'),
    (error.scene_ver_size, 'недопустимый scene selection файл. Размер "version" блока не равен 4'),
    (error.scene_ver, 'неподдерживаемая версия формата'),
    # motion
    (error.motion_shape, 'неподдерживаемая форма ключевого кадра'),
    (error.motion_ver, 'неподдерживаемая версия анимации')
)

translation = {}
default_context = bpy.app.translations.contexts.default
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
