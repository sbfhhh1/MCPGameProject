import unreal
mat = unreal.EditorAssetLibrary.load_asset("/Game/TerraceTerrain/M_TerraceTerrain")
mat.set_editor_property("two_sided", True)
unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[fix_material_twosided] two_sided=True applied")
