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
    (iface.apply_center, 'Применить Центр'),
    (iface.align_center, 'Выровнять Центр'),

    # material panel
    (iface.surface, 'Поверхность'),
    (iface.surface_presets, 'Предустановки Поверхности'),
    (iface.compile_shader, 'Компилятор'),
    (iface.two_sided, 'Двусторонний'),

    # mesh panel
    (iface.visible, 'Видимый'),
    (iface.locked, 'Заблокированный'),
    (iface.sgmask, 'Маска Групп Сглаживания')

)

translation = {}
default_context = bpy.app.translations.contexts.default
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
