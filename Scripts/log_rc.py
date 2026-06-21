import unreal, json
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pool = None
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "ChineseSealPoolAnimator":
        pool = a
        break
if pool:
    unreal.log("[log_rc] " + json.dumps({
        "Rows": pool.get_editor_property("Rows"),
        "Columns": pool.get_editor_property("Columns"),
        "proc": len(pool.get_components_by_class(unreal.ProceduralMeshComponent)),
        "bEnableAnimation": pool.get_editor_property("bEnableAnimation"),
        "bUseImportedStaticMeshes": pool.get_editor_property("bUseImportedStaticMeshes"),
    }, default=str))
