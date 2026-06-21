import unreal


ASSET_DIR = "/Game/TransformationVFX/SM2SM/jude"
MATERIAL_NAME = "M_YZL_ProceduralJade_SSS"
INSTANCE_NAME = "MI_YZL_AncientJade"
PROFILE_NAME = "SSP_YZL_Jade"
TARGET_LABEL = "YZL"

HLSL = r"""
struct FJade
{
    float Hash31(float3 p)
    {
        p = frac(p * 0.1031);
        p += dot(p, p.yzx + 33.33);
        return frac((p.x + p.y) * p.z);
    }

    float Noise(float3 p)
    {
        float3 i = floor(p);
        float3 f = frac(p);
        f = f * f * (3.0 - 2.0 * f);
        float n000 = Hash31(i + float3(0,0,0));
        float n100 = Hash31(i + float3(1,0,0));
        float n010 = Hash31(i + float3(0,1,0));
        float n110 = Hash31(i + float3(1,1,0));
        float n001 = Hash31(i + float3(0,0,1));
        float n101 = Hash31(i + float3(1,0,1));
        float n011 = Hash31(i + float3(0,1,1));
        float n111 = Hash31(i + float3(1,1,1));
        return lerp(
            lerp(lerp(n000, n100, f.x), lerp(n010, n110, f.x), f.y),
            lerp(lerp(n001, n101, f.x), lerp(n011, n111, f.x), f.y),
            f.z);
    }

    float FBM(float3 p)
    {
        float value = 0.0;
        float amplitude = 0.55;
        [unroll] for (int i = 0; i < 5; ++i)
        {
            value += Noise(p) * amplitude;
            p = p * 2.03 + float3(19.1, 7.7, 13.4);
            amplitude *= 0.48;
        }
        return value;
    }

    float2 Hash22(float2 p)
    {
        p = float2(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)));
        return frac(sin(p) * 43758.5453);
    }

    // 可调参数（由材质参数经 struct 成员传入）：轮廓不规则度 / 边缘锯齿强度 / 锯齿细度。
    float WarpAmount;
    float EdgeRough;
    float EdgeDetail;

    // 不规则点状沁色：Worley/胞状噪声 + 域扭曲 + 高频边缘扰动。
    // 域扭曲让斑点轮廓不是规则圆形；高频噪声叠加到距离场让边缘呈不平滑的锯齿状，更像天然玉石沁色。
    float SpotField(float2 uv, float contrast)
    {
        // 1) 低频域扭曲：整体推移采样坐标，破坏圆形轮廓、打散分布。WarpAmount 越大越不规则。
        float2 warp = float2(
            FBM(float3(uv * 2.3 + 11.5, 0.0)),
            FBM(float3(uv * 2.3 + 41.7, 9.0))) - 0.5;
        float2 wuv = uv + warp * WarpAmount;

        // 2) 高频细节：叠加到距离场上 → 斑点边缘变成不规则锯齿。EdgeRough=强度，EdgeDetail=细度(频率)。
        float edgeWobble = (FBM(float3(uv * 8.0 * EdgeDetail, 3.0)) - 0.5) * 0.26 * EdgeRough
                         + (FBM(float3(uv * 17.0 * EdgeDetail, 21.0)) - 0.5) * 0.12 * EdgeRough;

        float2 g = floor(wuv);
        float2 f = frac(wuv);
        float coverage = 0.0;
        [unroll] for (int y = -1; y <= 1; ++y)
        {
            [unroll] for (int x = -1; x <= 1; ++x)
            {
                float2 cell = float2(x, y);
                float2 rnd = Hash22(g + cell);
                float d = length(cell + rnd - f) + edgeWobble;
                float present = step(0.40, frac(rnd.x * 1.3 + rnd.y * 2.7));
                float radius = lerp(0.10, 0.40, frac(rnd.x * 7.1)) * present;
                // 边缘过渡宽度由 contrast(Ochre Stain Contrast) 控制：越大越锐。
                float edge = lerp(0.05, 0.015, saturate(contrast));
                coverage = max(coverage, 1.0 - smoothstep(radius - edge, radius, d));
            }
        }
        return saturate(coverage);
    }

    // 多尺度叠加得到大小不一的斑点，再用低频噪声让斑点成簇分布，更接近真实沁色。
    float StainSpots(float2 uv, float contrast)
    {
        float spots = max(SpotField(uv, contrast), SpotField(uv * 1.9 + 11.3, contrast) * 0.85);
        float cluster = 0.25 + 0.75 * Noise(float3(uv * 0.6, 3.1));
        return saturate(spots * cluster);
    }

    float4 Render(
        float3 position, float2 stainUV, float noiseScale, float veinScale, float stainAmount,
        float stainScale, float stainContrast,
        float cloudiness, float roughMin, float roughMax,
        float3 bodyColor, float3 paleColor, float3 ochreColor)
    {
        float3 p = position * noiseScale;
        float broadCloud = FBM(p * 0.42);
        float folded = FBM(p * veinScale + FBM(p * 0.7) * 2.4);

        float paleVeins = smoothstep(0.42, 0.78, folded) * cloudiness;
        // 沁色改用 UV 空间的不规则点状噪声（随模型旋转），不再使用世界坐标与正弦条纹。
        float2 suv = stainUV * stainScale;
        float ochrePattern = StainSpots(suv, stainContrast);
        float ochre = ochrePattern * saturate(stainAmount);

        float cloudMask = saturate(paleVeins * 0.65 + broadCloud * cloudiness * 0.30);
        float stainMask = saturate(ochre);

        // Keep BodyColor dominant so a single instance color edit is immediately visible.
        float3 color = bodyColor * lerp(0.82, 1.18, broadCloud);
        color = lerp(color, paleColor, cloudMask * 0.38);
        float3 stainedColor = ochreColor * lerp(0.38, 0.72, ochrePattern);
        color = lerp(color, stainedColor, stainMask);

        float roughness = lerp(roughMin, roughMax, saturate(broadCloud * 0.85 + ochre * 0.50));
        return float4(color, roughness);
    }
};

FJade Jade;
Jade.WarpAmount = StainWarpAmount;
Jade.EdgeRough = StainEdgeRoughness;
Jade.EdgeDetail = StainEdgeDetail;
return Jade.Render(
    Position, StainUV, NoiseScale, VeinScale, StainAmount, StainScale, StainContrast, Cloudiness,
    RoughnessMin, RoughnessMax, BodyColor, PaleColor, OchreColor);
"""


