import unreal, json, os

r = {}

# Step 1: 删除旧材质
mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"
try:
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        unreal.EditorAssetLibrary.delete_asset(mat_path)
        r["deleted"] = True
    else:
        r["not_exists"] = True
except Exception as e:
    r["delete_err"] = str(e)

# Step 2: 复制材质
try:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    source = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
    new_mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source)
    r["duplicated"] = new_mat.get_path_name() if new_mat else "None"
except Exception as e:
    r["dup_err"] = str(e)

# Step 3: 修改Blend Mode
try:
    if new_mat:
        new_mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        r["blend_mode"] = "translucent"
except Exception as e:
    r["blend_err"] = str(e)

# Step 4: 测试创建一个节点
try:
    if new_mat:
        da = unreal.MaterialEditingLibrary.create_material_expression(new_mat, unreal.MaterialExpressionScalarParameter)
        da.set_editor_property("parameter_name", "Dissolve Amount")
        da.set_editor_property("default_value", 0.0)
        r["node_created"] = da.get_name()
except Exception as e:
    r["node_err"] = str(e)

# Step 5: 测试connect_material_expressions的参数格式
try:
    # 先检查这个方法的签名
    r["connect_sig"] = str(unreal.MaterialEditingLibrary.connect_material_expressions.__doc__[:500] if hasattr(unreal.MaterialEditingLibrary.connect_material_expressions, '__doc__') and unreal.MaterialEditingLibrary.connect_material_expressions.__doc__ else "no doc")
except Exception as e:
    r["sig_err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ue5_step1.json"), "w") as f:
    json.dump(r, f, indent=2)
