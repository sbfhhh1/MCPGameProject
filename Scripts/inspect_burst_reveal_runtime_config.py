import unreal


for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for component in actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        materials = component.get_editor_property("state_fade_materials")
        unreal.log(
            f"[BurstRevealInspect] Actor={actor.get_actor_label()} "
            f"Start={component.get_editor_property('model_fade_start_dissolve')} "
            f"End={component.get_editor_property('model_fade_end_dissolve')} "
            f"Duration={component.get_editor_property('model_fade_in_duration')} "
            f"Fallback={component.get_editor_property('fallback_model_fade_material')}"
        )
        for index, material in enumerate(materials):
            unreal.log(
                f"[BurstRevealInspect] State={index + 1} "
                f"Material={material.get_path_name() if material else 'None'}"
            )
