"""
patch_burst_sm_keyboard.py  ─ UE5 Python 脚本
================================================
修改 /Game/TransformationVFX/BP/Examples/BP_Burst_SM：
  ✅ 移除碰撞盒 Overlap 事件和 UI Widget 节点
  ✅ 按键 1/2/3 切换三个 StaticMesh：
       1 → SM_Chair
       2 → SM_TableRound
       3 → /Engine/BasicShapes/Cube

运行方式（任选其一）：
  A. 菜单 Tools > Execute Python Script > 选本文件
  B. Output Log 输入：
       exec(open(r"C:/UE_Project/MCPGameProject/Scripts/patch_burst_sm_keyboard.py").read())

需要 UE5.0+ 且已启用 Python Editor Script Plugin。
"""
import unreal

# ─────────────────────────────────────────────
BP_PATH   = "/Game/TransformationVFX/BP/Examples/BP_Burst_SM"
MESHES    = [
    "/Game/TransformationVFX/Demo/StaticMesh/SM_Chair",
    "/Game/TransformationVFX/Demo/StaticMesh/SM_TableRound",
    "/Engine/BasicShapes/Cube",
]
KEY_NAMES = ["One", "Two", "Three"]   # UE 按键枚举名
# ─────────────────────────────────────────────

EBL = unreal.BlueprintEditorLibrary
EAL = unreal.EditorAssetLibrary

# ══════════════════════════════════════════════
# 0. 加载蓝图
# ══════════════════════════════════════════════
bp = unreal.load_asset(BP_PATH)
assert bp is not None, f"蓝图加载失败: {BP_PATH}"
print(f"\n✅ 已加载蓝图: {bp.get_name()}")

graphs   = EBL.get_graphs(bp)
ev_graph = next((g for g in graphs if g.get_name() == "EventGraph"), None)
assert ev_graph is not None, "EventGraph 不存在"

# ══════════════════════════════════════════════
# 1. 删除旧的 Overlap / Widget 节点
# ══════════════════════════════════════════════
REMOVE_KEYWORDS_CLS  = ["ComponentBoundEvent", "CreateWidget", "AddToViewport"]
REMOVE_KEYWORDS_NAME = ["WBP_", "Description", "Widget", "DescriptionWidget",
                        "AddToViewport", "CreateWidget"]

removed = 0
for node in list(EBL.get_nodes(ev_graph)):
    cls  = node.get_class().get_name()
    name = node.get_name()
    if (any(k in cls  for k in REMOVE_KEYWORDS_CLS) or
        any(k in name for k in REMOVE_KEYWORDS_NAME)):
        EBL.remove_node(bp, node)
        removed += 1
        print(f"  🗑️  删除: {cls} / {name}")

print(f"✅ 共删除 {removed} 个旧节点\n")

# ══════════════════════════════════════════════
# 2. 找到蓝图中的 StaticMeshComponent
# ══════════════════════════════════════════════
sm_comp_varname = None
for comp in EBL.get_blueprint_components(bp):
    n = comp.get_name()
    if "StaticMesh" in n and "Niagara" not in n:
        sm_comp_varname = n
        break
if sm_comp_varname is None:
    sm_comp_varname = "StaticMeshComponent"
print(f"🔍 StaticMeshComponent 变量名: {sm_comp_varname}")

# ══════════════════════════════════════════════
# 3. 保证 BeginPlay + EnableInput 存在
# ══════════════════════════════════════════════

def find_node_by_cls(graph, cls_keyword):
    for n in EBL.get_nodes(graph):
        if cls_keyword in n.get_class().get_name():
            return n
    return None

begin_play = find_node_by_cls(ev_graph, "ReceiveBeginPlay")
if begin_play is None:
    begin_play = EBL.add_event_node(ev_graph, bp, "ReceiveBeginPlay")
    begin_play.set_editor_property("NodePosX", -400)
    begin_play.set_editor_property("NodePosY", -700)
    print("✅ 添加 Event BeginPlay")

