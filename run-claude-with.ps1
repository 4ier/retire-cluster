param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "D:\codebase\retire-cluster\",
    
    [Parameter(Mandatory=$false)]
    [string]$Prompt = "请完成web仪表板的前后端代码开发和测试，测试完备&通过后，并提交到github",
    
    [switch]$SkipPermissions = $true
)

Set-Location $ProjectPath

if ($SkipPermissions) {
    claude --dangerously-skip-permissions $Prompt
} else {
    claude $Prompt
}
# 受到这个脚本的启发，我们的retire cluster或许需要支持一个定时的queue