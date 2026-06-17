import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

dirs = [
    "/Game/TransformationVFX/SM2SM/jude",
    "/Game/TransformationVFX/SM2SM/jude/BurstJade",
]

for d in dirs:
    for path in EAL.list_assets(d, recursive=False, include_folder=False):
        path = path.rstrip(".0123456789")  # strip object suffix if any
        asset = unreal.load_asset(path.split(".")[0])
        if not asset:
            continue
        cls = type(asset).__name__
        if cls not in ("Material", "MaterialInstanceConstant"):
            continue
        try:
            scalars = list(mel.get_scalar_parameter_names(asset))
            vectors = list(mel.get_vector_parameter_names(asset))
            textures = list(mel.get_texture_parameter_names(asset))
            parent = ""
            if isinstance(asset, unreal.MaterialInstanceConstant):
                p = asset.get_editor_property("parent")
                parent = p.get_path_name() if p else "None"
            total = len(scalars) + len(vectors) + len(textures)
            unreal.log(f"[JadeAll] {asset.get_name()} ({cls}) parent={parent} paramCount={total}")
            unreal.log(f"[JadeAll]    scalars={[str(s) for s in scalars]}")
            unreal.log(f"[JadeAll]    vectors={[str(v) for v in vectors]} textures={[str(t) for t in textures]}")
        except Exception as e:
            unreal.log_warning(f"[JadeAll] {path} err {e}")

unreal.log("[JadeAll] DONE")
