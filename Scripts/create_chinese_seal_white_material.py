# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_create_chinese_seal_white_material.json"
PACKAGE_PATH = "/Game/TransformationVFX/SM2SM/ChineseSeals"
ASSET_NAME = "M_ChineseSeal_DefaultWhite"
ASSET_PATH = PACKAGE_PATH + "/" + ASSET_NAME


def ensure_folder(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def set_scalar(material, property_name, parameter_name, value, x):
    # 用 ScalarParameter（而非 Constant），这样 Default Seal Metallic/Roughness/Specular
    # 可经动态材质实例由 C++ 覆盖生效。
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, x, 80
    )
    expression.set_editor_property("parameter_name", parameter_name)
    expression.set_editor_property("default_value", value)
    unreal.MaterialEditingLibrary.connect_material_property(expression, "", property_name)


def main():
    ensure_folder(PACKAGE_PATH)

    # 改材质前关闭它自己的编辑器窗口：材质在编辑器里打开会被加入 root set，
    # delete_all_material_expressions 会触发 !IsRooted() 断言崩溃。
    # （close_all_asset_editors/get_all_edited_assets 未暴露给 Python，用 close_all_editors_for_asset。）
    aes = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
        _existing = unreal.load_asset(ASSET_PATH)
        if _existing is not None:
            aes.close_all_editors_for_asset(_existing)

    material = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
    if not material:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = asset_tools.create_asset(
            ASSET_NAME,
            PACKAGE_PATH,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
    if not material:
        raise RuntimeError("Failed to create " + ASSET_PATH)

    if hasattr(unreal.MaterialEditingLibrary, "delete_all_material_expressions"):
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("two_sided", False)
    if hasattr(unreal, "MaterialShadingModel"):
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)

    # BaseColor 用 VectorParameter "BaseColor"（默认白），由 C++ 动态实例按 Default Seal Color 覆盖。
    base_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -420, -80
    )
    base_color.set_editor_property("parameter_name", "BaseColor")
    base_color.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        base_color, "", unreal.MaterialProperty.MP_BASE_COLOR
    )

    set_scalar(material, unreal.MaterialProperty.MP_METALLIC, "Metallic", 0.0, -420)
    set_scalar(material, unreal.MaterialProperty.MP_ROUGHNESS, "Roughness", 0.5, -220)
    set_scalar(material, unreal.MaterialProperty.MP_SPECULAR, "Specular", 0.5, -20)

    unreal.MaterialEditingLibrary.recompile_material(material)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(material)

    result = {
        "asset": ASSET_PATH,
        "saved": bool(saved),
        "base_color": [1.0, 1.0, 1.0, 1.0],
        "metallic": 0.0,
        "roughness": 0.5,
        "specular": 0.5,
        "shading": "DefaultLit",
        "blend": "Opaque",
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    unreal.log("[CreateChineseSealWhiteMaterial] " + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
