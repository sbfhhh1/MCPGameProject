# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_list_seal_actors.json"


def main():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()
    found = []
    for a in actors:
        cls = a.get_class().get_name()
        label = a.get_actor_label()
        if "Seal" in cls or "Seal" in label or "Procedural" in cls or "Chinese" in label:
            found.append({"label": label, "class": cls})
    result = {"matches": found, "total_actors": len(actors)}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[list_seal_actors] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
