# 检查 UE 编辑器状态
$ErrorActionPreference = "Continue"

Write-Host "检查 UE 编辑器状态..."

# 检查 UE 是否运行
$ueProcesses = Get-Process -Name "UnrealEditor" -ErrorAction SilentlyContinue
if ($ueProcesses) {
    Write-Host "UE 编辑器正在运行，进程 ID: $($ueProcesses.Id)"
} else {
    Write-Host "警告: UE 编辑器未运行"
}

# 检查 MCP 端口
$port = 55557

try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("127.0.0.1", $port)
    Write-Host "MCP 端口 $port 可访问"
    $tcpClient.Close()
} catch {
    Write-Host "MCP 端口 $port 无法连接: $($_.Exception.Message)"
}

# 读取最近的构建日志
$logPath = "C:\Users\lafa\AppData\Local\UnrealBuildTool\Log.txt"
if (Test-Path $logPath) {
    Write-Host "`n最近 50 行日志:"
    Get-Content $logPath -Tail 50
}