#Requires -Version 5.1
<#
.SYNOPSIS
Install the US Sleep Regulatory skill for Codex, Claude Code, and OpenCode on Windows.

.DESCRIPTION
Copies the skill once per client (no symlinks required). Updates preserve
snapshots/. Also installs the OpenCode /us-sleep-regulatory command wrapper.

Python 3.9+ is installed automatically (per-user, from python.org) when missing.
Use -SkipPythonInstall to opt out, or -ForcePythonInstall to repair/reinstall.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\install.ps1

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Target all -Force

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Uninstall

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\install.ps1 -From .\us-sleep-regulatory-v1.2.0.zip -Sha256 <hex>
#>
[CmdletBinding()]
param(
    [string]$Target = "all",
    [string]$BaseDir = "",
    [string]$From = "",
    [string]$Sha256 = "",
    [string]$Version = "",
    [string]$Destination = "",
    [switch]$Force,
    [switch]$NoDoctor,
    [switch]$Uninstall,
    [switch]$SkipPythonInstall,
    [switch]$ForcePythonInstall,
    [string]$PythonVersion = "3.12.10"
)

$ErrorActionPreference = "Stop"
$SkillName = "us-sleep-regulatory"
$SkillDisplay = "US Sleep Regulatory"
$DefaultVersion = "1.6.0"

$Repo = "allbegray/us-sleep-regulatory"
if ($env:US_SLEEP_REG_REPO) { $Repo = $env:US_SLEEP_REG_REPO }
if (-not $Sha256 -and $env:US_SLEEP_REG_SHA256) { $Sha256 = $env:US_SLEEP_REG_SHA256 }
if (-not $Version) {
    if ($env:US_SLEEP_REG_VERSION) { $Version = $env:US_SLEEP_REG_VERSION }
    else { $Version = $DefaultVersion }
}

$ScriptRoot = $PSScriptRoot
if (-not $ScriptRoot) { $ScriptRoot = (Get-Location).Path }

if (-not $BaseDir) {
    if ($env:USERPROFILE) { $BaseDir = $env:USERPROFILE }
    elseif ($HOME) { $BaseDir = $HOME }
    else { $BaseDir = (Get-Location).Path }
}

$TempDirs = New-Object System.Collections.Generic.List[string]
$script:Python = $null
$SourceDir = $null
$FromRoot = $null

function Join-Parts {
    param([string[]]$Parts)
    $path = $Parts[0]
    for ($i = 1; $i -lt $Parts.Length; $i++) { $path = Join-Path $path $Parts[$i] }
    return $path
}

function Find-SkillDir {
    param([string]$Path)
    $nested = Join-Parts @($Path, "skills", $SkillName, "SKILL.md")
    if (Test-Path -LiteralPath $nested) { return (Join-Parts @($Path, "skills", $SkillName)) }
    if (Test-Path -LiteralPath (Join-Path $Path "SKILL.md")) { return $Path }
    return $null
}

function Find-SkillInTree {
    param([string]$Path)
    $hit = Get-ChildItem -LiteralPath $Path -Recurse -Filter "SKILL.md" -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { return $hit.Directory.FullName }
    return $null
}

function Assert-Checksum {
    param([string]$Path)
    if (-not $Sha256) { return }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    if ($actual.ToUpperInvariant() -ne $Sha256.ToUpperInvariant()) {
        throw "checksum mismatch for $(Split-Path -Leaf $Path): expected $($Sha256.ToLowerInvariant()), got $($actual.ToLowerInvariant())"
    }
    Write-Host "  checksum OK: $(Split-Path -Leaf $Path)"
}

