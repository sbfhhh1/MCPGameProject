import unreal


INSTANCE_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"

instance = unreal.load_asset(INSTANCE_PATH)
mel = unreal.MaterialEditingLibrary
mel.set_material_instance_vector_parameter_value(
    instance, "Jade Body Color", unreal.LinearColor(0.20, 0.225, 0.060, 1.0))
mel.set_material_instance_vector_parameter_value(
    instance, "Pale Vein Color", unreal.LinearColor(0.410348, 0.432292, 0.201886, 1.0))
mel.set_material_instance_vector_parameter_value(
    instance, "SSS Scatter Color", unreal.LinearColor(0.22, 0.245, 0.055, 1.0))
mel.set_material_instance_scalar_parameter_value(instance, "Cloudiness", 0.772)
mel.update_material_instance(instance)
unreal.EditorAssetLibrary.save_loaded_asset(instance)
unreal.log("[JadeTest] Restored instance parameters")
