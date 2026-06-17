import unreal

LOG="[CAPEXP]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    log("NO_PIE_WORLD")
else:
    n = getattr(unreal, "_cap_counter", 0) + 1
    unreal._cap_counter = n
    fname = "cap_{:02d}.png".format(n)
    caps = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SceneCapture2D)
    done = False
    for cap in caps:
        cc = cap.capture_component2d
        rt = cc.get_editor_property("texture_target")
        if rt:
            cc.capture_scene()
            unreal.RenderingLibrary.export_render_target(
                world, rt, "C:/UE_Project/MCPGameProject/Saved/_capframes", fname)
            log("exported {}".format(fname))
            done = True
            break
    if not done:
        log("NO_CAPTURE_ACTOR")
log("DONE")
