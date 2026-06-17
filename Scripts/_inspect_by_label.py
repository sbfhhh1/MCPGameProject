import unreal
LOG="[BYLABEL]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ("YF","TYS","YZL","Exhibition","BP_Return_SM_Jade"):
        ascale=a.get_actor_scale3d(); aloc=a.get_actor_location()
        info="ACTOR '{}' [{}] loc=({:.0f},{:.0f},{:.0f}) actor_scale=({:.2f},{:.2f},{:.2f})".format(
            lbl, a.get_class().get_name(), aloc.x,aloc.y,aloc.z, ascale.x,ascale.y,ascale.z)
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            sm=c.get_editor_property("static_mesh")
            ws=c.get_world_scale()
            if sm:
                box=sm.get_bounding_box()
                info+=" | '{}' world_scale=({:.1f},{:.1f},{:.1f}) worldsize=({:.1f},{:.1f},{:.1f})".format(
                    c.get_name(), ws.x,ws.y,ws.z, (box.max.x-box.min.x)*ws.x,(box.max.y-box.min.y)*ws.y,(box.max.z-box.min.z)*ws.z)
        log(info)
log("DONE")
