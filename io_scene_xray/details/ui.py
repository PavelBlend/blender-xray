
import bpy
from ..utils import is_helper_object
from ..ui.collapsible import draw


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

            m = context.object.xray.detail.model

            layout.label('Detail Model Properties:')

            layout.prop(m, 'no_waving', text='No Waving', toggle=True)
            layout.prop(m, 'min_scale', text='Min Scale')
            layout.prop(m, 'max_scale', text='Max Scale')
            layout.prop(m, 'index', text='Detail Index')
            layout.prop(m, 'color', text='')

        elif context.active_object.type == 'EMPTY':

            s = context.object.xray.detail.slots

            layout.label('Level Details Properties:')

            layout.prop_search(
                s,
                'meshes_object',
                bpy.data,
                'objects',
                text='Meshes Object'
                )

            layout.prop_search(
                s,
                'slots_base_object',
                bpy.data,
                'objects',
                text='Slots Base Object'
                )

            layout.prop_search(
                s,
                'slots_top_object',
                bpy.data,
                'objects',
                text='Slots Top Object'
                )

            _, box = draw(
                layout, 'object:lighting', 'Lighting Coefficients'
                )

            if box:

                l = s.ligthing
                box.label('Format:')
                row = box.row()
                row.prop(l, 'format', expand=True, text='Format')

                box.prop_search(
                    l,
                    'lights_image',
                    bpy.data,
                    'images',
                    text='Lights'
                    )

                if l.format == 'builds_1569-cop':

                    box.prop_search(
                        l,
                        'hemi_image',
                        bpy.data,
                        'images',
                        text='Hemi'
                        )

                    box.prop_search(
                        l,
                        'shadows_image',
                        bpy.data,
                        'images',
                        text='Shadows'
                        )

            _, box = draw(
                layout, 'object:slots', 'Slots Meshes Indices'
                )

            if box:
                m = s.meshes
                for i in range(4):
                    box.prop_search(
                        m,
                        'mesh_{}'.format(i),
                        bpy.data,
                        'images',
                        text='Mesh {}'.format(i)
                        )

    def draw_header(self, context):
        self.layout.label(icon='PLUGIN')
