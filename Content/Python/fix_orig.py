import unreal, json, os

r = {}

mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS")
if mat:
    # 断开Opacity连接 - 在Opaque模式下不需要Opacity
    unreal.MaterialEditingLibrary.connect_material_property(None, "", unreal.MaterialProperty.MP_OPACITY)
    r["opacity_disconnected"] = True
    
    # 重新编译
    unreal.MaterialEditingLibrary.recompile_material(mat)
    r["recompiled"] = True
    
    # 保存
    unreal.EditorAssetLibrary.save_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS", only_if_is_dirty=False)
    r["saved"] = True

with open(os.path.join(os.environ["USERPROFILE"], "fix_orig.json"), "w") as f:
    json.dump(r, f, indent=2)
