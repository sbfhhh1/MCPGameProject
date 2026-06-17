import unreal
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
b=next((a for a in actors if a.get_actor_label()=='BP_Burst_SM_Test'),None)
if b:
  for sw in b.get_components_by_class(unreal.BurstMeshStateSwitcherComponent):
    sw.set_editor_property('model_fade_in_duration',10.0)
    sw.set_editor_property('source_fade_out_duration',5.0)
    unreal.log('[SlowFade] set 10/5')