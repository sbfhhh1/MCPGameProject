import unreal


material_path = "/Game/TransformationVFX/Material/CharactorMaterial/MI_Manny_Particle"
system_path = "/Game/TransformationVFX/Niagara/NS_Inhalation_SM"

material = unreal.load_asset(material_path)
system = unreal.load_asset(system_path)

unreal.log(f"[BurstInspect] Material={material.get_path_name() if material else 'None'}")
if material:
    for parameter in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material):
        unreal.log(f"[BurstInspect] Scalar={parameter}")
    for parameter in unreal.MaterialEditingLibrary.get_vector_parameter_names(material):
        unreal.log(f"[BurstInspect] Vector={parameter}")

unreal.log(f"[BurstInspect] System={system.get_path_name() if system else 'None'}")
if system:
    store = system.get_editor_property("exposed_parameters")
    unreal.log(f"[BurstInspect] ExposedParameters={store.export_text()}")
