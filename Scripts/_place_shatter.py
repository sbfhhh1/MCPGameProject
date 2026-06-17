import unreal
LOG="[PLACESH]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
ell=unreal.EditorLevelLibrary
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 删除旧的 BP_Return_SM_Jade 实例（避免重叠+按键冲突）
removed=0
for a in list(eas.get_all_level_actors()):
    cls=a.get_class().get_name()
    if "BP_Return_SM_Jade" in cls or "BP_Jade_Shatter" in cls:
        log("remove existing '{}' [{}]".format(a.get_actor_label(), cls))
        ell.destroy_actor(a); removed+=1
log("removed {}".format(removed))

bp=unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/SM2SM/BP_Jade_Shatter")
actor=ell.spawn_actor_from_object(bp, unreal.Vector(390.0,0.0,120.0), unreal.Rotator(0,0,0))
if actor:
    actor.set_actor_label("BP_Jade_Shatter")
    log("spawned BP_Jade_Shatter at (390,0,120)")
else:
    log("SPAWN FAILED")
log("DONE")
