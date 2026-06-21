# -*- coding: utf-8 -*-
"""给 BP_Burst_SM 蓝图添加 FistDisplayToggleComponent 组件。结果写 UE 日志。"""
import unreal

BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
CLASS_PATH = "/Script/MCPGameProject.FistDisplayToggleComponent"


def main():
    bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)
    if not bp:
        unreal.log("[add_fist] BP_NOT_FOUND")
        return

    comp_class = unreal.load_class(None, CLASS_PATH)
    if not comp_class:
        unreal.log("[add_fist] CLASS_NOT_FOUND - Live Coding 新类可能需重启编辑器才注册到 Python")
        return

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
    if not handles:
        unreal.log("[add_fist] NO_HANDLES")
        return

    # 检查是否已存在该组件，避免重复添加
    for h in handles:
        data = subsystem.k2_find_subobject_data_from_handle(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
        if obj and obj.get_class().get_name() == "FistDisplayToggleComponent":
            unreal.log("[add_fist] ALREADY_EXISTS skip")
            return

    root = handles[0]
    params = unreal.AddNewSubobjectParams()
    params.parent_handle = root
    params.new_class = comp_class
    params.blueprint_context = bp
    new_handle, fail = subsystem.add_new_subobject(params)
    if fail and not fail.is_empty():
        unreal.log("[add_fist] ADD_FAILED: " + str(fail))
        return

    subsystem.rename_subobject(new_handle, unreal.Text("FistDisplayToggle"))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(bp)
    unreal.log("[add_fist] DONE added FistDisplayToggle to BP_Burst_SM saved=%s" % saved)


if __name__ == "__main__":
    main()
