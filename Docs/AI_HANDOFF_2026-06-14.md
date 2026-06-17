# MCPGameProject AI 工作交接文档

> 更新时间：2026-06-14  
> 项目目录：`C:\UE_Project\MCPGameProject`  
> Unreal Engine：UE 5.7  
> 当前主测试关卡：`/Game/TransformationVFX/SM2SM/SM2SM`

## 1. 必须遵守的用户规则

1. **每次主动关闭或重启 Unreal Editor 前，必须先执行 `save_all`。**
2. 必须确认返回同时满足：
   - `status = success`
   - `result.success = true`
3. 保存失败时禁止关闭或重启编辑器。
4. 当前工作区很脏，包含大量用户资产和其他功能改动。**禁止回滚、删除或覆盖与当前任务无关的改动。**
5. 不要在 PIE 运行期间调用 MCP `take_screenshot`，此前曾导致编辑器崩溃。
6. 用户要求保持原有 Game 视口构图、Pawn 相机和模型位置，不要擅自调整。

## 2. 当前编辑器和连接方式

- Unreal MCP 插件监听：`127.0.0.1:55557`
- 启动编辑器：

```powershell
powershell -ExecutionPolicy Bypass -File Scripts\start_ue.ps1
```

- 编译项目：

```powershell
& 'C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat' `
  MCPGameProjectEditor Win64 Development `
  'C:\UE_Project\MCPGameProject\MCPGameProject.uproject' `
  -WaitMutex -NoHotReloadFromIDE
