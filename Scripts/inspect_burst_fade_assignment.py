import unreal


for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        material = component.get_editor_property("particle_material")
        duration = component.get_editor_property("particle_fade_out_duration")
        exponent = component.get_editor_property("particle_fade_out_ease_exponent")
        unreal.log(
            f"[BurstFadeInspect] Actor={actor.get_actor_label()} "
            f"Material={material.get_path_name() if material else 'None'} "
            f"Duration={duration} EaseExponent={exponent}"
        )
