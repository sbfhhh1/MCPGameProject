# 启动 UE 编辑器
$ErrorActionPreference = "Continue"
$UEPath = "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
$ProjectPath = "C:\UE_Project\MCPGameProject\MCPGameProject.uproject"

Write-Host "启动 UE 编辑器..."

if (Test-Path $UEPath) {
    Start-Process $UEPath -ArgumentList $ProjectPath
    Write-Host "UE 编辑器已启动"
} else {
    Write-Host "错误: 找不到 UE 可执行文件: $UEPath"
}