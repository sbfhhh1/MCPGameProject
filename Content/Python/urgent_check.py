import unreal, json, os

r = {}

actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    if a.get_name() == "part_00000001_0":
        smc = a.get_components_by_class(unreal.StaticMeshComponent)[0]
        m = smc.get_material(0)
        r["mat_path"] = m.get_path_name() if m else "None"
        r["mat_name"] = m.get_name() if m else "None"
        r["mat_class"] = m.get_class().get_name() if m else "None"
        
        # 检查材质实例的父材质
        if m and "MaterialInstanceConstant" in m.get_class().get_name():
            p = m.get_editor_property("parent")
            r["parent"] = p.get_path_name() if p else "None"
            if p:
                r["parent_blend"] = str(p.get_editor_property("blend_mode"))
                r["parent_shading"] = str(p.get_editor_property("shading_model"))
        break

with open(os.path.join(os.environ["USERPROFILE"], "urgent_check.json"), "w") as f:
    json.dump(r, f, indent=2)