```

- 当前编辑器已启动，测试关卡已打开，PIE 已停止，最后一次 `save_all` 已成功。

桌面会话没有原生 Unreal MCP 工具时，可通过 Node REPL 连接：

```js
var net = await import('node:net');
var sendUE = (type, params={}) => new Promise((resolve,reject)=>{
  const s = net.createConnection(
    {host:'127.0.0.1', port:55557},
    () => s.write(JSON.stringify({type, params}))
  );
  let d = '';
  s.on('data', c => {
    d += c.toString();
    try {
      const o = JSON.parse(d);
      s.destroy();
      resolve(o);
    } catch {}
  });
  s.on('error', reject);
});
```

常用命令：

```js
await sendUE('open_level', {path:'/Game/TransformationVFX/SM2SM/SM2SM'});
await sendUE('execute_python_file', {path:'C:/UE_Project/MCPGameProject/Scripts/start_pie.py'});
await sendUE('save_all', {});
```

## 3. 当前重点功能：BP_Burst_SM_Test

### 用户最终需求

- 使用按键 `1 / 2 / 3` 在三个模型间任意切换。
- 去掉 UI 和玩家碰撞触发逻辑。
- 初始状态不播放粒子。
- 按键切换时播放吸入/爆发粒子。
- 粒子不能直接受重力坠落，需保留原来的力场运动状态。
- 粒子动画结束时自然淡出，不能立即消失。
- 粒子淡出完成后，新模型从不可见开始淡入，不能先完整出现、再消失、再弹出。
- 模型淡入持续 `2.0` 秒。
- 三个新模型都使用略有色差的玉石材质。

### 核心资产

- 蓝图：`/Game/TransformationVFX/BP/Examples/BP_Burst_SM`
- 关卡实例标签：`BP_Burst_SM_Test`
- Niagara：`/Game/TransformationVFX/Niagara/NS_Inhalation_SM`
- 粒子材质：`/Game/TransformationVFX/Material/CharactorMaterial/MI_Manny_Particle`

三个状态模型：

| 状态 | 来源 Actor | Static Mesh |
|---|---|---|
| 1 | `YF` | `/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65` |
| 2 | `TYS` | `/Game/TransformationVFX/SM2SM/jude/20260613123723_f8ed59ab` |
| 3 | `YZL` | `/Game/TransformationVFX/SM2SM/jude/20260613130638_a1276204` |

玉石淡入材质：

- 父材质：`/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeFade`
- YF：`/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YF`
- TYS：`/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_TYS`
- YZL：`/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_Burst_Jade_YZL`

父材质使用 `Dissolve Amount`：

- `0.0`：不可见
- `0.65`：完全显示
- 使用 Masked + Dither Temporal AA + Subsurface。

### 核心代码

- `Source/MCPGameProject/BurstMeshStateSwitcherComponent.h`
- `Source/MCPGameProject/BurstMeshStateSwitcherComponent.cpp`

当前逻辑顺序：

1. 按下 `1 / 2 / 3`。
2. 当前模型快速隐藏，Niagara 开始运行。
3. 粒子运行 `FrontHalfDuration`，当前配置为 `2.5s`。
4. 粒子开始淡出，当前配置为 `2.0s`。
5. 粒子淡出完成后，目标模型才设置为可见。
6. 目标模型以 `Dissolve Amount 0.0 -> 0.65` 淡入，持续 `2.0s`。

重要修复：

- `ApplyInitialStateMaterials()` 在运行后的首个 Tick 强制恢复 `StateFadeMaterials`。
- 此修复解决了旧蓝图 BeginPlay 逻辑把状态 1 覆盖成椅子溶解材质的问题。
- 初始状态必须显示 YF 玉石材质，不能显示旧 `M_Chair_Dissolve`。

当前暴露参数位于 `Burst Switcher` 分类，包括：

- 模型淡入材质数组
- 粒子材质数组
- 粒子系统
- 粒子时长与淡出时长
- 模型淡入时长
- 粒子整体/非均匀缩放
- 粒子位置、旋转偏移
- 吸入扩散比例
- 吸引点位置
- Transformation Alpha 参数
- Dissolve 起止值

## 4. 本轮已验证完成的结果

2026-06-14 已重新构建、重启编辑器并在 PIE 中完成运行时验证。

构建结果：

```text
Result: Succeeded
```

初始状态：

```text
Static Mesh A Visible=True
Material=MI_Burst_Jade_YF
Static Mesh B/C Visible=False
```

状态 1 -> 2：

```text
switching from state 1 to state 2
beginning 2.00s particle fade out before target reveal
particle fade complete; beginning target model fade in
state 2 transition complete
Static Mesh B Visible=True
Material=MID_MI_Burst_Jade_TYS_0
Dissolve≈0.65
```

状态 2 -> 3：

```text
state 3 transition complete
Static Mesh C Visible=True
Material=MID_MI_Burst_Jade_YZL_0
Dissolve≈0.65
```

状态 3 -> 1：

```text
state 1 transition complete
Static Mesh A Visible=True
Material=MID_MI_Burst_Jade_YF_0
Dissolve≈0.65
```

因此目前 `1 / 2 / 3` 循环切换、粒子淡出、模型淡入和三个玉石材质均已通过运行时验证。

## 5. BP_Burst_SM_Test 配置和验证脚本

主要配置脚本：

- `Scripts/configure_burst_jade_states.py`
  - 创建玉石淡入父材质和三个材质实例。
  - 给关卡实例配置模型、材质与时序。
- `Scripts/configure_burst_jade_subobjects.py`
  - 使用 `SubobjectDataSubsystem` 写入真正的蓝图 SCS 模板。
  - 这是比只修改关卡实例更可靠的配置方式。
- `Scripts/configure_burst_reveal_timing.py`
  - 设置粒子淡出 `2.0s`、模型淡入 `2.0s`、Dissolve `0.0 -> 0.65`。
- `Scripts/restore_burst_inhalation_force_motion.py`
  - 恢复 `NS_Inhalation_SM` 和力场运动参数，避免粒子仅受重力掉落。

PIE 验证脚本：

- `Scripts/start_pie.py`
- `Scripts/stop_pie.py`
- `Scripts/trigger_burst_state_one.py`
- `Scripts/trigger_burst_state_two.py`
- `Scripts/trigger_burst_state_three.py`
- `Scripts/sample_burst_runtime_meshes.py`

推荐复测流程：

1. 打开 `/Game/TransformationVFX/SM2SM/SM2SM`。
2. 必要时运行 `configure_burst_jade_subobjects.py`。
3. 执行 `save_all`。
4. 启动 PIE。
5. 初始采样一次，确认 A 为 YF 玉石材质。
6. 依次触发状态 2、3、1，每次等待约 8 秒后采样。
7. 从 `Saved/Logs/MCPGameProject.log` 检查 `BurstMeshStateSwitcher` 和 `BurstMeshSample`。
8. 停止 PIE，再次执行 `save_all`。

## 6. 模型组件层级和编辑器可调要求

用户明确要求：

- `Static Mesh A / B / C` 都应是根物体的直接子物体。
- 三者应各自独立调整变换。
- 不允许 C 成为 A/B 的父物体。
- 自定义添加模型时，编辑器场景中需要能看到并手动调节。
- 运行时只显示当前状态，但编辑阶段不能因为逻辑隐藏而无法摆放模型。
- 不要自动缩放模型；模型比例由用户手动决定。

本轮主要验证的是运行时切换逻辑。下次若修改蓝图组件层级，必须先检查 SCS 层级，并重新验证 A/B/C 的相对变换和运行时显示状态。

## 7. 其他已开展功能

以下内容此前已修改，但本轮没有进行完整回归测试。继续修改前应先检查现状。

### 专业展厅灯光

- C++ Actor：
  - `Source/MCPGameProject/ExhibitionLightingRig.h`
  - `Source/MCPGameProject/ExhibitionLightingRig.cpp`
- 蓝图：
  - `/Game/TransformationVFX/SM2SM/BP_ExhibitionLightingRig_Professional`
- 关卡 Actor 标签：`ExhibitionLightingRig_Professional`
- 转换脚本：`Scripts/convert_exhibition_lighting_rig_to_blueprint.py`
- 用户要求使用 Pawn 相机，并保持原 Game 视口构图和模型位置。

### BG 网络 Shader

- 目标 Actor 标签：`BG`
- 父材质：`/Game/TransformationVFX/SM2SM/M_BG_Network`
- 材质实例：`/Game/TransformationVFX/SM2SM/MI_BG_Network`
- 创建脚本：`Scripts/create_bg_network_material.py`
- 透明设置脚本：`Scripts/configure_bg_transparent_rendering.py`
- 用户要求材质为无光照、自发光、带透明通道。
- 历史问题包括黑边、交叉点连成大片、线条轮廓不清晰。继续修改时必须实际查看效果，不能只确认材质编译成功。

### YZL 程序化玉石 SSS

- 资产目录：`/Game/TransformationVFX/SM2SM/jude`
- 创建脚本：`Scripts/create_yzl_procedural_jade_sss.py`
- 参数修复/测试脚本：
  - `restore_yzl_material_instance_values.py`
  - `restore_yzl_master_tint.py`
  - `restore_yzl_stain.py`
  - `set_yzl_requested_initial_values.py`
  - `test_yzl_*.py`
- 用户要求参考黄绿色古玉，温润、半透明、SSS、三平面映射，污渍参数必须真实生效。
- 历史问题：材质实例参数看似变化但场景模型无响应；Stain 无效果；曾出现不合理黑色斑点。
- Burst 切换当前使用的是独立的 `BurstJade` 淡入材质，不要误认为已完全复用上述 YZL 程序玉石主材质。

### BP_Upward_SM

- 代码：
  - `Source/MCPGameProject/UpwardMeshStateSwitcherComponent.h`
  - `Source/MCPGameProject/UpwardMeshStateSwitcherComponent.cpp`
- 此功能也经历过按键切换、粒子时序和模型淡入修改。
- 当前重点已转移到 `BP_Burst_SM_Test`，不要在没有用户要求时改动 Upward 系统。

## 8. 已知风险和注意事项

1. `Source/MCPGameProject/BurstMeshStateSwitcherComponent.cpp/.h` 当前在 Git 中显示为未跟踪文件，但已成功参与构建。不要删除。
2. `Content/TransformationVFX/` 整体也显示为未跟踪目录，包含当前核心资产。
3. 工作区还有大量插件、配置、其他关卡和系统改动，禁止执行：
   - `git reset --hard`
   - `git checkout -- .`
   - 对整个 Content 或 Source 的清理操作
4. 只修改关卡实例可能会在重载或运行时被蓝图模板覆盖。修改 `BP_Burst_SM` 时优先使用 `SubobjectDataSubsystem` 更新 SCS 模板。
5. 蓝图旧 BeginPlay 逻辑仍可能覆盖材质，因此 C++ 首 Tick 的 `ApplyInitialStateMaterials()` 不能随意删除。
6. Niagara 参数名可能同时存在带空格和不带空格版本，例如：
   - `User.Transformation Alpha`
   - `User.TransformationAlpha`
   - `User.Fade Opacity`
   - `User.FadeOpacity`
7. 模型淡入材质必须支持 `Dissolve Amount`。若没有淡入材质，当前逻辑会保持目标隐藏，以防止完整模型突然弹出。

## 9. 建议的下一步

1. 让用户实际试玩 `BP_Burst_SM_Test`，根据视觉反馈微调：
   - `FrontHalfDuration`
   - `ParticleFadeOutDuration`
   - `ModelFadeInDuration`
   - `ParticleEffectScale`
   - `InhalationSpreadScale`
2. 若用户要求更真实玉石质感，把 `BurstJade` 淡入能力合并进程序化 YZL 玉石主材质，而不是牺牲当前可靠的淡入逻辑。
3. 检查并确认 `Static Mesh A/B/C` 在蓝图 SCS 中均为根节点直接子组件。
4. 对 BG 网络材质做视觉回归测试，重点检查黑边和交叉点过曝。
5. 在任何重启前严格执行并确认 `save_all`。

## 10. 接手时快速检查清单

- [ ] 阅读本文档，确认不回滚用户改动。
- [ ] 检查 Unreal Editor 是否运行、55557 是否可连接。
- [ ] 确认当前关卡是 `/Game/TransformationVFX/SM2SM/SM2SM`。
- [ ] 检查 `BP_Burst_SM_Test` 初始状态无粒子且显示 YF。
- [ ] 按 `2`、`3`、`1` 检查粒子淡出后模型淡入。
- [ ] 检查日志中没有旧 Chair/Table 材质覆盖。
- [ ] 修改前先确认用户当前目标，避免同时动 BG、灯光、玉石和 Burst 多套系统。
- [ ] 关闭或重启编辑器前执行并确认 `save_all`。