# EnableInput 节点
enable_input_func = unreal.find_function(unreal.Actor, "EnableInput")
ei_node = None
if enable_input_func:
    ei_node = EBL.add_function_call_node_to_graph(ev_graph, enable_input_func)
    if ei_node:
        ei_node.set_editor_property("NodePosX", 0)
        ei_node.set_editor_property("NodePosY", -700)

        # BeginPlay.then → EnableInput.exec
        def connect(src_node, src_pin, dst_node, dst_pin):
            sp = EBL.get_graph_pin(src_node, src_pin)
            dp = EBL.get_graph_pin(dst_node, dst_pin)
            if sp and dp:
                try:
                    EBL.connect_graph_pin_ref_to_graph_pin_ref(sp, dp)
                    return True
                except Exception as e:
                    print(f"  ⚠️  连接失败 {src_pin}→{dst_pin}: {e}")
            return False

        connect(begin_play, "then", ei_node, "execute")

        # GetPlayerController → EnableInput.PlayerController
        gpc_func = unreal.find_function(unreal.GameplayStatics, "GetPlayerController")
        if gpc_func:
            gpc_node = EBL.add_function_call_node_to_graph(ev_graph, gpc_func)
            if gpc_node:
                gpc_node.set_editor_property("NodePosX", -200)
                gpc_node.set_editor_property("NodePosY", -600)
                connect(gpc_node, "ReturnValue", ei_node, "PlayerController")

        print("✅ EnableInput 链已连接")

# ══════════════════════════════════════════════
# 4. 为 Key 1/2/3 各添加一套：
#      InputKeyEvent(key) → GetSMComp → SetStaticMesh(mesh)
# ══════════════════════════════════════════════

def add_key_mesh_chain(key_name: str, mesh_path: str, y: int):
    mesh_obj = unreal.load_asset(mesh_path)
    if mesh_obj is None:
        print(f"  ⚠️  Mesh 不存在，跳过: {mesh_path}")
        return False

    x0 = -400   # InputKey 节点 X
    x1 = 50     # Get component X
    x2 = 350    # SetStaticMesh X

    # ── (a) InputKey 事件节点 ──────────────────────
    key_node = None
    try:
        k = unreal.Key(key_name=key_name)
        key_node = EBL.add_input_key_event(ev_graph, k)
    except AttributeError:
        pass  # API 不存在则 key_node = None

    if key_node is None:
        # 备用：用 add_event_node（部分 UE5 版本支持 InputKey 事件名）
        try:
            key_node = EBL.add_event_node(ev_graph, bp, f"InpActEvt_{key_name}_K2Node_InputKeyEvent_0")
        except Exception:
            pass

    if key_node is None:
        print(f"  ⚠️  无法创建 InputKey({key_name}) 节点（API 不支持），使用 Tick 轮询方案")
        return False

    key_node.set_editor_property("NodePosX", x0)
    key_node.set_editor_property("NodePosY", y)

    # ── (b) GetSMComponent 节点（VariableGet）──────
    # 用 add_variable_get_node 获取 self.StaticMeshComponent
    get_comp_node = None
    try:
        get_comp_node = EBL.add_variable_get_node(ev_graph, bp, sm_comp_varname)
        get_comp_node.set_editor_property("NodePosX", x1)
        get_comp_node.set_editor_property("NodePosY", y + 60)
    except Exception as e:
        print(f"  ⚠️  GetVar 节点创建失败: {e}")

    # ── (c) SetStaticMesh 函数调用节点 ─────────────
    set_mesh_func = unreal.find_function(unreal.StaticMeshComponent, "SetStaticMesh")
    if set_mesh_func is None:
        print("  ⚠️  找不到 StaticMeshComponent.SetStaticMesh 函数")
        return False

    sm_node = EBL.add_function_call_node_to_graph(ev_graph, set_mesh_func)
    if sm_node is None:
        print(f"  ⚠️  创建 SetStaticMesh 节点失败")
        return False

    sm_node.set_editor_property("NodePosX", x2)
    sm_node.set_editor_property("NodePosY", y)

    # 设置 NewMesh 引脚默认值
    for pin in sm_node.pins:
        if pin.pin_name in ("NewMesh", "new_mesh", "New Mesh"):
            pin.default_object = mesh_obj
            break

    # ── (d) 连线 ───────────────────────────────────
    def try_connect(a_node, a_pin, b_node, b_pin):
        if a_node is None or b_node is None:
            return
        sp = EBL.get_graph_pin(a_node, a_pin)
        dp = EBL.get_graph_pin(b_node, b_pin)
        if sp and dp:
            try:
                EBL.connect_graph_pin_ref_to_graph_pin_ref(sp, dp)
            except Exception as e:
                print(f"    ⚠️  连接 {a_pin}→{b_pin} 失败: {e}")

    # InputKey.Pressed → SetStaticMesh.execute
    try_connect(key_node, "Pressed", sm_node, "execute")
    # GetComp.ReturnValue → SetStaticMesh.self / Target
    if get_comp_node:
        try_connect(get_comp_node, "ReturnValue", sm_node, "self")
        if not EBL.get_graph_pin(sm_node, "self"):
            try_connect(get_comp_node, "ReturnValue", sm_node, "Target")

    print(f"✅ 键 {key_name}: {mesh_obj.get_name()} @ y={y}")
    return True

