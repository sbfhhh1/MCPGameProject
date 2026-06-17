import unreal

LOG = "[INSPECT_ONLY]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))
def P(o):
    try: return o.get_path_name() if o else "None"
    except Exception: return str(o)

w = unreal.EditorLevelLibrary.get_editor_world()
log("CURRENT_LEVEL={}".format(P(w)))
actors = unreal.EditorLevelLibrary.get_all_level_actors()
log("ACTOR_COUNT={}".format(len(actors)))
for a in actors:
    cls = a.get_class().get_name()
    label = a.get_actor_label()
    loc = a.get_actor_location()
    mesh = ""
    try:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and smc.static_mesh:
            mesh = " mesh={}".format(smc.static_mesh.get_name())
    except Exception:
        pass
    sw = ""
    try:
        for c in a.get_components_by_class(unreal.ActorComponent):
            if "Switcher" in c.get_class().get_name():
                sw = " [SWITCHER]"
    except Exception:
        pass
    log("ACTOR '{}' [{}] loc=({:.0f},{:.0f},{:.0f}){}{}".format(label, cls, loc.x,loc.y,loc.z, mesh, sw))
log("DONE")
