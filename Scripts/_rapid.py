import unreal
world=unreal.EditorLevelLibrary.get_game_world()
b=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_actor_label()=="BP_Burst_SM_Test"),None)
sw=None
for c in b.get_components_by_class(unreal.ActorComponent):
    if "Switcher" in c.get_class().get_name(): sw=c; break
# 连续快速切换 1->2->0->1，模拟狂按
for idx in [1,2,0,1,2]:
    sw.call_method("SwitchToState", args=(idx,))
