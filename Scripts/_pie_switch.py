import unreal

LOG = "[PIE_SWITCH]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))

world = None
try:
    world = unreal.EditorLevelLibrary.get_game_world()
except Exception as e:
    log("get_game_world err {}".format(e))

if not world:
    log("PIE_NOT_RUNNING")
else:
    log("game_world = {}".format(world.get_path_name()))
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    target = None
    for a in actors:
        if "BP_Return_SM_Jade" in a.get_name() or a.get_actor_label() == "BP_Return_SM_Jade":
            target = a
            break
    log("target actor = {}".format(target.get_name() if target else "None"))
    if target:
        comp = None
        for c in target.get_components_by_class(unreal.ActorComponent):
            if "Switcher" in c.get_class().get_name():
                comp = c
                break
        if comp:
            # 持久计数器，循环 1->2->0
            seq = getattr(unreal, "_jade_switch_seq", [1, 2, 0])
            counter = getattr(unreal, "_jade_switch_counter", 0)
            idx = seq[counter % len(seq)]
            unreal._jade_switch_counter = counter + 1
            comp.call_method("SwitchToState", args=(idx,))
            log("called SwitchToState({}) [call #{}]".format(idx, counter + 1))
        else:
            log("no switcher comp")
log("DONE")
