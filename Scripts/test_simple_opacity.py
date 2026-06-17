import unreal

mel = unreal.MaterialEditingLibrary
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve")

# 直接把 Dissolve Amount 接到 OpacityMask（无 noise），验证 PIE 里 OpacityMask+参数是否工作
diss = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, 200, 900)
diss.set_editor_property("parameter_name", "Dissolve Amount")
diss.set_editor_property("default_value", 1.0)
mel.connect_material_property(diss, "", unreal.MaterialProperty.MP_OPACITY_MASK)
mat.set_editor_property("opacity_mask_clip_value", 0.5)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[SimpleOp] OpacityMask = Dissolve Amount directly, clip 0.5")
