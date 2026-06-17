import unreal

mel = unreal.MaterialEditingLibrary
M = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
unreal.log(f"[YZL] blend={M.get_editor_property('blend_mode')} shading={M.get_editor_property('shading_model')} "
           f"twosided={M.get_editor_property('two_sided')} clip={M.get_editor_property('opacity_mask_clip_value')}")

mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
unreal.log("[YZL] --- MI_YZL_AncientJade values ---")
for name in mel.get_scalar_parameter_names(mi):
    try:
        v = mel.get_material_instance_scalar_parameter_value(mi, name)
        unreal.log(f"[YZL] S '{name}'={v}")
    except Exception:
        pass
for name in mel.get_vector_parameter_names(mi):
    try:
        v = mel.get_material_instance_vector_parameter_value(mi, name)
        unreal.log(f"[YZL] V '{name}'=({v.r:.3f},{v.g:.3f},{v.b:.3f})")
    except Exception:
        pass
unreal.log("[YZL] DONE")
