import unreal


paths = [
    "/Game/TransformationVFX/Material/ObjectMaterial/MI_Chair_UniversalDissolve",
    "/Game/TransformationVFX/Material/ObjectMaterial/MI_TableRound_UniversalDissolve",
]

for path in paths:
    material = unreal.load_asset(path)
    unreal.log(f"[FadeInspect] Material={material.get_path_name() if material else 'None'}")
    if not material:
        continue
    for name in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material):
        value = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, name)
        unreal.log(f"[FadeInspect] Scalar={name} Value={value}")
