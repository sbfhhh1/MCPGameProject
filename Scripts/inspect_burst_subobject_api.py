import unreal


unreal.log(f"[BurstSubobjectAPI] HasSubsystem={hasattr(unreal, 'SubobjectDataSubsystem')}")
for class_name in ["SubobjectDataSubsystem", "SubobjectDataBlueprintFunctionLibrary"]:
    cls = getattr(unreal, class_name, None)
    if not cls:
        continue
    unreal.log(f"[BurstSubobjectAPI] Class={class_name}")
    for name in dir(cls):
        if not name.startswith("_"):
            unreal.log(f"[BurstSubobjectAPI] Method={name}")