function Resolve-Source {
    if ($From) {
        if (Test-Path -LiteralPath $From -PathType Container) {
            $resolved = (Resolve-Path -LiteralPath $From).Path
            $script:FromRoot = $resolved
            $skill = Find-SkillDir $resolved
            if (-not $skill) { $skill = Find-SkillInTree $resolved }
            if (-not $skill) { throw "SKILL.md not found under $From" }
            return $skill
        }
        if (Test-Path -LiteralPath $From -PathType Leaf) {
            $tmp = Join-Path $env:TEMP ("us-sleep-src-" + [guid]::NewGuid().ToString("N"))
            New-Item -ItemType Directory -Force -Path $tmp | Out-Null
            $TempDirs.Add($tmp)
            Assert-Checksum $From
            Expand-Archive -LiteralPath $From -DestinationPath $tmp -Force
            $script:FromRoot = $tmp
            $skill = Find-SkillDir $tmp
            if (-not $skill) { $skill = Find-SkillInTree $tmp }
            if (-not $skill) { throw "SKILL.md not found in $From" }
            return $skill
        }
        # URL
        $tmp = Join-Path $env:TEMP ("us-sleep-src-" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Force -Path $tmp | Out-Null
        $TempDirs.Add($tmp)
        $zip = Join-Path $tmp "download.zip"
        Write-Host "Downloading $From ..."
        Invoke-WebRequest -Uri $From -OutFile $zip -UseBasicParsing
        Assert-Checksum $zip
        Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
        $script:FromRoot = $tmp
        $skill = Find-SkillDir $tmp
        if (-not $skill) { $skill = Find-SkillInTree $tmp }
        if (-not $skill) { throw "SKILL.md not found in $From" }
        return $skill
    }

    $local = Find-SkillDir $ScriptRoot
    if ($local) { $script:FromRoot = $ScriptRoot; return $local }

    $tmp = Join-Path $env:TEMP ("us-sleep-src-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $TempDirs.Add($tmp)
    $url = "https://github.com/$Repo/archive/refs/tags/v$Version.zip"
    $zip = Join-Path $tmp "download.zip"
    Write-Host "Downloading $url ..."
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    Assert-Checksum $zip
    Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
    $script:FromRoot = $tmp
    $skill = Find-SkillDir $tmp
    if (-not $skill) { $skill = Find-SkillInTree $tmp }
    if (-not $skill) { throw "SKILL.md not found in the downloaded archive" }
    return $skill
}

function Find-DistFile {
    param([string]$Name)
    $candidates = @()
    foreach ($base in @($SourceDir, $FromRoot, $ScriptRoot)) {
        if ($base) { $candidates += (Join-Path $base $Name) }
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    return $null
}

function Copy-SkillTree {
    param([string]$Source, [string]$Dest)
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    $exclude = @("tools", ".github", "dist", "__pycache__", ".git", ".idea")
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        if ($exclude -contains $_.Name) { return }
        Copy-Item -LiteralPath $_.FullName -Destination $Dest -Recurse -Force
    }
    foreach ($name in @("README.md", "README.ko.md", "LICENSE", "CHANGELOG.md", "VERSION", "install.sh", "install.ps1")) {
        $file = Find-DistFile $name
        if ($file) { Copy-Item -LiteralPath $file -Destination (Join-Path $Dest $name) -Force }
    }
}

function Install-One {
    param([string]$Dest)
    if (Test-Path -LiteralPath $Dest) {
        if (-not $Force) { throw "already installed at $Dest (use -Force)" }
    }
    $snapBackup = $null
    $snapDir = Join-Path $Dest "snapshots"
    if ($Force -and (Test-Path -LiteralPath $snapDir)) {
        $snapBackup = Join-Path $env:TEMP ("us-sleep-snap-" + [guid]::NewGuid().ToString("N"))
        Copy-Item -LiteralPath $snapDir -Destination $snapBackup -Recurse -Force
        $TempDirs.Add($snapBackup)
        Write-Host "  preserving snapshots"
    }
    if (Test-Path -LiteralPath $Dest) { Remove-Item -LiteralPath $Dest -Recurse -Force }
    Copy-SkillTree $SourceDir $Dest
    if ($snapBackup) {
        $snapDest = Join-Path $Dest "snapshots"
        New-Item -ItemType Directory -Force -Path $snapDest | Out-Null
        Get-ChildItem -LiteralPath $snapBackup -Force | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $snapDest -Recurse -Force
        }
        Write-Host "  restored snapshots"
    }
    Write-Host "  installed: $Dest"
}

function Uninstall-One {
    param([string]$Dest)
    $skill = Join-Path $Dest "SKILL.md"
    if (-not (Test-Path -LiteralPath $skill)) { return $false }
    $content = Get-Content -LiteralPath $skill -Raw
    if ($content -notmatch "US Sleep Regulatory") { return $false }
    Remove-Item -LiteralPath $Dest -Recurse -Force
    Write-Host "Removed: $Dest"
    return $true
}

function Install-OpenCodeCommand {
    param([string]$SkillDir, [string]$CommandsDir)
    $src = Join-Path $SkillDir "commands\opencode\us-sleep-regulatory.md"
    if (-not (Test-Path -LiteralPath $src)) { return }
    New-Item -ItemType Directory -Force -Path $CommandsDir | Out-Null
    $dest = Join-Path $CommandsDir "us-sleep-regulatory.md"
    Copy-Item -LiteralPath $src -Destination $dest -Force
    Write-Host "  command: $dest"
}

function Test-PythonCandidate {
    param([string]$Exe, [string[]]$Arguments)
    try {
        $version = & $Exe @Arguments -c "import sys; print(str(sys.version_info[0]) + '.' + str(sys.version_info[1]))" 2>$null
        if ($LASTEXITCODE -eq 0 -and $version -match '^([0-9]+)\.([0-9]+)$') {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                return [pscustomobject]@{ Exe = $Exe; Args = $Arguments; Version = "$major.$minor" }
            }
        }
    } catch { }
    return $null
}

