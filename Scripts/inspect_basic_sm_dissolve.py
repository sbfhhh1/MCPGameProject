import unreal

mel = unreal.MaterialEditingLibrary

for path in [
    "/Game/TransformationVFX/Demo/Material/M_Chair",
    "/Game/TransformationVFX/Demo/Material/M_TableRound",
]:
    m = unreal.load_asset(path)
    if not m:
        unreal.log_warning(f"[BasicMat] missing {path}")
        continue
    base = m
    if isinstance(m, unreal.MaterialInstanceConstant):
        base = m.get_editor_property("parent")
    unreal.log(f"[BasicMat] === {m.get_name()} (base {base.get_name() if base else None}) ===")
    unreal.log(f"[BasicMat] blend={base.get_editor_property('blend_mode')} "
               f"shading={base.get_editor_property('shading_model')} "
               f"twosided={base.get_editor_property('two_sided')}")
    unreal.log(f"[BasicMat] scalars={[str(x) for x in mel.get_scalar_parameter_names(m)]}")
    unreal.log(f"[BasicMat] vectors={[str(x) for x in mel.get_vector_parameter_names(m)]}")
    unreal.log(f"[BasicMat] textures={[str(x) for x in mel.get_texture_parameter_names(m)]}")

# BP_Basic_SM mesh components + nanite
bp = unreal.load_asset("/Game/TransformationVFX/BP/Examples/BP_Basic_SM")
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    obj = lib.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.StaticMeshComponent):
        sm = obj.get_editor_property("static_mesh")
        nan = None
        if sm:
            try:
                nan = sm.get_editor_property("nanite_settings").get_editor_property("enabled")
            except Exception:
                pass
        unreal.log(f"[BasicMat] BP mesh comp '{obj.get_name()}' mesh={sm.get_name() if sm else None} nanite={nan}")

unreal.log("[BasicMat] DONE")