def scalar(material, name, default, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, x, y)
    expression.set_editor_property("parameter_name", name)
    expression.set_editor_property("default_value", default)
    return expression


def vector(material, name, value, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, x, y)
    expression.set_editor_property("parameter_name", name)
    expression.set_editor_property("default_value", value)
    return expression


material_path = f"{ASSET_DIR}/{MATERIAL_NAME}"
instance_path = f"{ASSET_DIR}/{INSTANCE_NAME}"
profile_path = f"{ASSET_DIR}/{PROFILE_NAME}"

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
if unreal.EditorAssetLibrary.does_asset_exist(profile_path):
    profile = unreal.load_asset(profile_path)
else:
    profile = tools.create_asset(
        PROFILE_NAME, ASSET_DIR, unreal.SubsurfaceProfile, unreal.SubsurfaceProfileFactory())

profile_settings = unreal.SubsurfaceProfileStruct()
profile_settings.set_editor_property("enable_burley", True)
profile_settings.set_editor_property("enable_mean_free_path", True)
profile_settings.set_editor_property("mean_free_path_color", unreal.LinearColor(0.42, 0.64, 0.12, 1.0))
profile_settings.set_editor_property("mean_free_path_distance", 7.5)
profile_settings.set_editor_property("surface_albedo", unreal.LinearColor(0.48, 0.57, 0.20, 1.0))
profile_settings.set_editor_property("transmission_tint_color", unreal.LinearColor(0.62, 0.76, 0.22, 1.0))
profile_settings.set_editor_property("ior", 1.54)
profile_settings.set_editor_property("roughness0", 0.12)
profile_settings.set_editor_property("roughness1", 0.26)
profile_settings.set_editor_property("lobe_mix", 0.25)
profile_settings.set_editor_property("scattering_distribution", 0.72)
profile_settings.set_editor_property("world_unit_scale", 1.0)
profile.set_editor_property("settings", profile_settings)
unreal.EditorAssetLibrary.save_loaded_asset(profile)

