import unreal


for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if actor.get_actor_label() != "BP_Burst_SM_Test":
        continue
    unreal.log(f"[BurstActorProperty] Actor={actor}")
    for name in dir(actor):
        lowered = name.lower()
        if any(keyword in lowered for keyword in ["material", "dissolve", "mesh", "fade"]):
            try:
                value = actor.get_editor_property(name)
                unreal.log(f"[BurstActorProperty] {name}={value}")
            except Exception:
                pass
