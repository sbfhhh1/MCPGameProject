import unreal

LOG = "[OPEN_SM2SM]"
def log(m): unreal.log_warning("{} {}".format(LOG, m))
def P(o):
    try: return o.get_path_name() if o else "None"
    except Exception: return str(o)

# 1. 标记当前临时关卡为非脏，避免保存模态框
try:
    w = unreal.EditorLevelLibrary.get_editor_world()
    if w:
        pkg = w.get_outermost()
        pkg.set_dirty_flag(False)
        log("cleared dirty on {}".format(pkg.get_name()))
except Exception as e:
    log("clear dirty err {}".format(e))

# 2. 加载 SM2SM
ok = False
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ok = les.load_level("/Game/TransformationVFX/SM2SM/SM2SM")
    log("load_level ok={}".format(ok))
except Exception as e:
    log("load err {}".format(e))

# 3. 勘察 actor
try:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    log("CURRENT_LEVEL={}".format(P(unreal.EditorLevelLibrary.get_editor_world())))
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
                    sw = " SWITCHER"
        except Exception:
            pass
        log("ACTOR '{}' [{}] loc=({:.0f},{:.0f},{:.0f}){}{}".format(label, cls, loc.x,loc.y,loc.z, mesh, sw))
except Exception as e:
    log("inspect err {}".format(e))
log("DONE")
