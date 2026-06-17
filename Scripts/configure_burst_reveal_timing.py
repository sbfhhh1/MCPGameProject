import unreal


for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        component.modify()
        component.set_editor_property("particle_fade_out_duration", 2.0)
        component.set_editor_property("model_fade_in_duration", 2.0)
        component.set_editor_property("model_fade_start_dissolve", 0.0)
        component.set_editor_property("model_fade_end_dissolve", 0.65)
        unreal.log(
            f"[BurstRevealConfig] Actor={actor.get_actor_label()} "
            "ParticleFade=2.0 ModelReveal=2.0 Dissolve=0.0->0.65"
        )

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
