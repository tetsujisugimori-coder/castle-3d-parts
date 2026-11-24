#Requires -Version 7.0
# Non-destructive regression: capture-failure decisions, not actual disk corruption.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'stage3b-cli-capture-decision.ps1')
$cases=@(
 @{name='normal stdout plus empty but successfully captured stderr';primary=0;state='PASS';worker=0;problems=@();expectedState='PASS';expectedExit=0;capture='COMPLETE'},
 @{name='stdout copy incomplete';primary=0;state='PASS';worker=0;problems=@('stdout transfer incomplete');expectedState='INCOMPLETE';expectedExit=2;capture='INCOMPLETE'},
 @{name='stderr asynchronous copy exception';primary=0;state='PASS';worker=0;problems=@('stderr copy exception');expectedState='INCOMPLETE';expectedExit=2;capture='INCOMPLETE'},
 @{name='stdout flush exception';primary=0;state='PASS';worker=0;problems=@('stdout flush failed');expectedState='INCOMPLETE';expectedExit=2;capture='INCOMPLETE'},
 @{name='stderr missing output file';primary=0;state='PASS';worker=0;problems=@('stderr file missing');expectedState='INCOMPLETE';expectedExit=2;capture='INCOMPLETE'},
 @{name='stdout missing or unreadable';primary=0;state='PASS';worker=0;problems=@('stdout readback failed');expectedState='INCOMPLETE';expectedExit=2;capture='INCOMPLETE'},
 @{name='stdout and stderr both incomplete';primary=0;state='PASS';worker=0;problems=@('stdout transfer incomplete','stderr flush failed');expectedState='INCOMPLETE';expectedExit=2;capture='INCOMPLETE'},
 @{name='worker failure without capture failure';primary=1;state='FAIL';worker=1;problems=@();expectedState='FAIL';expectedExit=1;capture='COMPLETE'},
 @{name='worker failure with missing capture';primary=1;state='FAIL';worker=1;problems=@('stderr transfer incomplete');expectedState='INCOMPLETE';expectedExit=2;capture='INCOMPLETE'},
 @{name='timeout retains exit124 and separate capture failure';primary=124;state='TIMEOUT_RECOVERY_UNKNOWN';worker=$null;problems=@('stdout transfer incomplete');expectedState='INCOMPLETE';expectedExit=124;capture='INCOMPLETE'},
 @{name='setup failure retains exit4';primary=4;state='INCOMPLETE';worker=$null;problems=@('stdout not started');expectedState='INCOMPLETE';expectedExit=4;capture='INCOMPLETE'}
)
foreach($case in $cases){
 $decision=Resolve-Stage3BCaptureDecision -PrimaryExitCode $case.primary -PrimaryStatus $case.state -WorkerExitCode $case.worker -CaptureProblems $case.problems
 if($decision.Status -ne $case.expectedState -or $decision.ExitCode -ne $case.expectedExit -or $decision.CaptureStatus -ne $case.capture){
  throw "Incorrect decision: $($case.name) => $($decision | ConvertTo-Json -Compress)"
 }
 if($decision.PrimaryExitCode -ne $case.primary -or $decision.PrimaryStatus -ne $case.state -or $decision.WorkerExitCode -ne $case.worker){
  throw "Primary worker outcome lost: $($case.name)"
 }
 if($decision.CaptureProblems.Count -ne $case.problems.Count){throw "Capture error list lost: $($case.name)"}
}
# Check that the real controller uses the tested decision, waits both capture
# tasks, flushes both streams and reads back both mandatory files.
$src=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'stage3b-transport-cli.ps1') -Raw -Encoding UTF8
foreach($expected in @(
 'Resolve-Stage3BCaptureDecision',
 '$task.Wait(2000)',
 '$stream.Flush($true)',
 '[IO.File]::Open(',
 '$decision.CaptureStatus',
 'captureProblems=$decision.CaptureProblems',
 'workerExitCode=$workerExitCode',
 "'stdout'",
 "'stderr'"
)){
 if(-not $src.Contains($expected)){throw "Mandatory capture gate missing in controller: $expected"}
}
Write-Output (@{status='PASS';cases=$cases.Count;kind='non-destructive capture counterexamples';stopRequested=$false}|ConvertTo-Json -Compress)
