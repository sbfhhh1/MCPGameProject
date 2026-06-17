import unreal
tools=unreal.AssetToolsHelpers.get_asset_tools()
DIR="/Game/TransformationVFX/SM2SM/jude/BurstJade"
p="%s/SSP_Jade"%DIR
prof=unreal.load_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else tools.create_asset("SSP_Jade",DIR,unreal.SubsurfaceProfile,unreal.SubsurfaceProfileFactory())
unreal.log("[SSPdump] created="+str(bool(prof)))
st=prof.get_editor_property("settings")
props=[x for x in dir(st) if not x.startswith("_") and "color" in x.lower() or "scatter" in x.lower() or "radius" in x.lower()]
unreal.log("[SSPdump] props="+str(props))
unreal.EditorAssetLibrary.save_loaded_asset(prof)