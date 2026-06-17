import unreal


INSTANCE_PATH = "/Game/TransformationVFX/SM2SM/jude/MI_YZL_AncientJade"

instance = unreal.load_asset(INSTANCE_PATH)
mel = unreal.MaterialEditingLibrary

scalar_values = {
    "Cloudiness": 0.26,
    "Edge Transmission": 0.0,
    "Edge Transmission Power": 3.5,
    "Jade Noise Scale": 0.003,
    "Master Tint Amount": 0.0,
    "Ochre Stain Amount": 0.345334,
    # 以下两项语义已随沁色改为 UV 不规则点状而改变：
    # Contrast = 斑点边缘锐度(0..1)，Scale = UV 平铺次数(越大越密越小)。
    "Ochre Stain Contrast": 0.4,
    "Ochre Stain Scale": 6.0,
    "Polished Roughness": 0.020666,
    "Specular": 1.0,
    "SSS Amount": 0.35875,
    "Vein Scale": 1.63806,
    "Weathered Roughness": 0.32,
}

vector_values = {
    "Jade Body Color": unreal.LinearColor(0.017045, 0.050347, 0.022006, 1.0),
    "Master Tint": unreal.LinearColor(0.127230, 0.144097, 0.032772, 1.0),
    "Ochre Stain Color": unreal.LinearColor(0.074653, 0.027373, 0.004479, 1.0),
    "Ochre Stain Scatter Color": unreal.LinearColor(0.175347, 0.119467, 0.060272, 1.0),
    "Pale Vein Color": unreal.LinearColor(0.330000, 0.350000, 0.140000, 1.0),
    "SSS Scatter Color": unreal.LinearColor(0.403275, 0.421875, 0.280518, 1.0),
}

for name, value in scalar_values.items():
    mel.set_material_instance_scalar_parameter_value(instance, name, value)

for name, value in vector_values.items():
    mel.set_material_instance_vector_parameter_value(instance, name, value)

mel.update_material_instance(instance)
unreal.EditorAssetLibrary.save_loaded_asset(instance)
unreal.log("[JadeDefaults] Saved requested initial values to MI_YZL_AncientJade")
