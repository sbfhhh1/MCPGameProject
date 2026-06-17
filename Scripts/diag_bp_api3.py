"""
诊断第三轮：确认 find_event_graph 返回内容 + GameplayStatics 可用方法
exec(open(r"C:/UE_Project/MCPGameProject/Scripts/diag_bp_api3.py").read())
"""
import unreal

BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
bp = unreal.load_asset(BP_PATH)

# 1. find_event_graph 返回什么
print("\n── find_event_graph ──")
try:
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    print(f"  返回: {eg}")
    if eg:
        print(f"  类型: {eg.get_class().get_name()}")
        print(f"  名称: {eg.get_name()}")
        for m in dir(eg):
            if not m.startswith("_"):
                print(f"    {m}")
except Exception as e:
    print(f"  ❌ {e}")

# 2. GameplayStatics input 相关方法
print("\n── GameplayStatics 按键相关 ──")
gs = unreal.GameplayStatics
for m in dir(gs):
    if not m.startswith("_") and any(k in m.lower() for k in ["input","key","press","player"]):
        print(f"  {m}")

# 3. PlayerController 可用方法
print("\n── PlayerController input 方法 ──")
for m in dir(unreal.PlayerController):
    if not m.startswith("_") and any(k in m.lower() for k in ["input","key","press","was","is_"]):
        print(f"  {m}")

# 4. 检查场景里是否有 BP_Burst_SM Actor
print("\n── 场景中的 BP_Burst_SM Actor ──")
try:
    ell = unreal.EditorLevelLibrary
    actors = ell.get_all_level_actors()
    for a in actors:
        cls_name = a.get_class().get_name()
        if "Burst" in cls_name or "Burst" in a.get_name():
            print(f"  ✅ {a.get_name()} [{cls_name}]")
            # 列出组件
            comps = a.get_components_by_class(unreal.StaticMeshComponent)
            for c in comps:
                print(f"    StaticMeshComp: {c.get_name()} mesh={c.static_mesh}")
except Exception as e:
    print(f"  ❌ {e}")

# 5. 检查 unreal.uclass 装饰器是否可用
print("\n── Python Actor 扩展 API ──")
for attr in ["uclass", "ufunction", "uproperty", "uactor"]:
    print(f"  {'✅' if hasattr(unreal, attr) else '❌'} unreal.{attr}")

# 6. 检查 EditorLevelLibrary.replace_mesh_components_meshes_on_actors 签名
print("\n── replace_mesh_components_meshes_on_actors 参数 ──")
try:
    help_txt = str(unreal.EditorLevelLibrary.replace_mesh_components_meshes_on_actors.__doc__)
    print(f"  {help_txt[:300]}")
except:
    pass

print("\n===== 诊断第三轮完成 =====\n")
