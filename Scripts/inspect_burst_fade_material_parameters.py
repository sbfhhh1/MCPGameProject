import unreal


PATHS = [
    "/Game/TransformationVFX/SM2SM/M_Generic_ModelFade",
    "/Game/TransformationVFX/Material/ObjectMaterial/MI_Chair_UniversalDissolve",
    "/Game/TransformationVFX/Material/ObjectMaterial/MI_TableRound_UniversalDissolve",
    "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade",
]

mel = unreal.MaterialEditingLibrary
for path in PATHS:
    asset = unreal.load_asset(path)
    unreal.log(f"[FadeParamInspect] Asset={path} Loaded={bool(asset)}")
    if not asset:
        continue
    try:
        unreal.log(f"[FadeParamInspect] ScalarNames={list(mel.get_scalar_parameter_names(asset))}")
        unreal.log(f"[FadeParamInspect] VectorNames={list(mel.get_vector_parameter_names(asset))}")
        unreal.log(f"[FadeParamInspect] TextureNames={list(mel.get_texture_parameter_names(asset))}")
    except Exception as error:
        unreal.log_warning(f"[FadeParamInspect] Parameter inspection failed: {error}")
    try:
        parent = asset.get_editor_property("parent")
        unreal.log(f"[FadeParamInspect] Parent={parent.get_path_name() if parent else 'None'}")
    except Exception:
        pass
