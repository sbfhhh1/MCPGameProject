import unreal
world=unreal.EditorLevelLibrary.get_game_world()
cap=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SceneCapture2D) if a.get_actor_label()=="PawnCap"),None)
i=getattr(unreal,"_h",0); unreal._h=i+1
if cap:
    cc=cap.capture_component2d; rt=cc.get_editor_property("texture_target")
    cc.capture_scene(); unreal.RenderingLibrary.export_render_target(world, rt, "C:/UE_Project/MCPGameProject/Scripts","h_%02d.png"%i)
