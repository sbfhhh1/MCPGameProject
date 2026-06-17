import unreal


BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"

bp = unreal.load_asset(BP_PATH)
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
library = unreal.SubobjectDataBlueprintFunctionLibrary
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)

unreal.log(f"[BurstSubobject] Count={len(handles)}")
for handle in handles:
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    obj = library.get_object(data)
    obj_for_bp = library.get_object_for_blueprint(data, bp)
    unreal.log(
        f"[BurstSubobject] Display={library.get_display_name(data)} "
        f"Variable={library.get_variable_name(data)} "
        f"Object={obj} ObjectForBP={obj_for_bp}")
