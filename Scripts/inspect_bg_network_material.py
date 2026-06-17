import unreal


for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if actor.get_actor_label().lower() != "bg":
        continue

    unreal.log(f"[BGInspect] Actor={actor.get_path_name()}")
    components = actor.get_components_by_class(unreal.StaticMeshComponent)
    for component_index, component in enumerate(components):
        mesh = component.get_editor_property("static_mesh")
        unreal.log(
            f"[BGInspect] Component={component_index} "
            f"Mesh={mesh.get_path_name() if mesh else 'None'} "
            f"Materials={component.get_num_materials()}"
        )
        for material_index in range(component.get_num_materials()):
            material = component.get_material(material_index)
            unreal.log(
                f"[BGInspect] Slot={material_index} "
                f"Material={material.get_path_name() if material else 'None'}"
            )
