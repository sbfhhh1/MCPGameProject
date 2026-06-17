import unreal
LOG="[DISPJADE]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
GUIDS=["20260613130638_a1276204","20260613132029_aabaf03a","20260613133607_ec021d65","20260613123723_f8ed59ab"]
world = unreal.EditorLevelLibrary.get_editor_world()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lbl = a.get_actor_label()
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property("static_mesh")
        if sm and any(g in sm.get_name() for g in GUIDS):
            ascale=a.get_actor_scale3d(); rs=c.get_editor_property("relative_scale3d"); ws=c.get_world_scale()
            box=sm.get_bounding_box(); bx=box.max.x-box.min.x; by=box.max.y-box.min.y; bz=box.max.z-box.min.z
            log("ACTOR '{}' actor_scale=({:.1f},{:.1f},{:.1f}) | '{}' rel=({:.1f},{:.1f},{:.1f}) world=({:.1f},{:.1f},{:.1f}) mesh={} size=({:.2f},{:.2f},{:.2f}) -> worldsize=({:.1f},{:.1f},{:.1f})".format(
                lbl, ascale.x,ascale.y,ascale.z, c.get_name(), rs.x,rs.y,rs.z, ws.x,ws.y,ws.z, sm.get_name(), bx,by,bz, bx*ws.x,by*ws.y,bz*ws.z))
log("DONE")
