import json, unreal
OUT = r"C:/UE_Project/MCPGameProject/Scripts/_terrain_bounds.json"
data = {"found": False}
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if actor.get_actor_label() != "Terrace_Terrain":
            continue
    except Exception:
        continue
    o, e = actor.get_actor_bounds(only_colliding_components=False)
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    data = {
        "found": True,
        "location": [loc.x, loc.y, loc.z],
        "rotation": [rot.pitch, rot.yaw, rot.roll],
        "bounds_origin": [o.x, o.y, o.z],
        "bounds_extent": [e.x, e.y, e.z],
    }
    pmc = actor.get_component_by_class(unreal.ProceduralMeshComponent)
    if pmc:
        data["pmc_num_sections"] = pmc.get_num_sections()
        data["pmc_visible"] = pmc.is_visible()
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
unreal.log("[probe_terrain_bounds] " + json.dumps(data))
