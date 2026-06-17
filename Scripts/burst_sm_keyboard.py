"""
burst_sm_keyboard.py — 最终版
================================
在场景的 BP_Burst_SM_C_1 Actor 上直接挂载 Python Tick 轮询，
按 1/2/3 切换三个 StaticMesh，无需修改蓝图节点。

exec(open(r"C:/UE_Project/MCPGameProject/Scripts/burst_sm_keyboard.py").read())
"""
import unreal

# ── 配置 ──────────────────────────────────────────────────────
MESH_PATHS = [
    "/Game/TransformationVFX/Demo/StaticMesh/SM_Chair",       # 键 1
    "/Game/TransformationVFX/Demo/StaticMesh/SM_TableRound",  # 键 2
    "/Engine/BasicShapes/Cube",                                # 键 3
]
# 场景里的 Actor 名（诊断已确认）
ACTOR_NAME = "BP_Burst_SM_C_1"
# 切换哪个 StaticMeshComponent（诊断显示有两个：A 和 B，切 A）
COMP_NAME  = "Static Mesh A"

# ── 预加载 Mesh ───────────────────────────────────────────────
meshes = []
for p in MESH_PATHS:
    m = unreal.load_asset(p)
    assert m is not None, f"Mesh 加载失败: {p}"
    meshes.append(m)
    print(f"✅ Mesh: {m.get_name()}")

# ── 构造 Key 对象 ─────────────────────────────────────────────
def make_key(name: str):
    """构造 unreal.Key，兼容 UE5.7 不能传参的问题"""
    k = unreal.Key()
    try:
        k.set_editor_property("key_name", name)
    except Exception:
        pass
    return k

KEY_ONE   = make_key("One")
KEY_TWO   = make_key("Two")
KEY_THREE = make_key("Three")

# ── 找到场景 Actor ────────────────────────────────────────────
ell    = unreal.EditorLevelLibrary
actors = ell.get_all_level_actors()
target = next((a for a in actors if a.get_name() == ACTOR_NAME), None)

if target is None:
    # 宽松匹配
    target = next((a for a in actors if "Burst_SM" in a.get_name()), None)

assert target is not None, f"找不到 Actor: {ACTOR_NAME}"
print(f"✅ 找到 Actor: {target.get_name()}")

# 找 StaticMeshComponent
sm_comp = None
for c in target.get_components_by_class(unreal.StaticMeshComponent):
    if c.get_name() == COMP_NAME:
        sm_comp = c
        break
if sm_comp is None:
    # 取第一个
    comps = target.get_components_by_class(unreal.StaticMeshComponent)
    assert comps, "Actor 上没有 StaticMeshComponent"
    sm_comp = comps[0]

print(f"✅ 使用 StaticMeshComponent: {sm_comp.get_name()}")

# ── 定义 Python Tick Actor（附加到场景）────────────────────────
@unreal.uclass()
class KeyboardMeshSwitcher(unreal.Actor):
    """监听 1/2/3 键，切换目标 Actor 的 StaticMesh"""

    def __init__(self):
        super().__init__()
        self._index   = 0          # 当前 mesh 索引
        self._prev    = [False]*3  # 上一帧按键状态（边缘检测）
        self._sm_comp = None
        self._meshes  = []

    @unreal.ufunction(override=True)
    def receive_begin_play(self):
        super().receive_begin_play()
        self._meshes  = meshes
        self._sm_comp = sm_comp

        # 启用输入
        world = self.get_world()
        if world:
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            if pc:
                self.enable_input(pc)
        print("[KeyboardMeshSwitcher] BeginPlay OK")

    @unreal.ufunction(override=True)
    def receive_tick(self, delta_seconds: float):
        super().receive_tick(delta_seconds)
        world = self.get_world()
        if not world:
            return
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        if not pc:
            return

        keys = [KEY_ONE, KEY_TWO, KEY_THREE]
        for i, k in enumerate(keys):
            try:
                down = pc.was_input_key_just_pressed(k)
            except Exception:
                down = False

            if down and self._index != i:
                self._index = i
                if self._sm_comp and self._meshes:
                    self._sm_comp.set_static_mesh(self._meshes[i])
                    print(f"[KeyMeshSwitcher] 键{i+1} → {self._meshes[i].get_name()}")


# ── 在场景中生成 KeyboardMeshSwitcher ────────────────────────
world = unreal.EditorLevelLibrary.get_editor_world()

# 先删除旧的（避免重复运行堆积）
for a in ell.get_all_level_actors():
    if a.get_class().get_name() == "KeyboardMeshSwitcher_C":
        ell.destroy_actor(a)
        print("🗑️  删除旧 KeyboardMeshSwitcher")

loc = unreal.Vector(0, 0, -10000)   # 放到场景外，不可见
new_actor = ell.spawn_actor_from_class(KeyboardMeshSwitcher, loc)
assert new_actor is not None, "生成 KeyboardMeshSwitcher 失败"
print(f"✅ 已生成 KeyboardMeshSwitcher: {new_actor.get_name()}")

print("""
╔═══════════════════════════════════════╗
║  ✅ 完成！运行 PIE (Play) 后：        ║
║  按 1 → SM_Chair                     ║
║  按 2 → SM_TableRound                ║
║  按 3 → Cube                         ║
╚═══════════════════════════════════════╝
""")
