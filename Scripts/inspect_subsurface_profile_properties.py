import unreal


profile = unreal.SubsurfaceProfileStruct()
for name in dir(profile):
    if not name.startswith("_"):
        unreal.log(f"[SSSProfileProperty] {name}")
