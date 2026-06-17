import unreal


INSTANCE_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"

instance = unreal.load_asset(INSTANCE_PATH)
mel = unreal.MaterialEditingLibrary

if hasattr(mel, "clear_all_material_instance_parameters"):
    mel.clear_all_material_instance_parameters(instance)
else:
    instance.set_editor_property("scalar_parameter_values", [])
    instance.set_editor_property("vector_parameter_values", [])

mel.update_material_instance(instance)
unreal.EditorAssetLibrary.save_loaded_asset(instance)

scalar_overrides = instance.get_editor_property("scalar_parameter_values")
vector_overrides = instance.get_editor_property("vector_parameter_values")
unreal.log(
    f"[JadeDefaults] Cleared overrides: scalar={len(scalar_overrides)}, "
    f"vector={len(vector_overrides)}")
