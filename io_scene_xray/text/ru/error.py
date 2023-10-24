# blender modules
import bpy

# addon modules
from .. import error


translations_table = (
    # general
    (error.error_title, 'Ошибка'),
    (error.no_sel_files, 'Нет выделенных файлов!'),
    (error.fatal_import_error, 'Ошибка импорта. Файл не импортирован'),
    (error.mat_no_img, 'Материал не имеет изображения'),
    (error.mat_many_img, 'Материал имеет больше одного изображения'),
    (error.mat_many_tex, 'Материал имеет больше одной текстуры'),
    (error.no_uv, 'Меш-объект не имеет UV-карты'),
    (error.mat_not_use_nodes, 'Материал не использует ноды'),
    (error.obj_empty_mat, 'Объект использует пустой слот материала'),
    (error.no_tex, 'Материал не имеет текстуры'),
    (error.obj_no_mat, 'Объект не имеет материала'),
    (error.many_mat, 'Меш-объект имеет более одного материала'),
    (error.file_another_prog, 'Невозможно записать файл. Файл открыт в другой программе'),
    (error.no_active_obj, 'Нет активного объекта!'),
    (error.no_selected_obj, 'Нет выделенных объектов!'),
    (error.no_blend_obj, 'Текущий blend-файл не имеет объектов'),
    (error.is_not_arm, 'Активный объект не является арматурой!'),
    (error.file_not_found, 'Файл не найден'),
    (error.file_folder_not_found, 'Файл или папка не найден(а)'),
    (error.ltx_invalid_syntax, 'Ошибка синтаксиса ltx файла'),
    (error.has_no_main_chunk, 'Файл не имеет основного блока данных'),
    (error.arm_non_uniform_scale, 'Объект имеет неравномерный масштаб'),
    (error.not_pose_mode, 'Pose mode не активирован!'),
    (error.no_active_bone, 'Нет активной кости!'),

    # anm export
    (error.anm_no_keys, 'Анимация имеет ключи не для всех каналов'),

    # anm import
    (error.anm_unsupport_ver, 'Файл имеет неподдерживаемую версию формата'),

    # details convert
    (error.details_light_1569, 'Объект имеет некорректный формат освещения: "Builds 1096-1558". Должен быть "Builds 1569-CoP"'),
    (error.details_light_1096, 'Объект имеет некорректный формат освещения: "Builds 1569-CoP". Должен быть "Builds 1096-1558"'),
    (error.details_slots_size, 'Размер объекта "Slots Base" не равен размеру "Slots Top"'),
    (error.details_poly_count, 'Объект слотов имеет некооректное количество полигонов'),
    (error.details_img_size, 'Изображение имеет некорректный размер'),

    # details import
    (error.details_bad_header, 'Некорректный DETAILS файл. Размер HEADER блока не равен 24'),
    (error.details_unsupport_ver, 'Неподдерживаемая версия DETAILS формата'),
    (error.details_no_header, 'Некорректный DETAILS файл. Не найден HEADER блок'),
    (error.details_no_meshes, 'Некорректный DETAILS файл. Не найден MESHES блок'),
    (error.details_no_slots, 'Некорректный DETAILS файл. Не найден SLOTS блок'),

    # details utility
    (error.details_has_no_img, 'Level details объект не имеет свойство-изображение'),
    (error.details_has_no_obj, 'Level details объект не имеет свойство-объект'),
    (error.details_cannot_find_img, 'Не найдено изображение'),
    (error.details_cannot_find_obj, 'Не найден объект'),
    (error.details_wrong_type, 'Объект имеет неправильный тип'),

    # details write
    (error.details_file_duplicates, 'Найдены дубликаты путей'),
    (error.details_no_children, 'Объект details-мешей не имеет потомков'),
    (error.details_many_children, 'Объект details-мешей имеет слишком много потомков'),
    (error.details_not_mesh, 'Потомок объекта details-мешей не является мешем'),
    (error.details_bad_detail_index, 'Объект имеет некорректный параметр "Detail Index"'),
    (error.details_no_model_index, 'Не найден detail-меш для индекса'),
    (error.details_duplicate_model, 'Найдены повторяющиеся индексы detail-мешей'),

    # dm create
    (error.dm_bad_indices, 'Меш имеет некорректное количество индексов треугольников'),

    # dm export
    (error.dm_many_verts, 'Меш-объект имеет слишком много вершин'),

    # dm validate
    (error.dm_tex_type, 'Текстура имеет некорректный тип'),

    # level cform import
    (error.cform_unsupport_ver, 'Неподдерживаемая версия level cform формата'),

    # level export
    (error.level_no_lmap, 'Не найдено изображение для карты освещения'),
    (error.level_has_children, 'Объекты Normal/Progressive не должны иметь потомков'),
    (error.level_lmap_no_dds, 'Некорректный формат карты освещения (должен быть *.dds)'),
    (error.level_sector_has_no_cform, 'Сектор не имеет cform-объекта'),
    (error.level_no_lights, 'Level-объект не имеет light-объектов'),
    (error.level_no_sectors, 'Level-объект не имеет sector-объектов'),

    # level export visual
    (error.level_visual_is_not_mesh, 'Visual-объект не является мешем'),
    (error.level_visual_no_faces, 'Visual меш-объект не имеет полигонов'),
    (error.level_visual_no_mat, 'Visual-объект не имеет материала'),
    (error.level_visual_empty_mat, 'Visual-объект имеет пустой слот материала'),
    (error.level_visual_many_mats, 'Visual-объект имеет больше одного материала'),
    (error.level_visual_no_uv, 'Visual-объект не имеет UV-карты'),
    (error.level_visual_no_hemi, 'Visual-объект не имеет hemi слоя'),
    (error.level_visual_no_light, 'Visual-объект не имеет light слоя'),
    (error.level_light_not_spec, 'У материала не указан параметр "Light"'),

    # level export glow
    (error.level_no_glow, 'Level-объект не имеет glow-объектов'),
    (error.level_bad_glow_type, 'Glow-объект не является мешем'),
    (error.level_bad_glow, 'Glow меш-объект не имеет полигонов'),
    (error.level_no_mat_glow, 'Glow-объект не имеет материала'),
    (error.level_glow_empty_mat, 'Glow-объект имеет пустой слот материала'),
    (error.level_glow_many_mats, 'Glow-объект имеет больше одного материала'),
    (error.level_bad_glow_radius, 'Glow объект имеет близкий к нулю радиус'),

    # level export portal
    (error.level_portal_is_no_mesh, 'Объект портала не является мешем'),
    (error.level_portal_no_vert, 'Меш-объект портала не имеет вершин'),
    (error.level_portal_bad, 'Меш-объект портала имеет меньше 3 вершин'),
    (error.level_portal_many_verts, 'Меш-объект портала должен иметь не более 6 вершин'),
    (error.level_portal_no_faces, 'Меш-объект портала не имеет полигонов'),
    (error.level_portal_many_faces, 'Меш-объект портала должен иметь не более 1 полигона'),
    (error.level_portal_no_front, 'Не указан объект "Sector Front" у портала'),
    (error.level_portal_no_back, 'Не указан объект "Sector Back" у портала'),

    # level cform export
    (error.level_bad_cform_type, 'Cform-объект не является мешем'),
    (error.level_cform_no_geom, 'Cform-объект не имеет полигонов'),
    (error.level_cform_no_mats, 'Cform-объект не имеет материалов'),
    (error.level_cform_empty_mat_slot, 'Cform-объект имеет пустой слот материала'),

    # level import
    (error.level_unsupport_ver, 'Неподдерживаемая версия game level формата'),

    # object export main
    (error.object_nonexp_group_verts, 'Меш-объект имеет вершины, которые не привязаны к экспортируемым костям'),
    (error.object_ungroupped_verts, 'Меш-объект имеет вершины, которые не имеют групп вершин'),
    (error.object_duplicate_bones, 'Объект имеет дубликаты костей'),
    (error.object_many_arms, 'Root-объект имеет более одной арматуры'),
    (error.object_no_meshes, 'Root-объект не имеет мешей'),
    (error.object_skel_many_meshes, 'Скелетный объект имеет больше одного меша'),
    (error.object_bad_boneparts, 'Не все кости привязаны к bone parts'),
    (error.object_many_parents, 'Объект-арматура имеет больше одной главной кости'),
    (error.object_no_roots, 'Не найдены root-объекты.'),
    (error.object_many_roots, 'Найдено слишком много root-объектов, но ни один не выбран.'),

    # object import bone
    (error.object_unsupport_bone_ver, 'Неподдерживаемая версия формата костей'),

    # object import main
    (error.object_unsupport_format_ver, 'Неподдерживаемая версия OBJECT формата'),

    # object import mesh
    (error.object_unsupport_mesh_ver, 'Неподдерживаемая версия меш-формата'),
    (error.object_bad_vmap, 'Неподдерживаемый тип карты вершин'),
    (error.object_many_duplicated_faces, 'Слишком много дублирующихся полигонов'),

    # ogf import
    (error.ogf_bad_ver, 'Неподдерживаемая версия OGF формата'),
    (error.ogf_bad_vertex_fmt, 'Неподдерживаемая версия формата OGF-вершин'),
    (error.ogf_bad_model_type, 'Неподдерживаемый тип OGF модели'),

    # ogf export
    (error.ogf_has_no_arm, 'Скелетный меш-объект не имеет арматуры'),

    # omf export
    (error.omf_empty, 'Используйте другой режим экспорта. Этот OMF файл пустой'),
    (error.omf_no_anims, 'OMF файл не имеет блок анимаций'),
    (error.omf_no_params, 'OMF файл не имеет блок параметров'),
    (error.omf_bone_no_group, 'Не все кости арматуры имеют группу костей (bone part)'),
    (error.omf_nothing_exp, 'Ничего не экспортируется!'),

    # omf import
    (error.omf_no_bone, 'Арматура не имеет всех костей, которые есть в OMF файле'),
    (error.omf_nothing, 'Ничего не импортировано. Измените настройки импорта'),
    (error.omf_nothing_imp, 'Ничего не импортируется!'),

    # omf merge
    (error.few_files, 'Необходимо выделить больше одного файла!'),
    (error.omf_merge_parts_count, 'Файл имеет разное количество boneparts'),

    # scene import
    (error.scene_incorrect_file, 'Недопустимый *.level файл'),
    (error.scene_err_info, 'Для получения подробной информации перейдите по этой ссылке:'),
    (error.scene_bad_file, 'Недопустимый scene selection файл. Не найден "scene version" блок'),
    (error.scene_obj_tool_ver, 'Неподдерживаемая версия "object tools"'),
    (error.scene_obj_count, 'Недопустимый scene selection файл. Не найден "scene objects count" блок'),
    (error.scene_scn_objs, 'Недопустимый scene selection файл. Не найден "scene objects" блок'),
    (error.scene_objs, 'Недопустимый scene selection файл. Не найден "objects" блок'),
    (error.scene_no_ver, 'Недопустимый scene selection файл. Не найден "version" блок'),
    (error.scene_ver_size, 'Недопустимый scene selection файл. Размер "version" блока не равен 4'),
    (error.scene_ver, 'Неподдерживаемая версия формата'),
    (error.scene_obj_ver, 'Неподдерживаемая версия формата объектов сцены'),

    # part import
    (error.part_no_objs, 'Файл не имеет объектов!'),

    # motion
    (error.motion_shape, 'Неподдерживаемая форма ключевого кадра'),
    (error.motion_ver, 'Неподдерживаемая версия анимации')
)

translation = {}
default_context = bpy.app.translations.contexts.default
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
