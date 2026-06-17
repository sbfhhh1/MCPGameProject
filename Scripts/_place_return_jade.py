import unreal

LOG = "[PLACE_JADE]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))
ell = unreal.EditorLevelLibrary

# 1. 删除旧的 BP_Burst_SM_Test 实例（避免双切换器冲突/几何重叠）
removed = 0
for a in ell.get_all_level_actors():
    if a.get_actor_label() == "BP_Burst_SM_Test":
        log("deleting old instance {} at {}".format(a.get_actor_label(), a.get_actor_location()))
        ell.destroy_actor(a)
        removed += 1
log("removed old instances = {}".format(removed))

# 2. spawn 新蓝图到旧实例位置 (265,0,90) yaw90
bp = unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/SM2SM/BP_Return_SM_Jade")
loc = unreal.Vector(265.0, 0.0, 90.0)
rot = unreal.Rotator(0.0, 0.0, 0.0)
rot.yaw = 90.0
new_actor = ell.spawn_actor_from_object(bp, loc, rot)
if new_actor:
    new_actor.set_actor_label("BP_Return_SM_Jade")
    new_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    nl = new_actor.get_actor_location(); nr = new_actor.get_actor_rotation()
    log("spawned '{}' [{}] loc=({:.1f},{:.1f},{:.1f}) yaw={:.1f}".format(
        new_actor.get_actor_label(), new_actor.get_class().get_name(), nl.x,nl.y,nl.z, nr.yaw))
else:
    log("SPAWN FAILED")
log("DONE")
