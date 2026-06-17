import unreal, json
out={}
folder="/Game/TransformationVFX/SM2SM/jude/BurstJade"
rest=[unreal.load_asset(folder+"/MI_YZL_Jade_YF_SSS"),unreal.load_asset(folder+"/MI_YZL_Jade_TYS_SSS"),unreal.load_asset(folder+"/MI_YZL_Jade_YZL_SSS")]
diss=[unreal.load_asset(folder+"/MI_YZL_JadeDiss_YF"),unreal.load_asset(folder+"/MI_YZL_JadeDiss_TYS"),unreal.load_asset(folder+"/MI_YZL_JadeDiss_YZL")]
out["rest_ok"]=[bool(m) for m in rest]; out["diss_ok"]=[bool(m) for m in diss]
bp=unreal.load_asset("/Game/TransformationVFX/BP/Examples/BP_Burst_SM")
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o=unreal.SubobjectDataBlueprintFunctionLibrary.get_object(sds.k2_find_subobject_data_from_handle(h))
    if o and "Switcher" in o.get_class().get_name():
        o.set_editor_property("StateFadeMaterials", rest)
        o.set_editor_property("StateDissolveMaterials", diss)
        out["bp"]=True; break
unreal.BlueprintEditorLibrary.compile_blueprint(bp); unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/BP/Examples/BP_Burst_SM")
# respawn instance
eas=unreal.EditorActorSubsystem()
for a in eas.get_all_level_actors():
    if a.get_actor_label()=="BP_Burst_SM_Test": eas.destroy_actor(a)
act=eas.spawn_actor_from_object(bp, unreal.Vector(250.0,0.0,150.0), unreal.Rotator(0,0,0)); act.set_actor_label("BP_Burst_SM_Test")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open("C:/UE_Project/MCPGameProject/Scripts/_set2.json","w").write(json.dumps(out,ensure_ascii=False))
