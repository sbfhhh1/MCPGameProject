import unreal


TARGET_ACTORS = {"YF", "TYS", "YZL"}
BURST_LABEL = "BP_Burst_SM_Test"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

for actor in actors:
    if actor.get_actor_label() in TARGET_ACTORS:
        unreal.log(
            f"[BurstJadeInspect] SourceActor={actor.get_actor_label()} "
            f"Transform={actor.get_actor_transform()}")
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.get_editor_property("static_mesh")
            materials = [
                component.get_material(index).get_path_name()
                if component.get_material(index) else "None"
                for index in range(component.get_num_materials())
            ]
            unreal.log(
                f"[BurstJadeInspect] SourceActor={actor.get_actor_label()} "
                f"Component={component.get_name()} Mesh={mesh.get_path_name() if mesh else 'None'} "
                f"Relative={component.get_relative_transform()} Materials={materials}")

for actor in actors:
    if actor.get_actor_label() != BURST_LABEL:
        continue
    unreal.log(f"[BurstJadeInspect] BurstActor={actor.get_actor_label()} Transform={actor.get_actor_transform()}")
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        materials = [
            component.get_material(index).get_path_name()
            if component.get_material(index) else "None"
            for index in range(component.get_num_materials())
        ]
        unreal.log(
            f"[BurstJadeInspect] BurstComponent={component.get_name()} "
            f"Mesh={mesh.get_path_name() if mesh else 'None'} "
            f"Relative={component.get_relative_transform()} Visible={component.is_visible()} "
            f"Materials={materials}")
    for component in actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        for property_name in [
            "state_fade_materials",
            "state_particle_materials",
            "fallback_model_fade_material",
            "particle_system",
            "front_half_duration",
            "particle_fade_out_duration",
            "model_fade_in_duration",
        ]:
            unreal.log(
                f"[BurstJadeInspect] Switcher {property_name}="
                f"{component.get_editor_property(property_name)}")
