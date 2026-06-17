import unreal

BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
BURST_LABEL = "BP_Burst_SM_Test"
DURATION = 3.5  # 更慢的溶解淡入，过程更明显

bp = unreal.load_asset(BP_PATH)
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    obj = lib.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.BurstMeshStateSwitcherComponent):
        obj.modify()
        obj.set_editor_property("model_fade_in_duration", DURATION)
        unreal.log(f"[FadeDur] SCS template model_fade_in_duration={DURATION}")
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        break

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
burst = next((a for a in actors if a.get_actor_label() == BURST_LABEL), None)
if burst:
    for sw in burst.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        sw.modify()
        sw.set_editor_property("model_fade_in_duration", DURATION)
        unreal.log(f"[FadeDur] level instance model_fade_in_duration={DURATION}")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[FadeDur] DONE")
