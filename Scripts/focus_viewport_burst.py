import unreal

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
burst = next((a for a in actors if a.get_actor_label() == "BP_Burst_SM_Test"), None)
if burst:
    loc = burst.get_actor_location()
    cam_loc = unreal.Vector(loc.x - 450.0, loc.y, loc.z + 60.0)
    cam_rot = unreal.Rotator(0.0, -5.0, 0.0)  # pitch, yaw?, roll -> UE Rotator(roll,pitch,yaw)
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)
        unreal.log(f"[Focus] camera set to {cam_loc} looking at burst {loc}")
    except Exception as e:
        unreal.log_warning(f"[Focus] set camera failed: {e}")
else:
    unreal.log_warning("[Focus] burst actor not found")
