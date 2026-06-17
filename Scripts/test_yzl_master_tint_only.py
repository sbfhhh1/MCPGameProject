import unreal

instance = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
mel = unreal.MaterialEditingLibrary
mel.set_material_instance_vector_parameter_value(
    instance, "Master Tint", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
mel.set_material_instance_scalar_parameter_value(instance, "Master Tint Amount", 1.0)
mel.update_material_instance(instance)
unreal.log("[JadeTest] Master Tint only: red, amount=1")
