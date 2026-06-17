import unreal


for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_actor_label().lower() != "yzl":
        continue
    unreal.log(f"[JadeInspect] Actor={actor.get_path_name()} Class={actor.get_class().get_path_name()}")
    for index, component in enumerate(actor.get_components_by_class(unreal.StaticMeshComponent)):
        mesh = component.get_editor_property("static_mesh")
        unreal.log(
            f"[JadeInspect] Component={index} Name={component.get_name()} "
            f"Mesh={mesh.get_path_name() if mesh else 'None'} Slots={component.get_num_materials()}"
        )
        for slot in range(component.get_num_materials()):
            material = component.get_material(slot)
            unreal.log(
                f"[JadeInspect] Component={index} Slot={slot} "
                f"Material={material.get_path_name() if material else 'None'}"
            )
