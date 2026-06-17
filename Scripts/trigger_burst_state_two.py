import unreal


world = unreal.EditorLevelLibrary.get_game_world()
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
for actor in actors:
    components = actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent)
    if components:
        components[0].switch_to_state(1)
        unreal.log(f"[BurstVerify] Requested state 2 on {actor.get_actor_label()}")
