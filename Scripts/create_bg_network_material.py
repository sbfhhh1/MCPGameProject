import unreal


ASSET_DIR = "/Game/TransformationVFX/SM2SM"
MATERIAL_NAME = "M_BG_Network"
INSTANCE_NAME = "MI_BG_Network"
TARGET_LABEL = "BG"


HLSL = r"""
struct FNetworkShader
{
    float Hash21(float2 p)
    {
        float3 a = frac(float3(p.x, p.y, p.x) * float3(213.897, 653.453, 253.098));
        a += dot(a, a.yzx + 79.76);
        return frac((a.x + a.y) * a.z);
    }

    float2 GetPos(float2 id, float2 offs, float t)
    {
        float n = Hash21(id + offs);
        float n1 = frac(n * 10.0);
        float n2 = frac(n * 100.0);
        float a = t + n;
        return offs + float2(sin(a * n1), cos(a * n2)) * 0.4;
    }

    float SegmentDistance(float2 a, float2 b, float2 p)
    {
        float2 pa = p - a;
        float2 ba = b - a;
        float h = saturate(dot(pa, ba) / max(dot(ba, ba), 0.0001));
        return length(pa - ba * h);
    }

    float Line(float2 a, float2 b, float2 p, float width)
    {
        float d = SegmentDistance(a, b, p);
        float d2 = length(a - b);
        float distanceGate = 1.0 - smoothstep(0.86, 1.18, d2);
        float lineShape = 1.0 - smoothstep(width * 0.45, width, d);
        return lineShape * distanceGate;
    }

    float Layer(float2 st, float n, float t, float width, float nodeSize)
    {
        float2 id = floor(st) + n;
        st = frac(st) - 0.5;
        float2 p[9];
        int index = 0;
        [unroll] for (int y = -1; y <= 1; ++y)
        {
            [unroll] for (int x = -1; x <= 1; ++x)
            {
                p[index++] = GetPos(id, float2(x, y), t);
            }
        }

        float m = 0.0;
        float sparkle = 0.0;
        [unroll] for (int i = 0; i < 9; ++i)
        {
            if (i != 4)
            {
                m = max(m, Line(p[4], p[i], st, width));
            }
            float d = max(length(st - p[i]), 0.002);
            float pulse = sin((frac(p[i].x) + frac(p[i].y) + t) * 5.0) * 0.4 + 0.6;
            float node = (nodeSize / max(d, 0.025)) * smoothstep(0.24, 0.04, d) * pow(pulse, 20.0);
            sparkle = max(sparkle, node);
        }

        m = max(m, Line(p[1], p[3], st, width));
        m = max(m, Line(p[1], p[5], st, width));
        m = max(m, Line(p[7], p[5], st, width));
        m = max(m, Line(p[7], p[3], st, width));
        float phase = (sin(t + n) + sin(t * 0.1)) * 0.25 + 0.5;
        return max(m, sparkle * phase * 0.35);
    }

    float3 Render(
        float2 uv, float timeValue, float density, float speed, float width,
        float nodeSize, float brightness, float rotationSpeed, float layerSpread,
        float vignette, float3 colorA, float3 colorB)
    {
        float t = timeValue * speed;
        float angle = t * rotationSpeed;
        float s = sin(angle);
        float c = cos(angle);
        uv -= 0.5;
        float2 st = mul(uv, float2x2(c, -s, s, c));
        float m = 0.0;

        [unroll] for (int layerIndex = 0; layerIndex < 4; ++layerIndex)
        {
            float i = layerIndex * 0.25;
            float z = frac(t * 0.1 + i);
            float size = lerp(density, max(1.0, density * 0.12), z);
            float fade = smoothstep(0.0, 0.6, z) * smoothstep(1.0, 0.8, z);
            m = max(m, fade * Layer(st * size - uv * z * layerSpread, i, t, width, nodeSize));
        }

        float colorPhase = sin(t * 0.2) * 0.5 + 0.5;
        float3 baseColor = lerp(colorA, colorB, colorPhase);
        float edgeFade = saturate(1.0 - dot(uv, uv) * vignette);
        float rawIntensity = max(m * edgeFade, 0.0);
        float cleanIntensity = smoothstep(0.18, 0.34, rawIntensity);
        return baseColor * cleanIntensity * brightness;
    }
};

FNetworkShader Shader;
return Shader.Render(UV, TimeValue, Density, Speed, LineWidth, NodeSize, Brightness, RotationSpeed, LayerSpread, Vignette, ColorA, ColorB);
"""


def log(message):
    unreal.log(f"[BGNetwork] {message}")


