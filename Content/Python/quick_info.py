import unreal
actors = unreal.EditorLevelLibrary.get_selected_level_actors()
for a in actors:
    unreal.log(f"SEL:{a.get_name()}")
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        unreal.log(f"COMP:{c.get_name()}")
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if m:
                unreal.log(f"MAT:{i}:{m.get_path_name()}")
