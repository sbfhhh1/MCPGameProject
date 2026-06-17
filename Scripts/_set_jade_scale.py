import unreal
LOG="[SETSCALE]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

S = getattr(unreal, "_jade_scale", 150.0)
BP_PATH = "/Game/TransformationVFX/SM2SM/BP_Return_SM_Jade"
bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
log("gathered {} subobjects".format(len(handles)))
changed = 0
for h in handles:
    data = sds.k2_find_subobject_data_from_handle(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
    if obj is None:
        continue
    nm = obj.get_name()
    cls = obj.get_class().get_name()
    if cls == "StaticMeshComponent" and "Static Mesh" in nm:
        try:
            old = obj.get_editor_property("relative_scale3d")
            obj.set_editor_property("relative_scale3d", unreal.Vector(S, S, S))
            new = obj.get_editor_property("relative_scale3d")
            log("  '{}' scale {}->{}".format(nm, (old.x,old.y,old.z), (new.x,new.y,new.z)))
            changed += 1
        except Exception as e:
            log("  '{}' set err {}".format(nm, e))
log("changed {} components to scale {}".format(changed, S))

# 编译+保存蓝图
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(BP_PATH)
log("compiled+saved")
log("DONE")
