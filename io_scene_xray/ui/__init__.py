def xprop(layout, data, prop, enabled=True, **kwargs):
    attrs = getattr(data.bl_rna, prop)[1]
    name = attrs.get('name', prop)
    lay = layout.row().split(percentage=0.33)
    lay.label(name + ':')
    lay = lay.row(align=True)
    lay_l = lay.row(align=True)
    lay_r = lay
    if not enabled:
        lay = lay.split(align=True)
        lay.enabled = False
    lay.prop(data, prop, text='', **kwargs)
    return lay_l, lay_r