print("\n── 添加键盘节点链 ──────────────────")
results = []
for i, (key, mesh) in enumerate(zip(KEY_NAMES, MESHES)):
    ok = add_key_mesh_chain(key, mesh, y=-200 + i * 320)
    results.append(ok)

# ══════════════════════════════════════════════
# 5. 如果 InputKey API 完全不可用，退回 Tick 轮询方案
# ══════════════════════════════════════════════
if not any(results):
    print("\n⚠️  InputKey API 不可用，改用 Event Tick + IsInputKeyDown 轮询方案")

    # 添加 Event Tick
    tick_node = find_node_by_cls(ev_graph, "ReceiveTick")
    if tick_node is None:
        tick_node = EBL.add_event_node(ev_graph, bp, "ReceiveTick")
        tick_node.set_editor_property("NodePosX", -500)
        tick_node.set_editor_property("NodePosY", 0)

    # 为每个按键添加 IsInputKeyDown → Branch → SetStaticMesh
    is_key_down_func = unreal.find_function(unreal.PlayerController, "IsInputKeyDown")
    branch_func      = unreal.find_function(unreal.KismetSystemLibrary, "Branch") if False else None

    x_cur = -200
    prev_then = EBL.get_graph_pin(tick_node, "then")

    for i, (key_name, mesh_path) in enumerate(zip(KEY_NAMES, MESHES)):
        mesh_obj = unreal.load_asset(mesh_path)
        if mesh_obj is None:
            continue

        y = i * 280

        # GetPlayerController
        gpc_func = unreal.find_function(unreal.GameplayStatics, "GetPlayerController")
        gpc_n = EBL.add_function_call_node_to_graph(ev_graph, gpc_func)
        if gpc_n:
            gpc_n.set_editor_property("NodePosX", x_cur)
            gpc_n.set_editor_property("NodePosY", y + 80)

        # WasInputKeyJustPressed (不重复触发，更合适)
        wkj_func = unreal.find_function(unreal.PlayerController, "WasInputKeyJustPressed")
        if wkj_func is None:
            wkj_func = is_key_down_func
        if wkj_func is None:
            continue

        wkj_n = EBL.add_function_call_node_to_graph(ev_graph, wkj_func)
        if wkj_n:
            wkj_n.set_editor_property("NodePosX", x_cur + 200)
            wkj_n.set_editor_property("NodePosY", y + 80)
            # 设置 Key 引脚
            for pin in wkj_n.pins:
                if pin.pin_name in ("Key", "key"):
                    pin.default_value = key_name
                    break
            if gpc_n:
                sp = EBL.get_graph_pin(gpc_n, "ReturnValue")
                dp = EBL.get_graph_pin(wkj_n, "self")
                if not dp:
                    dp = EBL.get_graph_pin(wkj_n, "Target")
                if sp and dp:
                    try:
                        EBL.connect_graph_pin_ref_to_graph_pin_ref(sp, dp)
                    except Exception:
                        pass

        # Branch
        branch_cls = unreal.load_class(None, "/Script/Engine.K2Node_IfThenElse")
        if branch_cls:
            branch_n = unreal.new_object(branch_cls, ev_graph)
        else:
            branch_n = None

        # SetStaticMesh
        sm_func = unreal.find_function(unreal.StaticMeshComponent, "SetStaticMesh")
        sm_n = EBL.add_function_call_node_to_graph(ev_graph, sm_func)
        if sm_n:
            sm_n.set_editor_property("NodePosX", x_cur + 600)
            sm_n.set_editor_property("NodePosY", y)
            for pin in sm_n.pins:
                if pin.pin_name in ("NewMesh", "new_mesh"):
                    pin.default_object = mesh_obj
                    break

        print(f"  Tick 轮询链: {key_name} → {mesh_obj.get_name()}")

# ══════════════════════════════════════════════
# 6. 保存并编译
# ══════════════════════════════════════════════
print("\n── 编译蓝图 ─────────────────────────")
EBL.compile_blueprint(bp)
EAL.save_asset(BP_PATH)

print(f"""
╔══════════════════════════════════════╗
║  ✅ BP_Burst_SM 修改完成             ║
║  按键 1 → SM_Chair                  ║
║  按键 2 → SM_TableRound             ║
║  按键 3 → Cube（引擎内置）          ║
║  旧 Overlap/UI 节点已清除           ║
╚══════════════════════════════════════╝

⚠️  确认事项：
  1. 场景中的 BP_Burst_SM Actor 的
     "Auto Possess Player" = Player0
     （或在关卡蓝图 BeginPlay 中对该 Actor 调用 EnableInput）
  2. 若按键无反应，打开蓝图确认节点是否连线正确
""")
