import unreal


world = unreal.EditorLevelLibrary.get_game_world()
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
    if not actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        continue
    for mesh in actor.get_components_by_class(unreal.StaticMeshComponent):
        normalized = mesh.get_name().replace(" ", "").replace("_", "")
        if not any(name in normalized for name in ["StaticMeshA", "StaticMeshB", "StaticMeshC"]):
            continue
        material = mesh.get_material(0)
        dissolve = "N/A"
        if material and hasattr(material, "get_scalar_parameter_value"):
            try:
                dissolve = material.get_scalar_parameter_value("Dissolve Amount")
            except Exception:
                pass
        unreal.log(
            f"[BurstMeshSample] Mesh={mesh.get_name()} Visible={mesh.is_visible()} "
            f"Material={material.get_path_name() if material else 'None'} Dissolve={dissolve}"
        )
