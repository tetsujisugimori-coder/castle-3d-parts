#Requires -Version 7.0
# Non-destructive controls for creation-owned handles. No process is terminated.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'stage3b-transport-cli.ps1') -Raw -Encoding UTF8
foreach($item in @('[System.Diagnostics.Process]::Start($info)','$workerSafeHandle=$worker.SafeHandle','$workerSafeHandle.DangerousGetHandle()','$workerIdentityReady -and $snapshotOk','$worker.Kill()','$worker.WaitForExit($TimeoutSeconds*1000)')){
 if(-not $source.Contains($item)){throw "Required launch-handle invariant missing: $item"}
}
foreach($unsafe in @('Start-Process -FilePath','Wait-Process -Id $worker.Id','taskkill.exe /PID $worker.Id','GetProcessById')){
 if($source.Contains($unsafe)){throw "Unsafe PID re-acquisition: $unsafe"}
}
function Owns-Worker([bool]$created,[bool]$snapshot,[bool]$alive,[bool]$handleMatches,[bool]$startMatches) {
 return ($created -and $snapshot -and $alive -and $handleMatches -and $startMatches)
}
$cases=@(
 @{name='valid creation handle';values=@($true,$true,$true,$true,$true);permit=$true},
 @{name='worker exited before observation';values=@($true,$true,$false,$true,$true);permit=$false},
 @{name='missing creation handle';values=@($false,$true,$true,$false,$true);permit=$false},
 @{name='PID reused by other process';values=@($false,$true,$true,$false,$false);permit=$false},
 @{name='early exit with PID recycled';values=@($true,$true,$false,$false,$false);permit=$false},
 @{name='snapshot unavailable';values=@($true,$false,$true,$true,$true);permit=$false},
 @{name='different native handle';values=@($true,$true,$true,$false,$true);permit=$false},
 @{name='different creation timestamp';values=@($true,$true,$true,$true,$false);permit=$false}
)
foreach($case in $cases){
 $v=$case.values
 $actual=Owns-Worker -created $v[0] -snapshot $v[1] -alive $v[2] -handleMatches $v[3] -startMatches $v[4]
 if($actual -ne $case.permit){throw "Unsafe synthetic decision: $($case.name)"}
}
# Benign worker exits on its own; validate retained creation handle even after exit.
$start=[System.Diagnostics.ProcessStartInfo]::new()
$start.FileName=(Get-Process -Id $PID).Path
$start.UseShellExecute=$false
$start.CreateNoWindow=$true
$start.RedirectStandardOutput=$true
$start.RedirectStandardError=$true
foreach($arg in @('-NoProfile','-NonInteractive','-Command','exit 0')){[void]$start.ArgumentList.Add($arg)}
$child=$null
try{
 $child=[System.Diagnostics.Process]::Start($start)
 if($null -eq $child){throw 'Creation returned null'}
 $handle=$child.SafeHandle
 if($null -eq $handle -or $handle.IsInvalid -or $handle.IsClosed){throw 'No creation handle'}
 $native=$handle.DangerousGetHandle()
 if(-not $child.WaitForExit(10000)){throw 'Benign process did not finish (test does not call Kill)'}
 if($handle.IsInvalid -or $handle.IsClosed -or $handle.DangerousGetHandle() -ne $native){
  throw 'Creation handle was not retained after exit'
 }
}finally{if($null -ne $child){$child.Dispose()}}
Write-Output (@{status='PASS';syntheticCount=$cases.Count;creationHandleProbe='PASS';stopRequested=$false}|ConvertTo-Json -Compress)
