# GradientBox 运行时控制面板 - Blueprint 创建指南

## 创建步骤

### 1. 创建 WBP_GNControlPanel Blueprint Widget

在 UE5 Editor 中:
1. 右键 → User Interface → Widget Blueprint
2. 命名为 `WBP_GNControlPanel`
3. 保存到 `Content/Blueprints/`

### 2. 面板结构设计

```
Canvas Panel (根)
└── Vertical Box (主容器, 100% 宽度)
    ├── Header (水平盒子)
    │   ├── Icon (Text: 🎯)
    │   └── Title (Text: "GradientBox 动画控制")
    ├── Divider (Separator)
    │
    ├── CollapsibleSection: 呼吸动画
    │   ├── Row: 幅度
    │   │   ├── Label (Text: "幅度")
    │   │   ├── Slider (Min:0, Max:1, Step:0.01)
    │   │   └── ValueText (绑定 GradientBoxMotion.Amplitude)
    │   ├── Row: 速度
    │   │   ├── Label (Text: "速度")
    │   │   ├── Slider (Min:0, Max:4, Step:0.05)
    │   │   └── ValueText (绑定 GradientBoxMotion.Speed)
    │   └── Row: 平滑度
    │       ├── Label (Text: "平滑度")
    │       ├── Slider (Min:0, Max:1, Step:0.01)
    │       └── ValueText (绑定 GradientBoxMotion.Smoothness)
    │
    ├── CollapsibleSection: 性能设置
    │   ├── Row: 最大FPS
    │   │   ├── Label (Text: "FPS")
    │   │   ├── Slider (Min:1, Max:120, Step:1)
    │   │   └── ValueText
    │   ├── Checkbox: 快速动态网格
    │   └── Checkbox: 重算法线
    │
    └── CollapsibleSection: 材质同步
        ├── Row: 相位差指示 (蓝/粉 图标)
        └── Checkbox: 启用反向动画
            └── 绑定 RuntimePanel.SetGradientBoxReversePink
```

### 3. 控件属性绑定

| 控件 | 属性路径 | 更新方式 |
|------|----------|----------|
| Amplitude Slider | GradientBoxMotion → Amplitude | OnValueChanged → SetGradientBoxAmplitude |
| Speed Slider | GradientBoxMotion → Speed | OnValueChanged → SetGradientBoxSpeed |
| Smoothness Slider | GradientBoxMotion → Smoothness | OnValueChanged → SetGradientBoxSmoothness |
| FPS Slider | GradientBoxMotion → MaxAnimationFrameRate | OnValueChanged → UpdateTickRate |
| FastMesh Checkbox | GradientBoxMotion → bUseFastDynamicMesh | OnCheckStateChanged → SetGradientBoxUseFastMesh |
| Normals Checkbox | GradientBoxMotion → bRecalculateAnimatedNormals | OnCheckStateChanged → SetGradientBoxRecalcNormals |
| Reverse Checkbox | RuntimePanel → SetGradientBoxReversePink | OnCheckStateChanged |

### 4. 样式设置 (在 Designer 中)

**面板背景**:
- Brush: 纯色
- Color And Opacity: `(0.08, 0.08, 0.12, 0.95)` (深蓝灰)
- Margin: 10px
- Padding: 15px

**标题样式**:
- Font Size: 18
- Font: Bold
- Color: `#E0E0E0` (浅灰)

**滑块样式**:
- Track Color: `(0.25, 0.25, 0.35)` (暗灰)
- Fill Color: Linear Gradient (蓝→粉: `#4169E1` → `#FF69B4`)
- Thumb Color: `#FFFFFF`

**标签样式**:
- Font Size: 13
- Color: `#B0B0B0`

### 5. 交互逻辑 (Event Graph)

```blueprint
Event Construct:
    → Get Owner Actor
    → Get Component by Class (BlenderGNGradientBoxMotionComponent)
    → 存储到变量 GradientBoxMotion
    → Get Component by Class (BlenderGNRuntimePanelWidget)
    → 存储到变量 RuntimePanel

On Amplitude Slider Changed (float Value):
    → SetGradientBoxAmplitude(Value)
    → 更新 ValueText 显示: FMath::RoundToFloat(Value * 100) / 100

On Speed Slider Changed (float Value):
    → SetGradientBoxSpeed(Value)
    → 更新 ValueText 显示: FMath::RoundToFloat(Value * 100) / 100

... 其他滑块同理 ...

On Reverse Checkbox Changed (bool bIsChecked):
    → SetGradientBoxReversePink(bIsChecked)
```

### 6. 使用方法

在 Level Blueprint 或 GameMode 中:

```blueprint
Event BeginPlay:
    → Create Widget (WBP_GNControlPanel)
    → Add to Viewport
    → 可选: 设置锚点居中或角落
```

### 7. 快捷键支持 (可选)

添加键盘快捷键:
- `1-4`: 切换展开/折叠各区域
- `R`: 重置所有值为默认
- `H`: 隐藏/显示面板

## 快速验证清单

- [ ] 滑块拖动时动画实时响应
- [ ] 数值显示正确更新
- [ ] 粉色和蓝色动画方向正确
- [ ] FPS 滑块影响动画流畅度
- [ ] 快速网格开关有效
- [ ] 面板样式美观协调