# UE5.7 下对“已打开或被引用”的材质调用 delete_all_material_expressions 会触发
# Assertion failed: !IsRooted() 崩溃：材质编辑器/材质实例编辑器会把材质加入 root set，
# 而编辑器窗口的关闭是延迟到下一帧的（重启编辑器还会自动恢复上次打开的标签页），
# 同一帧内材质仍处于 rooted。稳妥做法：先关所有资产编辑器，再直接删除旧材质资产并重建，
# 完全绕开 delete_all_material_expressions（delete_asset 会自行强制关闭编辑器，不受 rooted 影响）。
asset_editor_subsystem = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# UE5.7 下 delete_all_material_expressions 在本材质上会触发 MarkAsGarbage 的 check(!IsRooted())
# 崩溃（某个表达式被 root 住，关编辑器/无头都无法规避）。改用 delete_asset 整资产删除重建
# （走 ObjectTools 强删，不触发该断言）。delete_asset 会孤立以本材质为父的实例，
# 因此【删除前自动扫描】jude 与 BurstJade 两个文件夹里所有以它为父的材质实例，重建后精确重挂。
_scan_folders = [
    "/Game/TransformationVFX/SM2SM/jude",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade",
]
child_instance_paths = []
if unreal.EditorAssetLibrary.does_asset_exist(material_path):
    old_material = unreal.load_asset(material_path)
    for _folder in _scan_folders:
        if not unreal.EditorAssetLibrary.does_directory_exist(_folder):
            continue
        for _asset_path in unreal.EditorAssetLibrary.list_assets(_folder, recursive=False, include_folder=False):
            _clean = _asset_path.split(".")[0]
            _obj = unreal.load_asset(_clean)
            if isinstance(_obj, unreal.MaterialInstanceConstant) and _obj.get_editor_property("parent") == old_material:
                child_instance_paths.append(_clean)
    unreal.log(f"[JadeSSS] Found {len(child_instance_paths)} child instance(s) parented to the jade material: {child_instance_paths}")
    # 关闭所有相关编辑器（无头模式下本就无编辑器，best-effort）。
    asset_editor_subsystem.close_all_editors_for_asset(old_material)
    unreal.EditorAssetLibrary.delete_asset(material_path)

if unreal.EditorAssetLibrary.does_asset_exist(material_path):
    raise RuntimeError("旧材质删除失败（仍被占用）。请关闭编辑器后用无头脚本重试。")
material = tools.create_asset(MATERIAL_NAME, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())
material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SUBSURFACE)
material.set_editor_property("two_sided", False)

position = mel.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1600, -700)
# 沁色采样坐标改用 UV（贴合表面、随模型旋转），不再用世界坐标。
tex_coord = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1600, -660)
noise_scale = scalar(material, "Jade Noise Scale", 0.003, -1600, -600)
vein_scale = scalar(material, "Vein Scale", 1.63806, -1600, -500)
stain_amount = scalar(material, "Ochre Stain Amount", 0.345334, -1600, -400)
# UV 空间下 StainScale 表示斑点平铺次数（数值越大斑点越密越小）。
stain_scale = scalar(material, "Ochre Stain Scale", 6.0, -1600, -350)
stain_contrast = scalar(material, "Ochre Stain Contrast", 0.4, -1600, -325)
# 斑点形状可调参数（材质实例里直接拖）：轮廓不规则度 / 边缘锯齿强度 / 锯齿细度。
stain_warp = scalar(material, "Stain Warp Amount", 0.9, -1600, -315)
stain_edge_rough = scalar(material, "Stain Edge Roughness", 1.0, -1600, -312)
stain_edge_detail = scalar(material, "Stain Edge Detail", 1.0, -1600, -309)
cloudiness = scalar(material, "Cloudiness", 0.26, -1600, -300)
rough_min = scalar(material, "Polished Roughness", 0.020666, -1600, -200)
rough_max = scalar(material, "Weathered Roughness", 0.32, -1600, -100)
body_color = vector(material, "Jade Body Color", unreal.LinearColor(0.017045, 0.050347, 0.022006, 1), -1600, 20)
pale_color = vector(material, "Pale Vein Color", unreal.LinearColor(0.33, 0.35, 0.14, 1), -1600, 120)
ochre_color = vector(material, "Ochre Stain Color", unreal.LinearColor(0.074653, 0.027373, 0.004479, 1), -1600, 220)

custom = mel.create_material_expression(material, unreal.MaterialExpressionCustom, -900, -350)
custom.set_editor_property("description", "Procedural ancient jade body, veins and沁色")
custom.set_editor_property("code", HLSL)
custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
input_names = [
    "Position", "StainUV", "NoiseScale", "VeinScale", "StainAmount", "StainScale", "StainContrast", "Cloudiness",
    "RoughnessMin", "RoughnessMax", "BodyColor", "PaleColor", "OchreColor",
    "StainWarpAmount", "StainEdgeRoughness", "StainEdgeDetail"
]
inputs = []
for name in input_names:
    item = unreal.CustomInput()
    item.set_editor_property("input_name", name)
    inputs.append(item)
