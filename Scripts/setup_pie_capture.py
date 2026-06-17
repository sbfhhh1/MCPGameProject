import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
burst = next(a for a in actors if a.get_actor_label() == "BP_Burst_SM_Test")
loc = burst.get_actor_location()

# remove old diag capture if any
for a in actors:
    if a.get_actor_label() == "DiagCapture":
        unreal.EditorLevelLibrary.destroy_actor(a)

cam_loc = unreal.Vector(loc.x - 450.0, loc.y, loc.z + 60.0)
cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, unreal.Rotator(0.0, -5.0, 0.0))
cap.set_actor_label("DiagCapture")

rt = unreal.RenderingLibrary.create_render_target2d(
    world, 800, 600, unreal.TextureRenderTargetFormat.RTF_RGBA8)
cc = cap.capture_component2d
cc.set_editor_property("texture_target", rt)
cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cc.set_editor_property("capture_every_frame", True)
cc.set_editor_property("capture_on_movement", True)
unreal.log("[PIECap] DiagCapture spawned looking at burst")
