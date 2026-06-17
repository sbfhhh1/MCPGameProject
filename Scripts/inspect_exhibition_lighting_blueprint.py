import unreal


actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actor_subsystem.get_all_level_actors():
    if actor.get_actor_label() != "ExhibitionLightingRig_Professional":
        continue

    transform = actor.get_actor_transform()
    unreal.log(
        f"[LightingRigInspect] Class={actor.get_class().get_path_name()} "
        f"Location={transform.translation} Scale={transform.scale3d}"
    )
    unreal.log(
        f"[LightingRigInspect] Components={len(actor.get_components_by_class(unreal.ActorComponent))} "
        f"Key={actor.get_editor_property('key_intensity')} "
        f"Fill={actor.get_editor_property('fill_intensity')} "
        f"Top={actor.get_editor_property('top_intensity')} "
        f"Rim={actor.get_editor_property('rim_intensity')}"
    )
