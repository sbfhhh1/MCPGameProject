import unreal

# 获取选中的actor
selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()
if not selected_actors:
    unreal.log("No actors selected")
else:
    for actor in selected_actors:
        unreal.log(f"Selected Actor: {actor.get_name()} (Class: {actor.get_class().get_name()})")
        # 获取所有StaticMeshComponent
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        for comp in components:
            unreal.log(f"  Component: {comp.get_name()}")
            num_mats = comp.get_num_materials()
            unreal.log(f"  Material slots: {num_mats}")
            for i in range(num_mats):
                mat = comp.get_material(i)
                if mat:
                    unreal.log(f"    Slot {i}: {mat.get_name()} (Path: {mat.get_path_name()})")
                else:
                    unreal.log(f"    Slot {i}: None")
        # 也检查子actor
        children = actor.get_components_by_class(unreal.ChildActorComponent)
        for child in children:
            child_actor = child.get_child_actor()
            if child_actor:
                unreal.log(f"  Child Actor: {child_actor.get_name()}")
                child_comps = child_actor.get_components_by_class(unreal.StaticMeshComponent)
                for comp in child_comps:
                    unreal.log(f"    Component: {comp.get_name()}")
                    num_mats = comp.get_num_materials()
                    for i in range(num_mats):
                        mat = comp.get_material(i)
                        if mat:
                            unreal.log(f"      Slot {i}: {mat.get_name()} (Path: {mat.get_path_name()})")

unreal.log("Done")
