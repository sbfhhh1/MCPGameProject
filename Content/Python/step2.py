import unreal, json, os

# 先删除重建
mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"
if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
    unreal.EditorAssetLibrary.delete_asset(mat_path)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
source = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source)
r = {"step": "init"}

if not mat:
    r["error"] = "duplicate failed"
else:
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    
    # 检查OneMinus的输入名
    om_test = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionOneMinus)
    om_inputs = unreal.MaterialEditingLibrary.get_material_expression_input_names(om_test)
    r["oneminus_inputs"] = [str(x) for x in om_inputs]
    
    # 获取原有Emissive
    orig_emissive_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, "emissive_color")
    r["orig_emissive"] = orig_emissive_node.get_name() if orig_emissive_node else "None"
    
    # 也检查opacity
    orig_opacity_node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, "opacity")
    r["orig_opacity"] = orig_opacity_node.get_name() if orig_opacity_node else "None"

with open(os.path.join(os.environ["USERPROFILE"], "ue5_step2.json"), "w") as f:
    json.dump(r, f, indent=2)
