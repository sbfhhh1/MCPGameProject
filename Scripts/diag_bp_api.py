"""
诊断脚本：检查 UE5.7 Python API 可用性
在 Output Log Python 控制台运行：
    exec(open(r"C:/UE_Project/MCPGameProject/Scripts/diag_bp_api.py").read())
"""
import unreal

print("\n===== UE Python API 诊断 =====")
print(f"unreal 模块: {unreal}")

# 1. BlueprintEditorLibrary 是否存在
try:
    bel = unreal.BlueprintEditorLibrary
    print(f"✅ BlueprintEditorLibrary: {bel}")
except AttributeError as e:
    print(f"❌ BlueprintEditorLibrary 不存在: {e}")
    bel = None

# 2. 检查关键方法
if bel:
    methods = [
        "get_graphs", "get_nodes", "remove_node",
        "add_event_node", "add_function_call_node_to_graph",
        "add_input_key_event", "get_graph_pin",
        "connect_graph_pin_ref_to_graph_pin_ref",
        "get_blueprint_components", "compile_blueprint",
        "get_blueprint_variables", "add_variable_get_node",
    ]
    for m in methods:
        has = hasattr(bel, m)
        print(f"  {'✅' if has else '❌'} BlueprintEditorLibrary.{m}")

# 3. 加载蓝图
BP_PATH = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
try:
    bp = unreal.load_asset(BP_PATH)
    print(f"\n✅ 蓝图加载成功: {bp.get_name()}" if bp else f"❌ 蓝图加载失败: {BP_PATH}")
except Exception as e:
    print(f"❌ load_asset 异常: {e}")
    bp = None

# 4. 列出 EventGraph 节点
if bp and bel and hasattr(bel, "get_graphs"):
    try:
        graphs = bel.get_graphs(bp)
        print(f"\n📋 图列表: {[g.get_name() for g in graphs]}")
        eg = next((g for g in graphs if g.get_name() == "EventGraph"), None)
        if eg:
            nodes = bel.get_nodes(eg)
            print(f"📋 EventGraph 节点数: {len(nodes)}")
            for n in nodes:
                print(f"   - [{n.get_class().get_name()}] {n.get_name()}")
    except Exception as e:
        print(f"❌ 枚举节点失败: {e}")

# 5. 检查 Key API
print("\n── Key API ──")
try:
    k = unreal.Key(key_name="One")
    print(f"✅ unreal.Key(key_name='One'): {k}")
except Exception as e:
    print(f"❌ unreal.Key: {e}")

# 6. 检查 find_function
print("\n── find_function ──")
for cls, fn in [
    (unreal.StaticMeshComponent, "SetStaticMesh"),
    (unreal.Actor, "EnableInput"),
    (unreal.GameplayStatics, "GetPlayerController"),
]:
    try:
        f = unreal.find_function(cls, fn)
        print(f"  {'✅' if f else '❌'} {cls.__name__}.{fn}: {f}")
    except Exception as e:
        print(f"  ❌ {cls.__name__}.{fn}: {e}")

print("\n===== 诊断完成 =====\n")
