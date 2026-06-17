# 编译 UE 项目
$ErrorActionPreference = "Continue"
$ProjectPath = "C:\UE_Project\MCPGameProject\MCPGameProject.uproject"
$BuildBat = "C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat"

Write-Host "开始编译项目..."

# 调用 Build.bat
& $BuildBat $ProjectPath -Target="MCPGameProjectEditor Win64" Development -WaitMutex

if ($LASTEXITCODE -eq 0) {
    Write-Host "编译成功!"
} else {
    Write-Host "编译失败，退出码: $LASTEXITCODE"
}