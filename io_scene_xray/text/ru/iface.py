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

    # armature panel
    (iface.display_bone_shapes, 'Отображать Формы Костей'),
    (iface.display_bone_mass_centers, 'Отображать Центры Масс Костей'),
    (iface.crosshair_size, 'Размер Перекрестия'),
    (iface.display_bone_limits, 'Отображать Лимиты Костей'),
    (iface.gizmo_radius, 'Радиус Гизмо'),
    (iface.limit_x, 'Ограничение по X'),
    (iface.limit_y, 'Ограничение по Y'),
    (iface.limit_z, 'Ограничение по Z'),
    (iface.use_limits, 'Использовать Лимиты')

)

translation = {}
default_context = bpy.app.translations.contexts.default
for eng, rus in translations_table:
    translation[(default_context, eng)] = rus
