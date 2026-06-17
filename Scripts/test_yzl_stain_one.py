import unreal

instance = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Amount", 1.0)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Scale", 0.018)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Contrast", 0.65)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, "Ochre Stain Color", unreal.LinearColor(0.32, 0.07, 0.005, 1.0))
unreal.MaterialEditingLibrary.update_material_instance(instance)
unreal.log("[JadeStainTest] Stain=1")
