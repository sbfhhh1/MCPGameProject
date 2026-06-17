import unreal
LOG="[SWITCHTO]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    log("NO_PIE")
else:
    idx = getattr(unreal, "_switch_idx", 1)
    target=None
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if "BP_Jade_Shatter" in a.get_name() or "BP_Return_SM_Jade" in a.get_name():
            target=a; break
    if target:
        for c in target.get_components_by_class(unreal.ActorComponent):
            if "Switcher" in c.get_class().get_name():
                c.call_method("SwitchToState", args=(idx,))
                log("SwitchToState({}) on {}".format(idx, c.get_class().get_name()))
                break
    else:
        log("no target")
log("DONE")
