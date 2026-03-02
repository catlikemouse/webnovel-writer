# D:\Code\gitRepository\webnovel-writer\start.ps1

# 1. 设置中转大模型的 API 环境变量 (主模型，替代 Claude 官方)
# 使用您的 Antigravity 本地反代服务
$env:ANTHROPIC_API_KEY="sk-4f5fd675bb47490c87490af189cd222a"
$env:ANTHROPIC_BASE_URL="http://127.0.0.1:8046"

# 因为您使用的是 Antigravity 代理的 claude-opus-4-6-thinking 
# 我们需要告诉 Claude Code 系统这使用的是什么模型。
$env:MODEL="claude-opus-4-6-thinking"

# 2. 挂载项目的 Python 脚本路径
$env:PYTHONPATH = "$PSScriptRoot\.claude\scripts"

Write-Host "环境变量设置完成！正在启动 Claude Code..." -ForegroundColor Green

# 3. 运行 Claude Code 工具
npx @anthropic-ai/claude-code
