import unreal


MATERIAL_PATH = "/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS"
TARGET_LABEL = "YZL"

material = unreal.load_asset(MATERIAL_PATH)
unreal.log(f"[JadeNanite] material={material.get_path_name() if material else 'None'}")

if material:
    for property_name in ["used_with_nanite", "automatically_set_usage_in_editor"]:
        try:
            unreal.log(f"[JadeNanite] {property_name}={material.get_editor_property(property_name)}")
        except Exception as error:
            unreal.log_warning(f"[JadeNanite] unavailable {property_name}: {error}")

for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_actor_label().lower() != TARGET_LABEL.lower():
        continue
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        unreal.log(f"[JadeNanite] mesh={mesh.get_path_name() if mesh else 'None'}")
        if mesh:
            try:
                settings = mesh.get_editor_property("nanite_settings")
                unreal.log(f"[JadeNanite] nanite_enabled={settings.enabled}")
            except Exception as error:
                unreal.log_warning(f"[JadeNanite] nanite unavailable: {error}")
        for slot in range(component.get_num_materials()):
            assigned = component.get_material(slot)
            unreal.log(f"[JadeNanite] slot={slot} assigned={assigned.get_path_name() if assigned else 'None'}")
