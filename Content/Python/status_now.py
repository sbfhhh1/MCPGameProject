import unreal, json, os

r = {}

# 检查YZL当前材质
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    if a.get_name() == "part_00000001_0":
        smc = a.get_components_by_class(unreal.StaticMeshComponent)[0]
        m = smc.get_material(0)
        r["current_mat"] = m.get_path_name() if m else "None"
        break

# 检查M_YZL_JadeDissolve的Opacity连接
mat = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/M_YZL_JadeDissolve")
if mat:
    op = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY)
    r["op_node"] = op.get_name() if op else "None"

# 检查MI的DissolveProgress值
mi = unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/MI_YZL_JadeDissolve")
if mi:
    dp = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, "DissolveProgress")
    r["dissolve_progress"] = dp

with open(os.path.join(os.environ["USERPROFILE"], "status_now.json"), "w") as f:
    json.dump(r, f, indent=2)
