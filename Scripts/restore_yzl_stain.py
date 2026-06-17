import unreal

instance = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Amount", 0.26)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Scale", 6.0)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Ochre Stain Contrast", 0.55)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, "Ochre Stain Color", unreal.LinearColor(0.30, 0.11, 0.018, 1.0))
unreal.MaterialEditingLibrary.update_material_instance(instance)
unreal.EditorAssetLibrary.save_loaded_asset(instance)
unreal.log("[JadeStainTest] Restored Stain=0.26")
