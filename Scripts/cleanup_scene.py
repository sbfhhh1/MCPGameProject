import unreal
acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
a=next(x for x in acts if x.get_actor_label()=='BP_Burst_SM_Test')
mis={'StaticMeshA':'MI_Burst_Jade_YF','StaticMeshB':'MI_Burst_Jade_TYS','StaticMeshC':'MI_Burst_Jade_YZL'}
for c in a.get_components_by_class(unreal.StaticMeshComponent):
 n=c.get_name().replace(' ','').replace('_','')
 for e in mis:
  if e in n:
   c.empty_override_materials()
   mi=unreal.load_asset('/Game/TransformationVFX/SM2SM/jude/BurstJade/'+mis[e])
   for i in range(max(c.get_num_materials(),1)):
    c.set_material(i,mi)
   c.set_visibility(e=='StaticMeshA',True)
unreal.log('[Cleanup] restored A visible jade, B/C hidden')