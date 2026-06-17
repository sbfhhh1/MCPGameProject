import unreal


for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_actor_label().lower() == "yzl":
        origin, extent = actor.get_actor_bounds(False)
        unreal.log(f"[YZLBounds] Origin={origin} Extent={extent}")
