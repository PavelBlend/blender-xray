from ..version_utils import layout_split, IS_28


def xprop(layout, data, prop, enabled=True, **kwargs):
    if IS_28:
        attrs = data.bl_rna.properties.get(prop)
        name = attrs.name
        split_factor = 0.242
    else:
        attrs = getattr(data.bl_rna, prop)[1]
        name = attrs.get('name', prop)
        split_factor = 0.33
    row = layout.row()
    lay = layout_split(row, split_factor)
    lay.label(text=name + ':')
    lay = lay.row(align=True)
    lay_l = lay.row(align=True)
    lay_r = lay
    if not enabled:
        lay = lay.split(align=True)
        lay.enabled = False
    lay.prop(data, prop, text='', **kwargs)
    return lay_l, lay_r
