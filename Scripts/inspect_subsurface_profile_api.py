import unreal


for name in dir(unreal):
    if "subsurface" in name.lower() or "substrate" in name.lower():
        unreal.log(f"[SSSAPI] {name}")
