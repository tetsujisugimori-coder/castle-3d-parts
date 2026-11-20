$ErrorActionPreference = 'Stop'
$fixed = '72ddc71d6ffbd461de143fbf27fb3629bcce4aa8'
$repo = $PWD.Path
$cli = Join-Path $repo 'scripts/stage3b-transport-cli.ps1'
$blob = (git hash-object $cli).Trim()
if ($blob -cne (git rev-parse "$($fixed):scripts/stage3b-transport-cli.ps1").Trim()) { throw 'CLI bytes differ' }
$helper = 'scripts/stage3b-cli-capture-decision.ps1'
if ((git hash-object $helper).Trim() -cne (git rev-parse "$($fixed):$helper").Trim()) { throw 'Helper bytes differ' }
$root = Join-Path $env:RUNNER_TEMP "pr44-timeout-$env:GITHUB_RUN_ID"
New-Item -ItemType Directory $root | Out-Null
$ev = Join-Path $root 'evidence'
$fake = (New-Item -ItemType Directory (Join-Path $root 'fixture')).FullName
$env:PR44_TIMEOUT_EVIDENCE = $ev
$env:Path = "$fake;$env:Path"
$stub = Join-Path $fake 'npm.ps1'
@'
$ErrorActionPreference = 'Stop'
$dir = $env:PR44_TIMEOUT_EVIDENCE
$parent = Get-Process -Id $PID
$child = Start-Process -PassThru -FilePath $parent.Path -ArgumentList '-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 45' -RedirectStandardOutput (Join-Path $dir 'child-out.log') -RedirectStandardError (Join-Path $dir 'child-err.log')
@{
  stub = $PSCommandPath
  workerPid = $PID
  workerStartTicks = $parent.StartTime.ToUniversalTime().Ticks.ToString()
  childPid = $child.Id
  childStartTicks = $child.StartTime.ToUniversalTime().Ticks.ToString()
  readyUtc = [DateTime]::UtcNow.ToString('o')
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'fixture.json')
[Console]::Out.WriteLine('synthetic timeout fixture entered')
Start-Sleep -Seconds 60
exit 99
'@ | Set-Content -LiteralPath $stub
if ((Get-Command npm).Path -cne $stub) { throw 'Fixture does not resolve as npm' }
$info = [Diagnostics.ProcessStartInfo]::new()
$info.FileName = (Get-Process -Id $PID).Path
$info.UseShellExecute = $false
$limit = 15
foreach ($arg in @('-NoProfile','-NonInteractive','-File',$cli,'-ExpectedHead',$fixed,'-RepositoryPath',$repo,'-WorktreePath',(Join-Path $root 'worktree'),'-DependenciesPath',(Join-Path $root 'deps'),'-BrowsersPath',(Join-Path $root 'browsers'),'-EvidenceRoot',$ev,'-TimeoutSeconds',"$limit")) { $info.ArgumentList.Add($arg) }
$clock = [Diagnostics.Stopwatch]::StartNew()
$launchUtc = [DateTime]::UtcNow
$ctrl = [Diagnostics.Process]::Start($info)
$fixture = $null
$marker = Join-Path $ev 'fixture.json'
while ($clock.Elapsed.TotalSeconds -lt 14 -and -not $ctrl.HasExited) {
  if (Test-Path -LiteralPath $marker) {
    try { $fixture = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json; break } catch {}
  }
  Start-Sleep -Milliseconds 50
}
function Get-ObservedProcess($processId, $expectedTicks) {
  $handle = Get-Process -Id $processId -ErrorAction Stop
  $null = $handle.Handle
  if ($handle.StartTime.ToUniversalTime().Ticks.ToString() -cne $expectedTicks) { throw 'PID identity mismatch' }
  $handle
}
if ($null -eq $fixture) { throw 'Synthetic worker did not produce an identity marker' }
$worker = Get-ObservedProcess $fixture.workerPid $fixture.workerStartTicks
$child = Get-ObservedProcess $fixture.childPid $fixture.childStartTicks
if (-not $ctrl.WaitForExit(40000)) { throw 'Controller exceeded observer deadline' }
$cliDuration = $clock.Elapsed.TotalSeconds
$receiptPath = Join-Path $ev 'controller-receipt.json'
$receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
$written = (Get-Item -LiteralPath $receiptPath).LastWriteTimeUtc
$workerExitUtc = if ($worker.HasExited) { $worker.ExitTime.ToUniversalTime() } else { $null }
$childAtReturn = -not $child.HasExited
$childNaturalExit = $child.WaitForExit(50000)
$result = [ordered]@{
  fixedHead = $fixed; harnessHead = $env:GITHUB_SHA; cliBlob = $blob
  os = [Environment]::OSVersion.VersionString; pwsh = $PSVersionTable.PSVersion.ToString()
  timeoutSeconds = $limit; controllerExitCode = $ctrl.ExitCode; controllerElapsedSeconds = $cliDuration
  launchUtc = $launchUtc.ToString('o'); receiptLastWriteUtc = $written.ToString('o')
  launchToReceiptSeconds = ($written - $launchUtc).TotalSeconds
  workerStartToReceiptSeconds = ($written - $worker.StartTime.ToUniversalTime()).TotalSeconds
  workerExitToReceiptSeconds = if ($null -ne $workerExitUtc) { ($written - $workerExitUtc).TotalSeconds } else { $null }
  workerExitedAtControllerReturn = ($null -ne $workerExitUtc)
  workerExitUtc = if ($null -ne $workerExitUtc) { $workerExitUtc.ToString('o') } else { $null }
  observedWorkerExitCode = if ($null -ne $workerExitUtc) { $worker.ExitCode } else { $null }
  childAliveAtControllerReturn = $childAtReturn; childExitedNaturally = $childNaturalExit
  childExitUtc = if ($childNaturalExit) { $child.ExitTime.ToUniversalTime().ToString('o') } else { $null }
  childExitCode = if ($childNaturalExit) { $child.ExitCode } else { $null }
  receipt = $receipt
}
$result | ConvertTo-Json -Depth 12 | Tee-Object -FilePath (Join-Path $ev 'observation.json')
if ($ctrl.ExitCode -ne 124 -or -not $receipt.timeout -or $receipt.workerPid -ne $fixture.workerPid -or -not $childNaturalExit) {
  throw 'Timeout/fixture/cleanup verification failed'
}
