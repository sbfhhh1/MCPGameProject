import unreal
LOG="[CAPSET]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
world = unreal.EditorLevelLibrary.get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label()=="DiagCapture":
        unreal.EditorLevelLibrary.destroy_actor(a)
cap=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(-420,0,160), unreal.Rotator(0,0,0))
cap.set_actor_label("DiagCapture")
rt=unreal.RenderingLibrary.create_render_target2d(world, 960, 600, unreal.TextureRenderTargetFormat.RTF_RGBA8)
cc=cap.capture_component2d
cc.set_editor_property("texture_target", rt)
cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cc.set_editor_property("capture_every_frame", True)
cc.set_editor_property("capture_on_movement", True)
cc.set_editor_property("fov_angle", 37.5)
log("DiagCapture spawned DONE")
