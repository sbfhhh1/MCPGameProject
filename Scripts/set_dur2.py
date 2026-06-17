import unreal
BP='/Game/TransformationVFX/BP/Examples/BP_Burst_SM'
bp=unreal.load_asset(BP)
ss=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib=unreal.SubobjectDataBlueprintFunctionLibrary
for h in ss.k2_gather_subobject_data_for_blueprint(bp):
 d=ss.k2_find_subobject_data_from_handle(h)
 o=lib.get_object_for_blueprint(d,bp)
 if isinstance(o,unreal.BurstMeshStateSwitcherComponent):
  o.set_editor_property('model_fade_in_duration',5.0)
  o.set_editor_property('source_fade_out_duration',2.5)
  unreal.BlueprintEditorLibrary.compile_blueprint(bp)
  unreal.EditorAssetLibrary.save_loaded_asset(bp)
  break
acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
b=next((a for a in acts if a.get_actor_label()=='BP_Burst_SM_Test'),None)
if b:
 for sw in b.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
  sw.set_editor_property('model_fade_in_duration',5.0)
  sw.set_editor_property('source_fade_out_duration',2.5)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
unreal.log('[Dur] set 5/2.5 saved')