# blender modules
import bpy

# addon modules
from .. import warn


mat_many_tex = 'материал имеет больше одной текстуры'

translations_table = (
    # general
    (warn.info_title, 'информация'),
    (warn.ready, 'Готово!'),
    (warn.imported, 'Импортировано'),
    (warn.сhanged, 'Изменено'),
    (warn.full_log, 'Полный лог хранится в окне Text Editor в текстовом файле'),
    (warn.tex_not_found, 'файл текстуры не найден'),
    (warn.tex_folder_not_spec, 'Папка с текстурами не указана в настройках аддона'),
    (warn.objs_folder_not_spec, 'Папка с объектами не указана в настройках аддона'),
    (warn.meshes_folder_not_spec, 'Папка с мешами не указана в настройках аддона'),
    (warn.env_tex, 'материал имеет некорректный тип ноды изображения (Environment Texture)'),
    (warn.no_bone_parent, 'не найдена родительская кость'),
    (warn.invalid_image_path, 'изображение имеет некорректный путь'),
    (warn.no_file, 'файл не выделен'),
    (warn.img_bad_image_path, 'изображение не находится в папке с текстурами'),
    (warn.use_shader_tex, mat_many_tex + '. Экспортирована текстура шейдера'),
    (warn.use_active_tex, mat_many_tex + '. Экспортирована активная текстура'),
    (warn.use_selected_tex, mat_many_tex + '. Экспортирована выделенная текстура'),
    # updates
    (warn.new_update_available, 'доступно новое обновление аддона blender-xray'),
    (warn.has_no_update, 'нет нового обновления аддона blender-xray'),
    # anm export
    (warn.anm_rot_mode, 'объект имеет режим вращения отличающийся от YXZ. Анимация была запечена'),
    # anm import
    (warn.anm_conv_linear, 'анимационные ключи были сконвертированы в LINEAR'),
    (warn.anm_unsupport_shape, 'найдены ключи с неподдерживаемой интерполяцией и были заменены на поддерживаемую'),
    # bones import
    (warn.bones_not_have_boneparts, 'bones файл не имеет bone parts'),
    (warn.bones_missing_bone, 'bone partition содержит отсутствующую кость'),
    (warn.bones_has_no_bone, 'объект-арматура не имеет кости'),
    # details read
    (warn.details_coord_base, 'details-слот имеет некорректную координату основания'),
    (warn.details_coord_top, 'details-слот имеет некорректную координату высоты'),
    # err import
    (warn.err_no_faces, 'файл не содержит неправильных треугольников (invalid faces)'),
    # object export bone
    (warn.object_bone_uppercase, 'имя кости было сохранено без символов верхнего регистра'),
    (warn.object_bone_plugin_ver, 'кость отредактирована другой версией этого аддона'),
    # object export main
    (warn.object_merged, 'скелетные меш-объекты были сохранены как один меш'),
    (warn.object_no_action, 'не найдена анимация'),
    (warn.object_legacy_motionrefs, 'пропущены устаревшие motion references данные'),
    (warn.object_set_dynamic, 'скелетный объект имеет неправильный тип. Тип объекта записан как Dynamic'),
    (warn.object_arm_mod_disabled, 'модификатор armature отключён в 3D viewport'),
    # object export mesh
    (warn.object_sg_smooth, 'Несовместимость Maya-сглаживания: сглаженные смежные рёбра имеют различные группы сглаживания'),
    (warn.object_sg_sharp, 'Несовместимость Maya-сглаживания: не сглаженные смежные рёбра имеют одинаковую группу сглаживания'),
    (warn.object_skip_geom, 'пропущена геометрия из групп вершин'),
    (warn.object_missing_group, 'вершины имеют отсутствующие группы'),
    # object import bone
    (warn.object_bone_renamed, 'группа вершин кости: была переименована'),
    (warn.object_bone_already_renamed, 'группа вершин кости: уже переименована'),
    (warn.object_bad_bone_name, 'ещё не поддерживается. Имя кости не равно def2 кости'),
    # object import main
    (warn.object_bad_userdata, 'некорректные пользовательские данные (userdata)'),
    # object import mesh
    (warn.object_uv_renamed, 'текстурная карта вершин была переименована'),
    (warn.object_zero_weight, 'карта веса вершин имеет значения близкие к нулю'),
    (warn.object_invalid_face, 'найдены неправильные треугольники (invalid faces)'),
    (warn.object_already_mat, 'полигону уже был назначен материал'),
    (warn.object_already_used_mat, 'полигону уже был назначен материал'),
    (warn.object_duplicate_faces, 'найдены дубликаты полигонов'),
    (warn.object_try_use_option, 'Попробуйте включить параметр импорта'),
    (warn.object_vert_group_created, 'Создана группа вершин'),
    # ogf import
    (warn.ogf_bad_shape, 'неподдерживаемый тип формы кости, используется тип по-умолчанию'),
    (warn.ogf_bad_joint, 'неподдерживаемый тип сустава кости, используется тип по-умолчанию'),
    # scene import
    (warn.scene_no_file, 'не найден файл'),
    # motion
    (warn.motion_non_zero_flags, 'кость имеет флаги, отличные от нуля'),
    (warn.motion_behaviors, 'кость имеет различные типы экстраполяций для начала и конца анимационной кривой'),
    (warn.motion_no_bone, 'не найдена кость'),
    (warn.motion_bone_replaced, 'ссылка на кость была изменена'),
    (warn.motion_rotation_mode, 'кость имеет режим вращения отличающийся от ZXY'),
    (warn.motion_to_stepped, 'формы анимационных ключей были сконвертированы в STEPPED'),
    (warn.motion_markers, 'маркеры пока не поддерживаются'),
    # envelope
    (warn.envelope_behaviors_replaced, 'анимационные кривые имеют различные типы экстраполяций для начала и конца, один будет заменён другим'),
    (warn.envelope_bad_behavior, 'тип экстраполяции анимационнной кривой не поддерживается и будет заменён'),
    (warn.envelope_extrapolation, 'тип экстраполяции анимационнной кривой не поддерживается и будет заменён'),
    (warn.envelope_shapes, 'неподдерживаемые формы анимационных ключей были заменены на поддерживаемые'),
    # skls browser
    (warn.browser_load, 'Загрузка анимаций из .skls файла: "{}"'),
    (warn.browser_done, 'Готово: {} анимаций'),
    (warn.browser_import, 'Импортировано анимаций'),
    # verify uv
    (warn.incorrect_uv_objs_count, 'выделено объектов с некорректной uv-картой'),
    # others operators
    (warn.added_motions, 'Добавлено анимаций'),
)

translation = {}
default_context = bpy.app.translations.contexts.default
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
