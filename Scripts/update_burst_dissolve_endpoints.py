import unreal

BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
BURST_LABEL = "BP_Burst_SM_Test"

# 玉石溶解材质语义：0.0=完全溶解消失 -> 1.0=完全显示（淡入出现）
START = 0.0
END = 1.0

bp = unreal.load_asset(BP_PATH)

# --- SCS template ---
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
library = unreal.SubobjectDataBlueprintFunctionLibrary
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
switcher_tmpl = None
for handle in handles:
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    obj = library.get_object_for_blueprint(data, bp)
    if obj and isinstance(obj, unreal.BurstMeshStateSwitcherComponent):
        switcher_tmpl = obj
        break

if switcher_tmpl:
    switcher_tmpl.modify()
    switcher_tmpl.set_editor_property("model_fade_start_dissolve", START)
    switcher_tmpl.set_editor_property("model_fade_end_dissolve", END)
    unreal.log(f"[DissolveEndpoints] SCS template start={START} end={END}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
else:
    unreal.log_warning("[DissolveEndpoints] SCS switcher template not found")

# --- level instance ---
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
burst_actor = next((a for a in actors if a.get_actor_label() == BURST_LABEL), None)
if burst_actor:
    for sw in burst_actor.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
        sw.modify()
        sw.set_editor_property("model_fade_start_dissolve", START)
        sw.set_editor_property("model_fade_end_dissolve", END)
        unreal.log(f"[DissolveEndpoints] level instance start={START} end={END}")
else:
    unreal.log_warning("[DissolveEndpoints] BP_Burst_SM_Test not found")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[DissolveEndpoints] DONE")
