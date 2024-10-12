# blender modules
import bpy

# addon modules
from .. import iface


translations_table = (

    # action panel
    (iface.fps, 'Частота Кадров'),
    (iface.speed, 'Скорость'),
    (iface.accrue, 'Нарастание'),
    (iface.falloff, 'Спад'),
    (iface.type_fx, 'Тип FX'),
    (iface.start_bone, 'Начальная Кость'),
    (iface.power, 'Сила'),
    (iface.bone_part, 'Часть Костей'),
    (iface.stop, 'Стоп'),
    (iface.no_mix, 'Не Смешивать'),
    (iface.sync, 'синхронизировать'),
    (iface.foot_steps, 'Шаги Ног'),
    (iface.move_xform, 'Переместить XForm'),
    (iface.idle, 'Анимация Простоя'),
    (iface.weapon_bone, 'Кость Оружия'),
    (iface.settings, 'Настройки'),
    (iface.bake, 'Запекание'),
    (iface.use_custom_thresh, 'Использовать Настраеваемые Пороги'),
    (iface.loc_thresh, 'Порог Позиции'),
    (iface.rot_thresh, 'Порог Вращения'),
    (iface.export_skl, 'Экспорт .skl'),
    (iface.on, 'Вкл.'),

    # armature panel
    (iface.display_bone_shapes, 'Отображать Формы Костей'),
    (iface.display_bone_mass_centers, 'Отображать Центры Масс Костей'),
    (iface.crosshair_size, 'Размер Перекрестия'),
    (iface.display_bone_limits, 'Отображать Лимиты Костей'),
    (iface.gizmo_radius, 'Радиус Гизмо'),
    (iface.limit_x, 'Ограничение по X'),
    (iface.limit_y, 'Ограничение по Y'),
    (iface.limit_z, 'Ограничение по Z'),
    (iface.use_limits, 'Использовать Лимиты'),

    # bone panel
    (iface.exportable, 'Экспортируемая Кость'),
    (iface.material, 'Материал'),
    (iface.length, 'Длина'),
    (iface.shape_type, 'Тип Формы'),
    (iface.shape_id, 'ID Формы'),
    (iface.no_pickable, 'Не Отрываемый'),
    (iface.no_physics, 'Без Физики'),
    (iface.remove_after_break, 'Удалить После Разрушения'),
    (iface.no_fog_collider, 'Нет Коллизии Тумана'),
    (iface.joint_type, 'Тип Сустава'),
    (iface.friction, 'Трение'),
    (iface.spring, 'Упругость'),
    (iface.damping, 'Затухание'),
    (iface.steer, 'Рулить'),
    (iface.steer_roll, 'Рулить-X / Вращение-Z'),
    (iface.rotate_z, 'Вращение по Z'),
    (iface.slide_z, 'Скольжение по Z'),
    (iface.joint_id, 'ID Сустава'),
    (iface.breakable, 'Разрушаемый'),
    (iface.force, 'Сила'),
    (iface.torque, 'Вращающий Момент'),
    (iface.edit_center, 'Редиктировать Центр'),
    (iface.edit_shape, 'Редиктировать Форму'),
    (iface.rigid, 'Неподвижный'),
    (iface.joint, 'Сустав'),
    (iface.wheel, 'Колесо'),
    (iface.slider, 'Скольжение'),
    (iface.custom, 'Настраиваемый'),

    # edit helper panel
    (iface.cancel, 'Отмена'),
    (iface.apply_shape, 'Применить Форму'),
    (iface.fit_shape, 'Вписать Форму'),
    (iface.aabb, 'Выровненные по Осям Габариты'),
    (iface.obb, 'Ориентированные Габариты'),
    (iface.apply_center, 'Применить Центр'),
    (iface.align_center, 'Выровнять Центр'),

    # material panel
    (iface.surface, 'Поверхность'),
    (iface.surface_presets, 'Предустановки Поверхности'),
    (iface.compile_shader, 'Компилятор'),
    (iface.two_sided, 'Двусторонний'),
    (iface.level_visual, 'Визуальный Объект Уровня'),
    (iface.texture_uv, 'UV Текстуры'),
    (iface.lmap_uv, 'UV Карты Освещения'),
    (iface.lmap_1, 'Карта Освещения 1'),
    (iface.lmap_2, 'Карта Освещения 2'),
    (iface.light, 'Источники Света'),
    (iface.sun, 'Свет Солнца'),
    (iface.hemi, 'Полусферическое Освещение'),
    (iface.level_cform, 'Коллизия Уровня'),
    (iface.supp_shadows, 'Подавить Тени'),
    (iface.supp_wallmarks, 'Подавить Следы на Стенах'),

    # mesh panel
    (iface.visible, 'Видимый'),
    (iface.locked, 'Заблокированный'),
    (iface.sgmask, 'Маска Групп Сглаживания'),

    # object panel
    (iface.obj_type, 'Тип'),
    (iface.hq_export, 'Высококачественный Экспорт'),
    (iface.lod_ref, 'LOD Ссылка'),
    (iface.exp_path, 'Путь Экспорта'),
    (iface.user_data, 'Пользовательские Данные'),
    (iface.motions, 'Анимации'),
    (iface.play_active_motion, 'Проиграть Активную Анимацию'),
    (iface.custom_names, 'Настраиваемые Имена'),
    (iface.show, 'Отображать'),
    (iface.dep_obj, 'Зависимость'),
    (iface.motion_refs, 'Ссылки на Анимации'),
    (iface.load_motion_ref, 'Загрузить Активную Ссылку на Анимацию'),
    (iface.fmt, 'Формат'),
    (iface.revision, 'Редакция'),
    (iface.owner_name, 'Имя Автора'),
    (iface.created_time, 'Время Создания'),
    (iface.moder_name, 'Имя Модифицирующего'),
    (iface.mod_time, 'Время Модифицирования'),
    (iface.time_fmt, 'Формат Времени'),
    (iface.time_fmt_1, 'Год.Месяц.День Часы:Минуты'),
    (iface.time_fmt_2, 'Год.Месяц.День'),

    # dm panel
    (iface.dm_props, 'Detail Model Параметры'),
    (iface.dm_no_waving, 'Без Волнения'),
    (iface.dm_min_scale, 'Мин. Масштаб'),
    (iface.dm_max_scale, 'Макс. Масштаб'),
    (iface.dm_index, 'Индекс'),

    # details panel
    (iface.details_props, 'Details Параметры'),
    (iface.details_meshes, 'Объект Мешей'),
    (iface.details_slots_base, 'Объект Низа Слотов'),
    (iface.details_slots_top, 'Объект Верха Слотов'),
    (iface.details_light_coefs, 'Коэффициенты Освещения'),
    (iface.details_fmt_cop, 'Билды 1569-ЗП'),
    (iface.details_fmt_1096, 'Билды 1096-1558'),
    (iface.details_meshes_indices, 'Индексы Мешей'),
    (iface.details_mesh, 'Меш'),
    (iface.details_pack, 'Упаковать Details Изображения')

)

translation = {}
default_context = bpy.app.translations.contexts.default
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