function Find-Python {
    # Prefer py/python on PATH, but skip the Microsoft Store aliases.
    foreach ($name in @("py", "python")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        if ($cmd.Source -match "WindowsApps") { continue }
        $arguments = @()
        if ($name -eq "py") { $arguments = @("-3") }
        $found = Test-PythonCandidate -Exe $cmd.Source -Arguments $arguments
        if ($found) { return $found }
    }

    # Known per-user and machine installs.
    $roots = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python"),
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    )
    foreach ($root in $roots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        foreach ($name in @("Python314", "Python313", "Python312", "Python311", "Python310", "Python39")) {
            $exe = Join-Path $root "$name\python.exe"
            if (Test-Path -LiteralPath $exe) {
                $found = Test-PythonCandidate -Exe $exe -Arguments @()
                if ($found) { return $found }
            }
        }
    }
    return $null
}

function Install-Python {
    $arch = "amd64"
    switch ($env:PROCESSOR_ARCHITECTURE) {
        "AMD64" { $arch = "amd64" }
        "ARM64" { $arch = "arm64" }
        "x86" { $arch = "win32" }
        default { $arch = "amd64" }
    }
    if ($arch -eq "win32") {
        $fileName = "python-$PythonVersion.exe"
    } else {
        $fileName = "python-$PythonVersion-$arch.exe"
    }
    $url = "https://www.python.org/ftp/python/$PythonVersion/$fileName"
    $installer = Join-Path $env:TEMP $fileName
    Write-Host "Python 3.9+ not found. Installing Python $PythonVersion ($arch, per-user)..."
    Write-Host "  $url"
    $oldProgress = $ProgressPreference
    $ProgressPreference = "SilentlyContinue"
    try {
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    } finally {
        $ProgressPreference = $oldProgress
    }

    $sig = Get-AuthenticodeSignature -FilePath $installer
    if ($sig.Status -ne "Valid" -or -not $sig.SignerCertificate -or $sig.SignerCertificate.Subject -notmatch "Python Software Foundation") {
        throw "Python installer signature check failed ($($sig.Status))."
    }

    $argList = @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=1",
        "Include_launcher=1",
        "Include_pip=1",
        "Include_test=0",
        "Include_doc=0",
        "AssociateFiles=0",
        "Shortcuts=0",
        "CompileAll=0"
    )
    $proc = Start-Process -FilePath $installer -ArgumentList $argList -Wait -PassThru
    Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
    if ($proc.ExitCode -notin @(0, 3010, 1638)) {
        throw "Python installer exited with code $($proc.ExitCode)."
    }

    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"

    $found = $null
    for ($i = 0; $i -lt 30; $i++) {
        $found = Find-Python
        if ($found) { break }
        Start-Sleep -Seconds 2
    }
    if (-not $found) { throw "Python installer finished but python.exe was not found." }
    Write-Host "Python installed: $($found.Exe) (version $($found.Version))"
    return $found
}

function Ensure-Python {
    $existing = Find-Python
    if ($existing -and -not $ForcePythonInstall) { return $existing }
    if ($SkipPythonInstall) {
        if ($existing) { return $existing }
        Write-Warning "Python 3.9+ was not found. Skipping automatic install because -SkipPythonInstall was used."
        Write-Warning "Install it from https://www.python.org/downloads/windows/ and rerun this installer."
        return $null
    }
    try {
        $installed = Install-Python
        if ($installed) { return $installed }
    } catch {
        Write-Warning "Automatic Python install failed: $($_.Exception.Message)"
    }
    $manual = Find-Python
    if ($manual) { return $manual }
    Write-Warning "Python 3.9+ is still unavailable. Install it from https://www.python.org/downloads/windows/ and rerun this installer."
    return $null
}

function Get-PythonDisplay {
    if (-not $script:Python) { return "python" }
    if ($script:Python.Exe -eq "py") { return "py -3" }
    if ($script:Python.Exe -match '\s') { return '"' + $script:Python.Exe + '"' }
    return $script:Python.Exe
}

function Invoke-Doctor {
    param([string]$SkillDir)
    if (-not $script:Python) {
        Write-Warning "Python 3.9+ is unavailable; skipping the doctor check."
        return
    }
    $reg = Join-Path $SkillDir "scripts\reg.py"
    if (-not (Test-Path -LiteralPath $reg)) { return }
    $pyArgs = @($script:Python.Args) + @($reg, "doctor", "--format", "md")
    & $script:Python.Exe @pyArgs
}

