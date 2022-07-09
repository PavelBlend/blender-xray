# blender modules
import bpy

# addon modules
from .. import text


mat_many_tex = 'материал имеет больше одной текстуры'
default_context = bpy.app.translations.contexts.default
translations_table = (
    # errors

    # general
    (text.error.mat_no_img, 'материал не имеет изображения'),
    (text.error.mat_many_img, 'материал имеет больше одного изображения'),
    (text.error.mat_many_tex, 'материал имеет больше одной текстуры'),
    (text.error.obj_many_uv, 'объект имеет больше одной UV-карты'),
    (text.error.no_uv, 'меш-объект не имеет UV-карту'),
    (text.error.mat_not_use_nodes, 'материал не использует ноды'),
    (text.error.obj_empty_mat, 'объект использует пустой слот материала'),
    (text.error.no_tex, 'материал не имеет текстуры'),
    (text.error.obj_no_mat, 'объект не имеет материала'),
    (text.error.many_mat, 'меш-объект имеет более одного материала'),
    (text.error.file_another_prog, 'невозможно записать файл. Файл открыт в другой программе'),
    (text.error.no_active_obj, 'нет активного объекта'),
    (text.error.is_not_arm, 'активный объект не является арматурой'),
    (text.error.file_not_found, 'файл не найден'),
    # anm export
    (text.error.anm_no_keys, 'анимация имеет ключи не для всех каналов'),
    # anm import
    (text.error.anm_unsupport_ver, 'файл имеет неподдерживаемую версию формата'),
    (text.error.anm_has_no_chunk, 'файл не имеет основного блока данных'),
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
    (text.error.dm_many_uv, 'меш-объект имеет более одной UV-карты'),
    (text.error.dm_tex_type, 'текстура имеет некорректный тип'),
    # level cform import
    (text.error.cform_unsupport_ver, 'неподдерживаемая версия level cform формата'),
    # level export
    (text.error.level_no_lmap, 'не найдено изображение для карты освещения'),
    (text.error.level_has_children, 'Normal/Progressive объекты не должны иметь потомков'),
    (text.error.level_bad_portal, 'меш-объект портала имеет меньше 3 вершин'),
    (text.error.level_bad_glow, 'glow меш-объект не имеет полигонов'),
    (text.error.level_bad_glow_radius, 'glow объект имеет близкий к нулю радиус'),
    (text.error.level_lmap_no_dds, 'некорректный формат карты освещения (должен быть *.dds)'),
    # level cform export
    (text.error.level_bad_glow_radius, 'glow объект имеет близкий к нулю радиус'),
    # level import
    (text.error.level_unsupport_ver, 'неподдерживаемая версия game level формата'),
    (text.error.level_bad_cform_type, 'cform-объект не является мешем'),
    (text.error.level_cform_no_geom, 'cform-объект не имеет полигонов'),
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
    # ogf import
    (text.error.ogf_bad_ver, 'неподдерживаемая версия ogf формата'),
    (text.error.ogf_bad_vertex_fmt, 'неподдерживаемая версия формата ogf-вершин'),
    (text.error.ogf_bad_color_mode, 'неизвестный режим цвета ogf'),
    (text.error.ogf_bad_model_type, 'неподдерживаемый тип ogf модели'),
    # ogf export
    (text.error.ogf_has_no_arm, 'скелетный меш-объект не имеет арматуры'),
    # omf export
    (text.error.omf_empty, 'используйте другой режим экспорта. Этот omf файл пустой'),
    (text.error.omf_no_anims, 'omf файл не имеет блок анимаций'),
    (text.error.omf_no_params, 'omf файл не имеет блок параметров'),
    (text.error.omf_bone_no_group, 'не все кости арматуры имеют группу костей (bone part)'),
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

    # warrnings

    # general
    (text.warn.full_log, 'Полный лог хранится в текстовом файле "{0}" (в окне Text Editor)'),
    (text.warn.tex_not_found, 'файл текстуры не найден'),
    (text.warn.env_tex, 'материал имеет некорректный тип ноды изображения (Environment Texture)'),
    (text.warn.no_bone_parent, 'не найдена родительская кость'),
    (text.warn.invalid_image_path, 'изображение имеет некорректный путь'),
    (text.warn.no_file, 'файл не выделен'),
    (text.warn.img_bad_image_path, 'изображение не находится в папке с текстурами'),
    (text.warn.use_shader_tex, mat_many_tex + '. Экспортирована текстура шейдера'),
    (text.warn.use_active_tex, mat_many_tex + '. Экспортирована активная текстура'),
    (text.warn.use_selected_tex, mat_many_tex + '. Экспортирована выделенная текстура'),
    # anm export
    (text.warn.anm_rot_mode, 'объект имеет режим вращения отличающийся от YXZ. Анимация была запечена'),
    # anm import
    (text.warn.anm_conv_linear, 'анимационные ключи были сконвертированы в LINEAR'),
    (text.warn.anm_unsupport_shape, 'найдены ключи с неподдерживаемой интерполяцией и были заменены на поддерживаемую'),
    # bones import
    (text.warn.bones_not_have_boneparts, 'bones файл не имеет bone parts'),
    (text.warn.bones_missing_bone, 'bone partition содержит отсутствующую кость'),
    (text.warn.bones_has_no_bone, 'объект-арматура не имеет кости'),
    # details read
    (text.warn.details_coord_base, 'details-слот имеет некорректную координату основания'),
    (text.warn.details_coord_top, 'details-слот имеет некорректную координату высоты'),
    # err import
    (text.warn.err_no_faces, 'файл не содержит неправильных треугольников (invalid faces)'),
    # object export bone
    (text.warn.object_bone_uppercase, 'имя кости было сохранено без символов верхнего регистра'),
    (text.warn.object_bone_plugin_ver, 'кость отредактирована другой версией этого аддона'),
    # object export main
    (text.warn.object_merged, 'скелетные меш-объекты были сохранены как один меш'),
    (text.warn.object_no_action, 'не найдена анимация'),
    (text.warn.object_legacy_motionrefs, 'пропущены устаревшие motion references данные'),
    (text.warn.object_set_dynamic, 'скелетный объект имеет неправильный тип. Тип объекта записан как Dynamic'),
    (text.warn.object_arm_mod_disabled, 'модификатор armature отключён в 3D viewport'),
    # object export mesh
    (text.warn.object_sg_smooth, 'Несовместимость Maya-сглаживания: сглаженные смежные рёбра имеют различные группы сглаживания'),
    (text.warn.object_sg_sharp, 'Несовместимость Maya-сглаживания: не сглаженные смежные рёбра имеют одинаковую группу сглаживания'),
    (text.warn.object_skip_geom, 'пропущена геометрия из групп вершин'),
    (text.warn.object_missing_group, 'вершины имеют отсутствующие группы'),
    # object import bone
    (text.warn.object_bone_renamed, 'группа вершин кости: была переименована'),
    (text.warn.object_bone_already_renamed, 'группа вершин кости: уже переименована'),
    (text.warn.object_unsupport_prop, 'неподдерживаемое значение свойства, используется значение по-умолчанию'),
    (text.warn.object_bad_bone_name, 'ещё не поддерживается. Имя кости не равно def2 кости'),
    # object import main
    (text.warn.object_bad_userdata, 'некорректные пользовательские данные (userdata)'),
    # object import mesh
    (text.warn.object_uv_renamed, 'текстурная карта вершин была переименована'),
    (text.warn.object_zero_weight, 'карта веса вершин имеет значения близкие к нулю'),
    (text.warn.object_invalid_face, 'найдены неправильные треугольники (invalid faces)'),
    (text.warn.object_already_mat, 'полигону уже был назначен материал'),
    (text.warn.object_already_used_mat, 'полигону уже был назначен материал'),
    (text.warn.object_duplicate_faces, 'найдены дубликаты полигонов, создана группа вершин'),
    (text.warn.object_try_use_option, ' (попробуйте включить "{}" параметр импорта)'),
    # ogf import
    (text.warn.ogf_bad_shape, 'неподдерживаемый тип формы кости'),
    (text.warn.ogf_bad_joint, 'неподдерживаемый тип сустава кости'),
    # scene import
    (text.warn.scene_no_file, 'не найден файл'),
    # motion
    (text.warn.motion_non_zero_flags, 'кость имеет флаги, отличные от нуля'),
    (text.warn.motion_behaviors, 'кость имеет различные типы экстраполяций для начала и конца анимационной кривой'),
    (text.warn.motion_no_bone, 'не найдена кость'),
    (text.warn.motion_bone_replaced, 'ссылка на кость была изменена'),
    (text.warn.motion_rotation_mode, 'кость имеет режим вращения отличающийся от ZXY'),
    (text.warn.motion_to_stepped, 'формы анимационных ключей были сконвертированы в STEPPED'),
    (text.warn.motion_markers, 'маркеры пока не поддерживаются'),
    # envelope
    (text.warn.envelope_behaviors_replaced, 'анимационные кривые имеют различные типы экстраполяций для начала и конца, один будет заменён другим'),
    (text.warn.envelope_bad_behavior, 'тип экстраполяции анимационнной кривой не поддерживается и будет заменён'),
    (text.warn.envelope_extrapolation, 'тип экстраполяции анимационнной кривой не поддерживается и будет заменён'),
    (text.warn.envelope_shapes, 'неподдерживаемые формы анимационных ключей были заменены на поддерживаемые'),
    # skls browser
    (text.warn.browser_load, 'Загрузка анимаций из .skls файла: "{}"'),
    (text.warn.browser_done, 'Готово: {} анимаций')
)
translation = {}
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