def delete_if_exists(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)


def scalar(mat, name, default, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, x, y)
    expression.set_editor_property("parameter_name", name)
    expression.set_editor_property("default_value", default)
    return expression


def vector(mat, name, value, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, x, y)
    expression.set_editor_property("parameter_name", name)
    expression.set_editor_property("default_value", value)
    return expression


def create_material():
    material_path = f"{ASSET_DIR}/{MATERIAL_NAME}"
    instance_path = f"{ASSET_DIR}/{INSTANCE_NAME}"
    delete_if_exists(instance_path)
    delete_if_exists(material_path)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(MATERIAL_NAME, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("two_sided", True)

    mel = unreal.MaterialEditingLibrary
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1500, -650)
    time_node = mel.create_material_expression(mat, unreal.MaterialExpressionTime, -1500, -560)
    density = scalar(mat, "Density", 15.0, -1500, -470)
    speed = scalar(mat, "Speed", 1.0, -1500, -380)
    width = scalar(mat, "Line Width", 0.055, -1500, -290)
    node_size = scalar(mat, "Node Size", 0.012, -1500, -200)
    brightness = scalar(mat, "Brightness", 12.0, -1500, -110)
    rotation_speed = scalar(mat, "Rotation Speed", 0.1, -1500, -20)
    layer_spread = scalar(mat, "Layer Spread", 1.0, -1500, 70)
    vignette = scalar(mat, "Vignette", 1.0, -1500, 160)
    color_a = vector(mat, "Color A", unreal.LinearColor(0.08, 1.2, 4.0, 1.0), -1500, 250)
    color_b = vector(mat, "Color B", unreal.LinearColor(3.5, 0.08, 4.0, 1.0), -1500, 340)

    custom = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, -850, -320)
    custom.set_editor_property("description", "Animated Network Layers")
    custom.set_editor_property("code", HLSL)
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    input_names = [
        "UV", "TimeValue", "Density", "Speed", "LineWidth", "NodeSize",
        "Brightness", "RotationSpeed", "LayerSpread", "Vignette", "ColorA", "ColorB"
    ]
    custom_inputs = []
    for name in input_names:
        custom_input = unreal.CustomInput()
        custom_input.set_editor_property("input_name", name)
        custom_inputs.append(custom_input)
    custom.set_editor_property("inputs", custom_inputs)
    sources = [
        uv, time_node, density, speed, width, node_size,
        brightness, rotation_speed, layer_spread, vignette, color_a, color_b
    ]
    for source, input_name in zip(sources, input_names):
        mel.connect_material_expressions(source, "", custom, input_name)

    opacity = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, -430, 120)
    opacity.set_editor_property("description", "Clean alpha without dark fringe")
    opacity.set_editor_property(
        "code",
        "float intensity = max(max(NetworkColor.r, NetworkColor.g), NetworkColor.b);"
        "return smoothstep(0.12, 1.0, intensity);"
    )
    opacity.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    opacity_input = unreal.CustomInput()
    opacity_input.set_editor_property("input_name", "NetworkColor")
    opacity.set_editor_property("inputs", [opacity_input])
    mel.connect_material_expressions(custom, "", opacity, "NetworkColor")

    mel.connect_material_property(custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)

    factory = unreal.MaterialInstanceConstantFactoryNew()
    instance = tools.create_asset(INSTANCE_NAME, ASSET_DIR, unreal.MaterialInstanceConstant, factory)
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, mat)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    return instance


def find_bg_actor():
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.get_actor_label().lower() == TARGET_LABEL.lower():
            return actor
    for actor in actors:
        if "bg" in actor.get_actor_label().lower() or "bg" in actor.get_name().lower():
            return actor
    return None


def apply_to_bg(instance):
    actor = find_bg_actor()
    if not actor:
        labels = [actor.get_actor_label() for actor in unreal.EditorLevelLibrary.get_all_level_actors()]
        raise RuntimeError(f"BG actor not found. Actors: {labels}")

    actor.modify()
    mesh_components = actor.get_components_by_class(unreal.StaticMeshComponent)
    if not mesh_components:
        raise RuntimeError(f"BG actor has no StaticMeshComponent: {actor.get_actor_label()}")
    for component in mesh_components:
        component.modify()
        for material_index in range(max(component.get_num_materials(), 1)):
            component.set_material(material_index, instance)
    log(f"Applied {INSTANCE_NAME} to {actor.get_actor_label()} without changing transform")


instance = create_material()
apply_to_bg(instance)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log("Material and instance created successfully")
