
import bpy

from ..utils import is_helper_object
from ..ui.collapsible import draw
from .operators import PackDetailsImages


class XRayDetailsPanel(bpy.types.Panel):
    bl_context = 'object'
    bl_label = 'XRay - details'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type in {'MESH', 'EMPTY'}
            and not is_helper_object(context.active_object)
        )

    def draw(self, context):

        layout = self.layout

        if context.active_object.type == 'MESH':

            model = context.object.xray.detail.model

            layout.label('Detail Model Properties:')

            layout.prop(model, 'no_waving', text='No Waving', toggle=True)
            layout.prop(model, 'min_scale', text='Min Scale')
            layout.prop(model, 'max_scale', text='Max Scale')
            layout.prop(model, 'index', text='Detail Index')
            layout.prop(model, 'color', text='')

        elif context.active_object.type == 'EMPTY':

            slots = context.object.xray.detail.slots

            layout.label('Level Details Properties:')

            layout.prop_search(
                slots,
                'meshes_object',
                bpy.data,
                'objects',
                text='Meshes Object'
                )

            layout.prop_search(
                slots,
                'slots_base_object',
                bpy.data,
                'objects',
                text='Slots Base Object'
                )

            layout.prop_search(
                slots,
                'slots_top_object',
                bpy.data,
                'objects',
                text='Slots Top Object'
                )

            _, box = draw(
                layout, 'object:lighting', 'Lighting Coefficients'
                )

            if box:

                ligthing = slots.ligthing
                box.label('Format:')
                row = box.row()
                row.prop(ligthing, 'format', expand=True, text='Format')

                box.prop_search(
                    ligthing,
                    'lights_image',
                    bpy.data,
                    'images',
                    text='Lights'
                    )

                if ligthing.format == 'builds_1569-cop':

                    box.prop_search(
                        ligthing,
                        'hemi_image',
                        bpy.data,
                        'images',
                        text='Hemi'
                        )

                    box.prop_search(
                        ligthing,
                        'shadows_image',
                        bpy.data,
                        'images',
                        text='Shadows'
                        )

            _, box = draw(
                layout, 'object:slots', 'Slots Meshes Indices'
                )

            if box:
                for i in range(4):
                    box.prop_search(
                        slots.meshes,
                        'mesh_{}'.format(i),
                        bpy.data,
                        'images',
                        text='Mesh {}'.format(i)
                        )

            layout.operator(PackDetailsImages.bl_idname)

    def draw_header(self, context):
        self.layout.label(icon='PLUGIN')
