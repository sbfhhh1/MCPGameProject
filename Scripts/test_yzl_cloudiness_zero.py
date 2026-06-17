import unreal

instance = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade")
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Cloudiness", 0.0)
unreal.MaterialEditingLibrary.update_material_instance(instance)
unreal.log("[JadeTest] Cloudiness=0")
