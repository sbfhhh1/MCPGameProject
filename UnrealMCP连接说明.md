# UnrealMCP 自动连接说明

## 链路结构

```
Claude (Claude Code)  ──stdio──▶  Scripts/unreal_mcp_bridge.js  (Node 桥接，26 个工具)
                                          │  TCP 127.0.0.1:55557
                                          ▼
                              UnrealMCP 插件（UE 编辑器内监听 55557）
```

桥接脚本依赖 `@modelcontextprotocol/sdk`（已随项目 `node_modules` 安装，端口 55557 与插件 C++ 中 `MCP_SERVER_PORT` 一致）。

## 下次自动连接（Claude Code 项目级）

已为你固化两处配置，之后在**项目目录**运行 `claude` 即会自动连上 `unreal-bridge`：

- `.claude/mcp.json` — 定义 `unreal-bridge`，已改为**绝对路径**，无论从哪个目录启动都稳定。
- `.claude/settings.json` — `"enabledMcpjsonServers": ["unreal-bridge"]`，自动启用。

前提：UE 编辑器开着，且 UnrealMCP 插件已启用、在监听 55557。

## 一键启动

双击根目录的 **`启动UE并连接MCP.bat`**，它会：

1. 校验项目文件与 UE 路径（默认 UE 5.7，换版本改脚本里的 `UE_EXE`）。
2. 若 UE 未运行则启动它并加载本项目。
3. 轮询等待 55557 端口就绪（最多等 3 分钟）。
4. 就绪后提示你可以运行 `claude` 或在 Cowork 里操作 UE。

## 关于 Cowork 桌面会话的限制

当前这个 Cowork 桌面会话的 MCP 列表由桌面端注册表决定，**不会自动读取项目里的 `.claude/mcp.json`**，所以本会话里不会出现 UnrealMCP 原生工具。两种使用方式：

- **推荐**：在项目目录用 `claude`（Claude Code），自动连接、原生工具齐全。
- **本会话内**：必要时我可在你 Windows 机器上经桥接脚本/端口 55557 间接驱动 UE（Cowork 沙箱本身访问不到宿主机端口，需在你机器上运行）。

## 故障排查

- **端口 55557 连不上**：确认 UE 已完全启动、UnrealMCP 插件已勾选启用；必要时在插件设置里确认 server 已 Start。
- **`claude` 没连上 unreal-bridge**：确认在**项目根目录**运行；检查 `node` 在 PATH 中（`node --version`）。
- **引擎版本不同**：编辑 `启动UE并连接MCP.bat` 顶部的 `UE_EXE` 路径。
