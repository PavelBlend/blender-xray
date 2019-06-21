from ..version_utils import layout_split


def xprop(layout, data, prop, enabled=True, **kwargs):
    attrs = getattr(data.bl_rna, prop)[1]
    name = attrs.get('name', prop)
    row = layout.row()
    lay = layout_split(row, 0.33)
    lay.label(text=name + ':')
    lay = lay.row(align=True)
    lay_l = lay.row(align=True)
    lay_r = lay
    if not enabled:
        lay = lay.split(align=True)
        lay.enabled = False
    lay.prop(data, prop, text='', **kwargs)
    return lay_l, lay_r
