import unreal

# 删除诊断捕获相机
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for a in acts:
    if a.get_actor_label() == "DiagCapture":
        unreal.EditorLevelLibrary.destroy_actor(a)
        unreal.log("[Final] removed DiagCapture")

# 合理速度
BP = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
bp = unreal.load_asset(BP)
ss = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in ss.k2_gather_subobject_data_for_blueprint(bp):
    d = ss.k2_find_subobject_data_from_handle(h)
    o = lib.get_object_for_blueprint(d, bp)
    if isinstance(o, unreal.BurstMeshStateSwitcherComponent):
        o.set_editor_property("source_fade_out_duration", 2.0)
        o.set_editor_property("model_fade_in_duration", 4.0)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        break

b = next((a for a in acts if a.get_actor_label() == "BP_Burst_SM_Test"), None)
if b:
    for sw in b.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        sw.set_editor_property("source_fade_out_duration", 2.0)
        sw.set_editor_property("model_fade_in_duration", 4.0)
    for c in b.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_name().replace(" ", "").replace("_", "")
        if "StaticMeshA" in n:
            c.set_visibility(True)
        elif "StaticMeshB" in n or "StaticMeshC" in n:
            c.set_visibility(False)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[Final] DONE source=2.0 model=4.0")
