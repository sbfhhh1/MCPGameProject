import unreal

LOG = "[DUP_JADE]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))

SRC = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
DST = "/Game/TransformationVFX/SM2SM/BP_Return_SM_Jade"

# 读取旧实例 BP_Burst_SM_Test 的完整 transform（用于新实例摆放）
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "BP_Burst_SM_Test":
        t = a.get_actor_transform()
        loc = a.get_actor_location(); rot = a.get_actor_rotation(); scl = a.get_actor_scale3d()
        log("OLD_INSTANCE loc=({:.2f},{:.2f},{:.2f}) rot=(p{:.2f},y{:.2f},r{:.2f}) scl=({:.3f},{:.3f},{:.3f})".format(
            loc.x,loc.y,loc.z, rot.pitch,rot.yaw,rot.roll, scl.x,scl.y,scl.z))
        break

# 复制资产
if unreal.EditorAssetLibrary.does_asset_exist(DST):
    log("DST already exists, deleting first")
    unreal.EditorAssetLibrary.delete_asset(DST)
ok = unreal.EditorAssetLibrary.duplicate_asset(SRC, DST)
log("duplicate ok = {}".format(bool(ok)))
log("DST exists = {}".format(unreal.EditorAssetLibrary.does_asset_exist(DST)))
unreal.EditorAssetLibrary.save_asset(DST)
log("DONE")
