import unreal


BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"

bp = unreal.load_asset(BP_PATH)
for graph in unreal.BlueprintEditorLibrary.get_graphs(bp):
    unreal.log(f"[BurstLegacyNode] Graph={graph.get_name()}")
    for node in unreal.BlueprintEditorLibrary.get_nodes(graph):
        details = []
        for pin in node.get_editor_property("pins"):
            default_object = pin.get_editor_property("default_object")
            default_value = pin.get_editor_property("default_value")
            if default_object:
                details.append(f"{pin.get_name()}={default_object.get_path_name()}")
            elif default_value:
                details.append(f"{pin.get_name()}={default_value}")
        text = " | ".join(details)
        if any(keyword in text for keyword in ["Chair", "TableRound", "Dissolve", "Material"]):
            unreal.log(
                f"[BurstLegacyNode] Node={node.get_name()} Class={node.get_class().get_name()} Pins={text}")
