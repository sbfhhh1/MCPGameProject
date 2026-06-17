import unreal
LOG="[BPMAT]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))
BP_PATH="/Game/TransformationVFX/SM2SM/BP_Return_SM_Jade"
bp=unreal.EditorAssetLibrary.load_asset(BP_PATH)
MI=unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")

sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles=sds.k2_gather_subobject_data_for_blueprint(bp)
sw_done=0; mesh_done=0
for h in handles:
    data=sds.k2_find_subobject_data_from_handle(h)
    obj=unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
    if obj is None: continue
    cls=obj.get_class().get_name()
    if "Switcher" in cls:
        obj.set_editor_property("state_fade_materials", [MI, MI, MI])
        obj.set_editor_property("fallback_model_fade_material", MI)
        log("switcher StateFadeMaterials set x3 + fallback")
        sw_done+=1
    elif cls=="StaticMeshComponent" and "Static Mesh" in obj.get_name():
        n=max(obj.get_num_materials(),1)
        for i in range(n):
            obj.set_material(i, MI)
        log("mesh '{}' material set".format(obj.get_name()))
        mesh_done+=1
log("switcher={} meshes={}".format(sw_done, mesh_done))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(BP_PATH)
log("compiled+saved DONE")