custom.set_editor_property("inputs", inputs)
sources = [
    position, tex_coord, noise_scale, vein_scale, stain_amount, stain_scale, stain_contrast, cloudiness,
    rough_min, rough_max, body_color, pale_color, ochre_color,
    stain_warp, stain_edge_rough, stain_edge_detail
]
for source, name in zip(sources, input_names):
    mel.connect_material_expressions(source, "", custom, name)

rgb = mel.create_material_expression(material, unreal.MaterialExpressionComponentMask, -500, -390)
rgb.set_editor_property("r", True)
rgb.set_editor_property("g", True)
rgb.set_editor_property("b", True)
rgb.set_editor_property("a", False)
mel.connect_material_expressions(custom, "", rgb, "")

master_tint = vector(material, "Master Tint", unreal.LinearColor(0.127230, 0.144097, 0.032772, 1), -500, -620)
master_tint_amount = scalar(material, "Master Tint Amount", 0.0, -500, -520)
master_tint_lerp = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -220, -390)
mel.connect_material_expressions(rgb, "", master_tint_lerp, "A")
mel.connect_material_expressions(master_tint, "", master_tint_lerp, "B")
mel.connect_material_expressions(master_tint_amount, "", master_tint_lerp, "Alpha")

roughness = mel.create_material_expression(material, unreal.MaterialExpressionComponentMask, -500, -160)
roughness.set_editor_property("r", False)
roughness.set_editor_property("g", False)
roughness.set_editor_property("b", False)
roughness.set_editor_property("a", True)
mel.connect_material_expressions(custom, "", roughness, "")

scatter_color = vector(material, "SSS Scatter Color", unreal.LinearColor(0.403275, 0.421875, 0.280518, 1), -500, 20)
sss_amount = scalar(material, "SSS Amount", 0.35875, -500, 120)
specular = scalar(material, "Specular", 1.0, -500, 220)
edge_glow = scalar(material, "Edge Transmission", 0.0, -500, 320)
fresnel_power = scalar(material, "Edge Transmission Power", 3.5, -500, 420)
fresnel = mel.create_material_expression(material, unreal.MaterialExpressionFresnel, -260, 260)
mel.connect_material_expressions(fresnel_power, "", fresnel, "ExponentIn")
transmission = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, 0, 260)
mel.connect_material_expressions(fresnel, "", transmission, "A")
mel.connect_material_expressions(edge_glow, "", transmission, "B")
transmission_color = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, 220, 260)
mel.connect_material_expressions(transmission, "", transmission_color, "A")
mel.connect_material_expressions(scatter_color, "", transmission_color, "B")

stain_mask = mel.create_material_expression(material, unreal.MaterialExpressionCustom, -100, 40)
stain_mask.set_editor_property("description", "Localized ochre stain mask for SSS")
# 与 BaseColor 沁色保持一致：UV 空间的不规则点状（Worley 胞状噪声），随模型旋转。
stain_mask.set_editor_property("code", """
struct FStain
{
    float2 Hash22(float2 p)
    {
        p = float2(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)));
        return frac(sin(p) * 43758.5453);
    }
    float Hash21(float2 p)
    {
        p = frac(p * float2(123.34, 345.45));
        p += dot(p, p + 34.345);
        return frac(p.x * p.y);
    }
    // 2D 值噪声，用于域扭曲与边缘扰动（FStain 内自带，不依赖 FJade）。
    float VNoise(float2 p)
    {
        float2 i = floor(p);
        float2 f = frac(p);
        f = f * f * (3.0 - 2.0 * f);
        float a = Hash21(i);
        float b = Hash21(i + float2(1.0, 0.0));
        float c = Hash21(i + float2(0.0, 1.0));
        float d = Hash21(i + float2(1.0, 1.0));
        return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
    }
    float WarpAmount;
    float EdgeRough;
    float EdgeDetail;
    float SpotField(float2 uv, float contrast)
    {
        // 域扭曲打散圆形轮廓 + 高频噪声扰动距离场做不平滑边缘（与 BaseColor 沁色一致，参数同源）。
        float2 warp = float2(VNoise(uv * 2.3 + 11.5), VNoise(uv * 2.3 + 41.7)) - 0.5;
        float2 wuv = uv + warp * WarpAmount;
        float edgeWobble = (VNoise(uv * 8.0 * EdgeDetail) - 0.5) * 0.26 * EdgeRough
                         + (VNoise(uv * 17.0 * EdgeDetail) - 0.5) * 0.12 * EdgeRough;

        float2 g = floor(wuv);
        float2 f = frac(wuv);
        float coverage = 0.0;
        [unroll] for (int y = -1; y <= 1; ++y)
        {
            [unroll] for (int x = -1; x <= 1; ++x)
            {
                float2 cell = float2(x, y);
                float2 rnd = Hash22(g + cell);
                float d = length(cell + rnd - f) + edgeWobble;
                float present = step(0.40, frac(rnd.x * 1.3 + rnd.y * 2.7));
                float radius = lerp(0.10, 0.40, frac(rnd.x * 7.1)) * present;
                float edge = lerp(0.05, 0.015, saturate(contrast));
                coverage = max(coverage, 1.0 - smoothstep(radius - edge, radius, d));
            }
        }
        return saturate(coverage);
    }
    float Eval(float2 uv, float scale, float contrast, float amount)
    {
        float2 suv = uv * scale;
        float spots = max(SpotField(suv, contrast), SpotField(suv * 1.9 + 11.3, contrast) * 0.85);
        return spots * saturate(amount);
    }
};
FStain S;
S.WarpAmount = StainWarpAmount;
S.EdgeRough = StainEdgeRoughness;
S.EdgeDetail = StainEdgeDetail;
return S.Eval(StainUV, StainScale, StainContrast, StainAmount);
""")
stain_mask.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
stain_mask_inputs = []
for name in ["StainUV", "StainScale", "StainContrast", "StainAmount",
             "StainWarpAmount", "StainEdgeRoughness", "StainEdgeDetail"]:
    item = unreal.CustomInput()
    item.set_editor_property("input_name", name)
    stain_mask_inputs.append(item)
