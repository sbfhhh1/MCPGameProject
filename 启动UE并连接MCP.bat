@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title UnrealMCP 一键启动

REM ============================================================
REM   UnrealMCP 一键启动脚本
REM   作用：启动 UE 编辑器（带本项目）→ 等待 MCP 插件监听 55557
REM        → 之后即可在本项目目录运行 `claude` 自动连接 unreal-bridge
REM ============================================================

set "PROJECT_DIR=C:\UE_Project\MCPGameProject"
set "UPROJECT=%PROJECT_DIR%\MCPGameProject.uproject"
set "UE_EXE=C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
set "MCP_PORT=55557"

echo ============================================================
echo   UnrealMCP 一键启动
echo ============================================================
echo.

REM ---- 1. 校验关键路径 ----
if not exist "%UPROJECT%" (
    echo [错误] 找不到项目文件：%UPROJECT%
    pause & exit /b 1
)
if not exist "%UE_EXE%" (
    echo [警告] 找不到 UE 编辑器：%UE_EXE%
    echo        如果你的引擎版本不是 5.7，请编辑本脚本里的 UE_EXE 路径。
    pause & exit /b 1
)

REM ---- 2. 检查 UE 是否已在运行 ----
tasklist /FI "IMAGENAME eq UnrealEditor.exe" 2>nul | find /I "UnrealEditor.exe" >nul
if %errorlevel%==0 (
    echo [信息] UnrealEditor 已在运行，跳过启动。
) else (
    echo [信息] 正在启动 UE 编辑器...
    start "" "%UE_EXE%" "%UPROJECT%"
    echo        已发出启动命令，UE 首次加载可能需要 1-2 分钟。
)
echo.

REM ---- 3. 等待 MCP 插件监听 55557 端口 ----
echo [信息] 正在等待 UnrealMCP 插件监听端口 %MCP_PORT% ...
echo        （UE 启动并加载插件后端口才会就绪，请耐心等待）
set /a tries=0
:WAIT_PORT
set /a tries+=1
netstat -ano | find ":%MCP_PORT% " | find "LISTENING" >nul
if %errorlevel%==0 (
    echo.
    echo [成功] 端口 %MCP_PORT% 已就绪，UnrealMCP 插件正在监听！
    goto PORT_READY
)
if %tries% GEQ 90 (
    echo.
    echo [超时] 等待 3 分钟仍未检测到端口 %MCP_PORT%。
    echo        请确认 UE 已完全启动，且 UnrealMCP 插件已启用。
    goto END
)
<nul set /p "=."
timeout /t 2 >nul
goto WAIT_PORT

:PORT_READY
echo.
echo ============================================================
echo   一切就绪！现在你可以：
echo   1) 在本项目目录打开终端运行  claude   （会自动连 unreal-bridge）
echo   2) 或在 Cowork 会话里让我通过桥接脚本操作 UE
echo ============================================================

:END
echo.
pause
endlocal
