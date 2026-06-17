import unreal
LOG="[NICHE]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
GUIDS=["20260613130638_a1276204","20260613132029_aabaf03a","20260613133607_ec021d65","20260613123723_f8ed59ab"]
ell = unreal.EditorLevelLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

removed_bp=0; removed_ref=0
for a in list(eas.get_all_level_actors()):
    cls = a.get_class().get_name()
    if "BP_Return_SM_Jade" in cls:
        log("remove BP instance '{}' at {}".format(a.get_actor_label(), a.get_actor_location()))
        ell.destroy_actor(a); removed_bp+=1
        continue
    if cls == "StaticMeshActor":
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            sm=c.get_editor_property("static_mesh")
            if sm and any(g in sm.get_name() for g in GUIDS):
                log("remove ref actor '{}' mesh={}".format(a.get_actor_label(), sm.get_name()))
                ell.destroy_actor(a); removed_ref+=1
                break
log("removed BP={} ref={}".format(removed_bp, removed_ref))

bp = unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/SM2SM/BP_Return_SM_Jade")
actor = ell.spawn_actor_from_object(bp, unreal.Vector(390.0,0.0,120.0), unreal.Rotator(0.0,0.0,0.0))
if actor:
    actor.set_actor_label("BP_Return_SM_Jade")
    actor.set_actor_scale3d(unreal.Vector(1,1,1))
    log("spawned fresh BP at (390,0,120) identity")
    # 确认网格世界尺寸
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.get_editor_property("static_mesh")
        if sm and any(g in sm.get_name() for g in GUIDS):
            ws=c.get_world_scale(); wl=c.get_world_location(); box=sm.get_bounding_box()
            log("  '{}' wloc=({:.0f},{:.0f},{:.0f}) wscale={:.0f} worldsize=({:.0f},{:.0f},{:.0f})".format(
                c.get_name(), wl.x,wl.y,wl.z, ws.x, (box.max.x-box.min.x)*ws.x,(box.max.y-box.min.y)*ws.y,(box.max.z-box.min.z)*ws.z))
else:
    log("SPAWN FAILED")
log("DONE")
