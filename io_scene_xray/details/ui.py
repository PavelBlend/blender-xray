import bpy

from .. import ui
from . import operators


def draw_function(self, context):

    box = self.layout.box()

    if context.active_object.type == 'MESH':

        model = context.object.xray.detail.model

        box.label('Detail Model Properties:')

        box.prop(model, 'no_waving', text='No Waving', toggle=True)
        box.prop(model, 'min_scale', text='Min Scale')
        box.prop(model, 'max_scale', text='Max Scale')
        box.prop(model, 'index', text='Detail Index')
        box.prop(model, 'color', text='')

    elif context.active_object.type == 'EMPTY':

        slots = context.object.xray.detail.slots

        box.label('Level Details Properties:')

        box.prop_search(
            slots,
            'meshes_object',
            bpy.data,
            'objects',
            text='Meshes Object'
            )

        box.prop_search(
            slots,
            'slots_base_object',
            bpy.data,
            'objects',
            text='Slots Base Object'
            )

        box.prop_search(
            slots,
            'slots_top_object',
            bpy.data,
            'objects',
            text='Slots Top Object'
            )

        _, box_ = ui.collapsible.draw(
            box, 'object:lighting', 'Lighting Coefficients'
            )

        if box_:

            ligthing = slots.ligthing
            box_.label('Format:')
            row = box_.row()
            row.prop(ligthing, 'format', expand=True, text='Format')

            box_.prop_search(
                ligthing,
                'lights_image',
                bpy.data,
                'images',
                text='Lights'
                )

            if ligthing.format == 'builds_1569-cop':

                box_.prop_search(
                    ligthing,
                    'hemi_image',
                    bpy.data,
                    'images',
                    text='Hemi'
                    )

                box_.prop_search(
                    ligthing,
                    'shadows_image',
                    bpy.data,
                    'images',
                    text='Shadows'
                    )

        _, box_ = ui.collapsible.draw(
            box, 'object:slots', 'Slots Meshes Indices'
            )

        if box_:
            for i in range(4):
                box_.prop_search(
                    slots.meshes,
                    'mesh_{}'.format(i),
                    bpy.data,
                    'images',
                    text='Mesh {}'.format(i)
                    )

        box.operator(operators.PackDetailsImages.bl_idname)
