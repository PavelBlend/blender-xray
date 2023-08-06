# blender modules
import bpy

# addon modules
from .. import warn


mat_many_tex = 'Материал имеет больше одной текстуры'

translations_table = (
    # general
    (warn.info_title, 'Информация'),
    (warn.ready, 'Готово!'),
    (warn.imported, 'Импортировано'),
    (warn.сhanged, 'Изменено'),
    (warn.full_log, 'Полный лог хранится в окне Text Editor в текстовом файле'),
    (warn.tex_not_found, 'Файл текстуры не найден'),
    (warn.tex_folder_not_spec, 'Папка с текстурами не указана в настройках аддона'),
    (warn.objs_folder_not_spec, 'Папка с объектами не указана в настройках аддона'),
    (warn.meshes_folder_not_spec, 'Папка с мешами не указана в настройках аддона'),
    (warn.env_tex, 'Материал имеет некорректный тип ноды изображения (Environment Texture)'),
    (warn.no_bone_parent, 'Не найдена родительская кость'),
    (warn.invalid_image_path, 'Изображение имеет некорректный путь'),
    (warn.no_file, 'Файл не выделен'),
    (warn.img_bad_image_path, 'Изображение не находится в папке с текстурами'),
    (warn.use_shader_tex, mat_many_tex + '. Экспортирована текстура шейдера'),
    (warn.use_active_tex, mat_many_tex + '. Экспортирована активная текстура'),
    (warn.use_selected_tex, mat_many_tex + '. Экспортирована выделенная текстура'),
    (warn.name_has_dot, 'Имя файла имеет больше одной точки. Файл был переименован'),
    (warn.obj_many_uv, 'Объект имеет больше одной UV-карты. Экспортирована активная UV-карта'),
    (warn.keymap_assign_more_one, 'Больше одного оператора назначено на'),

    # updates
    (warn.new_update_available, 'Доступно новое обновление аддона blender-xray'),
    (warn.has_no_update, 'Нет нового обновления аддона blender-xray'),

    # anm export
    (warn.anm_rot_mode, 'Объект имеет режим вращения отличающийся от YXZ. Анимация была запечена'),

    # anm import
    (warn.anm_conv_linear, 'Анимационные ключи были сконвертированы в LINEAR'),
    (warn.anm_unsupport_shape, 'Найдены ключи с неподдерживаемой интерполяцией и были заменены на поддерживаемую'),

    # bones import
    (warn.bones_not_have_boneparts, 'BONES файл не имеет bone parts'),
    (warn.bones_missing_bone, 'Bone partition содержит отсутствующую кость'),
    (warn.bones_has_no_bone, 'Объект-арматура не имеет кости'),

    # details read
    (warn.details_coord_base, 'Details-слот имеет некорректную координату основания'),
    (warn.details_coord_top, 'Details-слот имеет некорректную координату высоты'),

    # err import
    (warn.err_no_faces, 'Файл не содержит неправильных треугольников (invalid faces)'),

    # object export bone
    (warn.object_bone_uppercase, 'Имя кости было сохранено без символов верхнего регистра'),
    (warn.object_bone_plugin_ver, 'Кость отредактирована другой версией этого аддона'),

    # object export main
    (warn.object_merged, 'Скелетные меш-объекты были сохранены как один меш'),
    (warn.object_no_action, 'Не найдена анимация'),
    (warn.object_legacy_motionrefs, 'Пропущены устаревшие motion references данные'),
    (warn.object_set_dynamic, 'Скелетный объект имеет неправильный тип. Тип объекта записан как Dynamic'),
    (warn.object_arm_mod_disabled, 'Модификатор armature отключён в 3D viewport'),
    (warn.obj_used_arm, 'Не указан объект в модификаторе "Armature". Был использован объект из иерархии'),

    # object export mesh
    (warn.object_sg_smooth, 'Несовместимость Maya-сглаживания: сглаженные смежные рёбра имеют различные группы сглаживания'),
    (warn.object_sg_sharp, 'Несовместимость Maya-сглаживания: не сглаженные смежные рёбра имеют одинаковую группу сглаживания'),
    (warn.object_skip_geom, 'Пропущена геометрия из групп вершин'),
    (warn.object_missing_group, 'Вершины имеют отсутствующие группы'),

    # object import bone
    (warn.object_bone_renamed, 'Группа вершин кости: была переименована'),
    (warn.object_bone_already_renamed, 'Группа вершин кости: уже переименована'),
    (warn.object_bad_bone_name, 'Ещё не поддерживается. Имя кости не равно def2 кости'),

    # object import main
    (warn.object_bad_userdata, 'Некорректные пользовательские данные (userdata)'),

    # object import mesh
    (warn.object_uv_renamed, 'Текстурная карта вершин была переименована'),
    (warn.object_zero_weight, 'Карта веса вершин имеет значения близкие к нулю'),
    (warn.object_invalid_face, 'Найдены неправильные треугольники (invalid faces)'),
    (warn.object_already_mat, 'Полигону уже был назначен материал'),
    (warn.object_already_used_mat, 'Полигону уже был назначен материал'),
    (warn.object_duplicate_faces, 'Найдены дубликаты полигонов'),
    (warn.object_try_use_option, 'Попробуйте включить параметр импорта'),
    (warn.object_vert_group_created, 'Создана группа вершин'),

    # ogf import
    (warn.ogf_bad_shape, 'Неподдерживаемый тип формы кости, используется тип Custom'),
    (warn.ogf_bad_joint, 'Неподдерживаемый тип сустава кости, используется тип Custom'),
    (warn.ogf_bad_description, 'Описание прочитано с ошибками'),

    # omf import
    (warn.omf_exp_no_act, 'Не найден action объекта'),

    # omf merge
    (warn.omf_merge_part_names, 'Имена bonepart не идентичны'),
    (warn.omf_merge_part_bone_names, 'Имена костей bonepart не идентичны'),
    (warn.omf_merge_motion_duplicate, 'Анимация не сохранена, так как анимация с таким именем уже существует'),

    # scene import
    (warn.scene_no_file, 'Не найден файл'),

    # motion
    (warn.motion_non_zero_flags, 'Кость имеет флаги, отличные от нуля'),
    (warn.motion_behaviors, 'Кость имеет различные типы экстраполяций для начала и конца анимационной кривой'),
    (warn.motion_no_bone, 'Не найдена кость'),
    (warn.motion_bone_replaced, 'Ссылка на кость была изменена'),
    (warn.motion_rotation_mode, 'Кость имеет режим вращения отличающийся от ZXY'),
    (warn.motion_to_stepped, 'Формы анимационных ключей были сконвертированы в STEPPED'),
    (warn.motion_markers, 'Маркеры пока не поддерживаются'),

    # envelope
    (warn.envelope_behaviors_replaced, 'Анимационные кривые имеют различные типы экстраполяций для начала и конца, один будет заменён другим'),
    (warn.envelope_bad_behavior, 'Тип экстраполяции анимационнной кривой не поддерживается и будет заменён'),
    (warn.envelope_extrapolation, 'Тип экстраполяции анимационнной кривой не поддерживается и будет заменён'),
    (warn.envelope_shapes, 'Неподдерживаемые формы анимационных ключей были заменены на поддерживаемые'),

    # skls browser
    (warn.browser_load, 'Загрузка анимаций из .skls файла: "{}"'),
    (warn.browser_done, 'Готово: {} анимаций'),
    (warn.browser_import, 'Импортировано анимаций'),

    # rig operators
    (warn.remove_rig_warn, 'Будут удалены все констрейнты костей и кости, у которых выключен параметр "Exportable". Продолжить?'),

    # verify
    (warn.incorrect_uv_objs_count, 'Выделено объектов с некорректной uv-картой'),
    (warn.invalid_face_objs_count, 'Выделено объектов с invalid face'),

    # others operators
    (warn.added_motions, 'Добавлено анимаций'),
)

translation = {}
default_context = bpy.app.translations.contexts.default
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
