import unreal
LOG="[REFJADE]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
GUIDS=["20260613130638_a1276204","20260613132029_aabaf03a","20260613133607_ec021d65","20260613123723_f8ed59ab"]
world = unreal.EditorLevelLibrary.get_editor_world()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    cls = a.get_class().get_name()
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm=c.get_editor_property("static_mesh")
        if sm and any(g in sm.get_name() for g in GUIDS):
            loc=a.get_actor_location(); rot=a.get_actor_rotation(); scl=a.get_actor_scale3d()
            log("'{}' [{}] mesh={} loc=({:.0f},{:.0f},{:.0f}) rot=(roll{:.0f},pitch{:.0f},yaw{:.0f}) scale=({:.0f},{:.0f},{:.0f})".format(
                a.get_actor_label(), cls, sm.get_name().split('_')[-1] if '_' in sm.get_name() else sm.get_name(),
                loc.x,loc.y,loc.z, rot.roll,rot.pitch,rot.yaw, scl.x,scl.y,scl.z))
log("DONE")
