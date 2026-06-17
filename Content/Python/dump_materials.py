import unreal
import json
import os

result = {"actors": []}
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    actor_info = {"name": a.get_name(), "label": a.get_actor_label(), "class": a.get_class().get_name(), "materials": []}
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        comp_info = {"component": c.get_name(), "slots": []}
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if m:
                comp_info["slots"].append({"index": i, "name": m.get_name(), "path": m.get_path_name()})
        if comp_info["slots"]:
            actor_info["materials"].append(comp_info)
    # Also check child actor components
    for c in a.get_components_by_class(unreal.ChildActorComponent):
        child_actor = c.get_child_actor()
        if child_actor:
            for cc in child_actor.get_components_by_class(unreal.StaticMeshComponent):
                comp_info = {"component": f"Child:{cc.get_name()}", "slots": []}
                for i in range(cc.get_num_materials()):
                    m = cc.get_material(i)
                    if m:
                        comp_info["slots"].append({"index": i, "name": m.get_name(), "path": m.get_path_name()})
                if comp_info["slots"]:
                    actor_info["materials"].append(comp_info)
    result["actors"].append(actor_info)

out_path = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\lafa"), "ue5_material_dump.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
