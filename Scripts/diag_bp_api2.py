"""
诊断第二轮：找 UE5.7 实际可用的蓝图/输入 API
exec(open(r"C:/UE_Project/MCPGameProject/Scripts/diag_bp_api2.py").read())
"""
import unreal

print("\n===== 诊断第二轮 =====")

# 1. BlueprintEditorLibrary 实际有哪些方法
bel = unreal.BlueprintEditorLibrary
available = [m for m in dir(bel) if not m.startswith("_")]
print(f"\nBlueprintEditorLibrary 可用方法 ({len(available)} 个):")
for m in available:
    print(f"  {m}")

# 2. 检查 SubsystemBlueprintLibrary / EditorUtilityLibrary
print("\n── 其他可用库 ──")
for lib_name in ["SubsystemBlueprintLibrary", "EditorUtilityLibrary",
                 "EditorLevelLibrary", "EditorAssetLibrary",
                 "KismetSystemLibrary", "KismetMathLibrary",
                 "GameplayStatics", "PythonBPLibrary"]:
    lib = getattr(unreal, lib_name, None)
    if lib:
        methods = [m for m in dir(lib) if not m.startswith("_")]
        print(f"  ✅ {lib_name}: {len(methods)} 个方法")
    else:
        print(f"  ❌ {lib_name}")

# 3. 检查 EditorLevelLibrary 的 Actor 操作
print("\n── EditorLevelLibrary Actor 相关方法 ──")
ell = getattr(unreal, "EditorLevelLibrary", None)
if ell:
    for m in dir(ell):
        if not m.startswith("_") and any(k in m.lower() for k in ["actor", "select", "spawn", "level"]):
            print(f"  {m}")

# 4. 检查 unreal.Actor 方法（是否有 input 相关）
print("\n── unreal.Actor input 相关 ──")
for m in dir(unreal.Actor):
    if not m.startswith("_") and any(k in m.lower() for k in ["input", "key", "bind"]):
        print(f"  {m}")

# 5. 关键：检查 get_editor_subsystem 是否可用
print("\n── EditorSubsystem ──")
try:
    sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    print(f"  ✅ UnrealEditorSubsystem: {sub}")
    for m in dir(sub):
        if not m.startswith("_"):
            print(f"    {m}")
except Exception as e:
    print(f"  ❌ {e}")

# 6. 检查 unreal.StaticMeshComponent 方法
print("\n── StaticMeshComponent 方法 ──")
for m in dir(unreal.StaticMeshComponent):
    if not m.startswith("_") and "mesh" in m.lower():
        print(f"  {m}")

print("\n===== 诊断第二轮完成 =====\n")
