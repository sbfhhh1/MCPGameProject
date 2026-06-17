import unreal

world = unreal.EditorLevelLibrary.get_game_world()
caps = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SceneCapture2D)
unreal.log(f"[PIECap] found {len(caps)} capture actors in PIE world")
for cap in caps:
    cc = cap.capture_component2d
    rt = cc.get_editor_property("texture_target")
    if rt:
        cc.capture_scene()
        unreal.RenderingLibrary.export_render_target(
            world, rt, "C:/UE_Project/MCPGameProject/Saved", "pie_actual.png")
        unreal.log("[PIECap] exported PIE view to pie_actual.png")
        break
