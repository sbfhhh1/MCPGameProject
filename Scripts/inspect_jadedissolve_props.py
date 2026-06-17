import unreal

mel = unreal.MaterialEditingLibrary
for path in [
    "/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve",
    "/Game/TransformationVFX/Material/ObjectMaterial/M_Chair_Dissolve",
]:
    m = unreal.load_asset(path)
    unreal.log(f"[JDProp] === {m.get_name()} ===")
    unreal.log(f"[JDProp] blend={m.get_editor_property('blend_mode')} "
               f"shading={m.get_editor_property('shading_model')} "
               f"clip={m.get_editor_property('opacity_mask_clip_value')} "
               f"twosided={m.get_editor_property('two_sided')}")
    unreal.log(f"[JDProp] num_expr={mel.get_num_material_expressions(m)}")
    unreal.log(f"[JDProp] scalars={list(mel.get_scalar_parameter_names(m))}")
    try:
        dv = mel.get_material_default_scalar_parameter_value(m, "Dissolve Amount")
        unreal.log(f"[JDProp] Dissolve Amount default={dv}")
    except Exception as e:
        unreal.log_warning(f"[JDProp] dissolve read err {e}")

unreal.log("[JDProp] DONE")
