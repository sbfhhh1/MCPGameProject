import unreal

# confirm Noise expression + enum availability
has_noise = hasattr(unreal, "MaterialExpressionNoise")
unreal.log(f"[Probe2] MaterialExpressionNoise={has_noise}")
nf = getattr(unreal, "NoiseFunction", None)
if nf:
    names = [a for a in dir(nf) if a.startswith("NOISEFUNCTION")]
    unreal.log(f"[Probe2] NoiseFunction values={names}")

# inspect BP_Basic_SM referenced dissolve material on its mesh components
bp = unreal.load_asset("/Game/TransformationVFX/BP/Examples/BP_Basic_SM")
unreal.log(f"[Probe2] BP_Basic_SM loaded={bool(bp)}")
if bp:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        obj = lib.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.StaticMeshComponent):
            for i in range(max(obj.get_num_materials(), 1)):
                m = obj.get_material(i)
                unreal.log(f"[Probe2] BP_Basic_SM mesh comp '{obj.get_name()}' mat[{i}]={m.get_path_name() if m else None}")

unreal.log("[Probe2] DONE")