stain_mask.set_editor_property("inputs", stain_mask_inputs)
for source, name in [
    (tex_coord, "StainUV"),
    (stain_scale, "StainScale"),
    (stain_contrast, "StainContrast"),
    (stain_amount, "StainAmount"),
    (stain_warp, "StainWarpAmount"),
    (stain_edge_rough, "StainEdgeRoughness"),
    (stain_edge_detail, "StainEdgeDetail"),
]:
    mel.connect_material_expressions(source, "", stain_mask, name)

stain_scatter_color = vector(
    material, "Ochre Stain Scatter Color", unreal.LinearColor(0.175347, 0.119467, 0.060272, 1), -100, 120)
scatter_lerp = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, 180, 60)
mel.connect_material_expressions(scatter_color, "", scatter_lerp, "A")
mel.connect_material_expressions(stain_scatter_color, "", scatter_lerp, "B")
mel.connect_material_expressions(stain_mask, "", scatter_lerp, "Alpha")

mel.connect_material_property(master_tint_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(scatter_lerp, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
mel.connect_material_property(sss_amount, "", unreal.MaterialProperty.MP_OPACITY)
mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
mel.connect_material_property(transmission_color, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material)

if unreal.EditorAssetLibrary.does_asset_exist(instance_path):
    instance = unreal.load_asset(instance_path)
else:
    instance = tools.create_asset(
        INSTANCE_NAME, ASSET_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
unreal.MaterialEditingLibrary.set_material_instance_parent(instance, material)
unreal.MaterialEditingLibrary.update_material_instance(instance)
unreal.EditorAssetLibrary.save_loaded_asset(instance)

# 把删除前自动扫描到的所有子实例重新挂回新父材质（auto-discovered，不依赖名字），
# 并把语义已变的 UV 沁色参数设为合理值，确保它们跟随父材质、不掉父级（否则棋盘格）。
for child_path in child_instance_paths:
    if child_path == instance_path:  # 主实例已在上面处理
        continue
    if not unreal.EditorAssetLibrary.does_asset_exist(child_path):
        continue
    child = unreal.load_asset(child_path)
    mel.set_material_instance_parent(child, material)
    mel.set_material_instance_scalar_parameter_value(child, "Ochre Stain Scale", 6.0)
    mel.set_material_instance_scalar_parameter_value(child, "Ochre Stain Contrast", 0.4)
    mel.update_material_instance(child)
    unreal.EditorAssetLibrary.save_loaded_asset(child)
    unreal.log(f"[JadeSSS] Re-parented child instance {child_path}")

# 标签兜底：若场景里存在标签为 YZL 的独立 Actor，确保它也用上实例材质。
for actor in actor_subsystem.get_all_level_actors():
    if actor.get_actor_label().lower() != TARGET_LABEL.lower():
        continue
    actor.modify()
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        component.modify()
        for slot in range(max(component.get_num_materials(), 1)):
            component.set_material(slot, instance)
    unreal.log(f"[JadeSSS] Applied {INSTANCE_NAME} to {actor.get_actor_label()} by label")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[JadeSSS] Procedural ancient jade SSS material created")