# Paths
$codexDest = Join-Parts @($BaseDir, ".agents", "skills", $SkillName)
$claudeDest = Join-Parts @($BaseDir, ".claude", "skills", $SkillName)
$opencodeDest = Join-Parts @($BaseDir, ".config", "opencode", "skills", $SkillName)
$opencodeCommandsDir = Join-Parts @($BaseDir, ".config", "opencode", "commands")
$opencodeSourceDest = $opencodeDest
$projectRoot = (Get-Location).Path
$projectCodex = Join-Parts @($projectRoot, ".agents", "skills", $SkillName)
$projectClaude = Join-Parts @($projectRoot, ".claude", "skills", $SkillName)
$projectOpencode = Join-Parts @($projectRoot, ".opencode", "skills", $SkillName)
$projectCommands = Join-Parts @($projectRoot, ".opencode", "commands")

$dests = @()
$commandDirs = @()

if ($Destination) {
    $dests = @($Destination)
} elseif ($Target -eq "all") {
    $dests = @($codexDest, $claudeDest, $opencodeDest)
    $commandDirs = @($opencodeCommandsDir)
} elseif ($Target -eq "auto") {
    $dests = @($codexDest)
    if (Test-Path -LiteralPath (Join-Path $BaseDir ".claude")) { $dests += $claudeDest }
    if (Test-Path -LiteralPath (Join-Path $BaseDir ".config\opencode")) {
        $dests += $opencodeDest
        $commandDirs = @($opencodeCommandsDir)
    }
} elseif ($Target -eq "codex") {
    $dests = @($codexDest)
} elseif ($Target -eq "claude") {
    $dests = @($claudeDest)
} elseif ($Target -eq "opencode") {
    $dests = @($opencodeDest)
    $commandDirs = @($opencodeCommandsDir)
} elseif ($Target -eq "project") {
    $dests = @($projectCodex, $projectClaude, $projectOpencode)
    $commandDirs = @($projectCommands)
    $opencodeSourceDest = $projectOpencode
} elseif ($Target -eq "codex-legacy") {
    $dests = @(Join-Parts @($BaseDir, ".codex", "skills", $SkillName))
} else {
    $dests = @($Target)
}

if ($Uninstall) {
    $removed = 0
    foreach ($dest in $dests) {
        if (Uninstall-One $dest) { $removed++ }
    }
    foreach ($dir in $commandDirs) {
        $cmd = Join-Path $dir "us-sleep-regulatory.md"
        if (Test-Path -LiteralPath $cmd) {
            $content = Get-Content -LiteralPath $cmd -Raw
            if ($content -match "us-sleep-regulatory") {
                Remove-Item -LiteralPath $cmd -Force
                Write-Host "Removed: $cmd"
                $removed++
            }
        }
    }
    if ($removed -eq 0) { throw "no installed US Sleep Regulatory skill found for target '$Target'" }
    exit 0
}

$SourceDir = Resolve-Source
$script:Python = Ensure-Python
$installedVersion = $Version
$versionFile = Find-DistFile "VERSION"
if ($versionFile) { $installedVersion = (Get-Content -LiteralPath $versionFile -Raw).Trim() }

Write-Host "Installing $SkillDisplay v$installedVersion"
Write-Host "  from: $SourceDir"
foreach ($dest in $dests) { Install-One $dest }
foreach ($dir in $commandDirs) { Install-OpenCodeCommand $opencodeSourceDest $dir }

if (-not $NoDoctor) {
    Write-Host ""
    Write-Host "== source health check =="
    try { Invoke-Doctor $dests[0] }
    catch {
        Write-Warning "The health check failed. The skill is installed; run it later:"
        Write-Warning "  $(Get-PythonDisplay) `"$($dests[0])\scripts\reg.py`" doctor"
    }
}

Write-Host ""
Write-Host "Installed: $SkillDisplay v$installedVersion"
foreach ($dest in $dests) { Write-Host "Path: $dest" }
$py = Get-PythonDisplay
if ($script:Python) { Write-Host "Python: $($script:Python.Version) ($py)" } else { Write-Host "Python: NOT FOUND" }
Write-Host ""
Write-Host "How to invoke:"
Write-Host "  Codex CLI     `$us-sleep-regulatory  (or /skills to list)"
Write-Host "  Claude Code   /us-sleep-regulatory"
Write-Host "  OpenCode      /us-sleep-regulatory  (or @us-sleep-regulatory)"
Write-Host "  CLI           $py `"$($dests[0])\scripts\reg.py`" --help"
Write-Host ""
Write-Host "First commands:"
Write-Host "  $py `"$($dests[0])\scripts\reg.py`" predicates --product-code QVO --format md"
Write-Host "  $py `"$($dests[0])\scripts\reg.py`" doctor"
Write-Host ""
Write-Host "Update:    re-run with -Force"
Write-Host "Uninstall: .\install.ps1 -Target $Target -Uninstall"

foreach ($tmp in $TempDirs) {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
