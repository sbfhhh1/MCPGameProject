"""探测 frame 区域 actor 的网格与包围盒，写入 json 供放置地形参考。"""
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_frame_bounds.json"
TARGET = unreal.Vector(202.0, 0.0, 160.0)

data = {"actors": []}
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        loc = actor.get_actor_location()
    except Exception:
        continue
    if (loc - TARGET).length() > 5.0:
        continue
    origin, extent = actor.get_actor_bounds(only_colliding_components=False)
    entry = {
        "name": actor.get_name(),
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location": [loc.x, loc.y, loc.z],
        "rotation": None,
        "bounds_origin": [origin.x, origin.y, origin.z],
        "bounds_extent": [extent.x, extent.y, extent.z],
    }
    rot = actor.get_actor_rotation()
    entry["rotation"] = [rot.pitch, rot.yaw, rot.roll]
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        mesh = smc.get_editor_property("static_mesh")
        entry["mesh"] = mesh.get_path_name() if mesh else None
    data["actors"].append(entry)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
unreal.log(f"[probe_frame_bounds] wrote {OUT} with {len(data['actors'])} actors")
