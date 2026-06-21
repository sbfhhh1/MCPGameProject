import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_level_mesh_details.json"


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def main():
    rows = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        comps = actor.get_components_by_class(unreal.StaticMeshComponent)
        if not comps:
            continue
        origin, extent = actor.get_actor_bounds(False)
        item = {
            "label": actor.get_actor_label(),
            "name": actor.get_name(),
            "class": actor.get_class().get_name(),
            "location": vec(actor.get_actor_location()),
            "bounds_origin": vec(origin),
            "bounds_extent": vec(extent),
            "meshes": [],
        }
        for comp in comps:
            mesh = comp.get_editor_property("static_mesh")
            mats = []
            for idx in range(comp.get_num_materials()):
                mat = comp.get_material(idx)
                mats.append(mat.get_path_name() if mat else "")
            item["meshes"].append({
                "component": comp.get_name(),
                "mesh": mesh.get_path_name() if mesh else "",
                "materials": mats,
            })
        rows.append(item)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    unreal.log("[LevelMeshDetails] wrote " + OUT)


main()
