import unreal, json, os

r = {}

# 删除材质
mat_path = "/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve"
try:
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        unreal.EditorAssetLibrary.delete_asset(mat_path)
        r["deleted"] = True
    else:
        r["not_exists"] = True
except Exception as e:
    r["del_err"] = str(e)

# 重新复制
try:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    source = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
    mat = asset_tools.duplicate_asset("M_YZL_JadeDissolve", "/Game/TransformationVFX/SM2SM/jude", source)
    if mat:
        r["duplicated"] = mat.get_path_name()
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        r["blend_set"] = True
        
        # 检查orig emissive
        orig_e = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, "emissive_color")
        r["orig_emissive"] = orig_e.get_name() if orig_e else "None"
    else:
        r["dup_failed"] = True
except Exception as e:
    r["err"] = str(e)

with open(os.path.join(os.environ["USERPROFILE"], "ue5_clean.json"), "w") as f:
    json.dump(r, f, indent=2)
