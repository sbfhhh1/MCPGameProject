import unreal, json
world=unreal.EditorLevelLibrary.get_game_world()
b=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_actor_label()=="BP_Burst_SM_Test"),None)
vis=[c.get_name() for c in b.get_components_by_class(unreal.StaticMeshComponent) if c.is_visible()]
open("C:/UE_Project/MCPGameProject/Scripts/_vc.json","w").write(json.dumps({"visible_count":len(vis),"meshes":vis}))
