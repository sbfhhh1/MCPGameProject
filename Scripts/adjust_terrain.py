"""调整 Terrace_Terrain 的变换（按 label 查找）。改 PARAMS 即可。"""
import json, unreal

PARAMS = {"loc": (150.0, 0.0, 160.0), "rot": (90.0, 0.0, 0.0), "scale": (1.5, 1.5, 1.5)}
OUT = r"C:/UE_Project/MCPGameProject/Scripts/_terrain_bounds.json"

for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if actor.get_actor_label() != "Terrace_Terrain":
            continue
    except Exception:
        continue
    actor.set_actor_location(unreal.Vector(*PARAMS["loc"]), False, False)
    r = unreal.Rotator(); r.pitch, r.yaw, r.roll = PARAMS["rot"]
    actor.set_actor_rotation(r, False)
    actor.set_actor_scale3d(unreal.Vector(*PARAMS["scale"]))
    o, e = actor.get_actor_bounds(only_colliding_components=False)
    data = {"found": True, "rotation": list(PARAMS["rot"]),
            "bounds_origin": [o.x, o.y, o.z], "bounds_extent": [e.x, e.y, e.z]}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    unreal.log("[adjust_terrain] " + json.dumps(data))
    break
