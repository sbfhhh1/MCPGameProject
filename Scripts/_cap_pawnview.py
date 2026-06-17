import unreal
LOG="[PAWNCAP]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
world = unreal.EditorLevelLibrary.get_game_world()
if not world:
    log("NO_PIE")
else:
    pcm = unreal.GameplayStatics.get_player_camera_manager(world, 0)
    if not pcm:
        log("no camera manager")
    else:
        cloc = pcm.get_camera_location()
        crot = pcm.get_camera_rotation()
        cfov = pcm.get_fov_angle()
        n = getattr(unreal, "_pcap_counter", 0) + 1
        unreal._pcap_counter = n
        fname = "pawn_{:02d}.png".format(n)
        done=False
        for cap in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SceneCapture2D):
            cap.set_actor_location_and_rotation(cloc, crot, False, False)
            cc = cap.capture_component2d
            cc.set_editor_property("fov_angle", cfov)
            rt = cc.get_editor_property("texture_target")
            if rt:
                cc.capture_scene()
                unreal.RenderingLibrary.export_render_target(world, rt,
                    "C:/UE_Project/MCPGameProject/Saved/_capframes", fname)
                log("{} camloc=({:.0f},{:.0f},{:.0f}) rot=(p{:.1f},y{:.1f}) fov={:.1f}".format(
                    fname, cloc.x,cloc.y,cloc.z, crot.pitch, crot.yaw, cfov))
                done=True
                break
        if not done:
            log("no capture actor / rt")
log("DONE")
