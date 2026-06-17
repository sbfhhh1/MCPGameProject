import unreal


INSTANCE_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"

instance = unreal.load_asset(INSTANCE_PATH)
asset_editor = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
asset_editor.close_all_editors_for_asset(instance)
asset_editor.open_editor_for_assets([instance])
unreal.log("[JadeEditor] Reopened MI_YZL_AncientJade editor with refreshed preview")
