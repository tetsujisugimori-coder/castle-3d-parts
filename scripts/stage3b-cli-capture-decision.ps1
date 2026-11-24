#Requires -Version 7.0
# Pure decision function used by the controller and its non-destructive tests.
# Primary result is preserved even when mandatory stdout/stderr capture fails.
function Resolve-Stage3BCaptureDecision {
 [CmdletBinding()]
 param(
  [Parameter(Mandatory)][int]$PrimaryExitCode,
  [Parameter(Mandatory)][string]$PrimaryStatus,
  [AllowNull()][object]$WorkerExitCode=$null,
  [string[]]$CaptureProblems=@()
 )
 $problems=@($CaptureProblems | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
 $captureStatus=if($problems.Count -eq 0){'COMPLETE'}else{'INCOMPLETE'}
 $status=$PrimaryStatus
 $code=$PrimaryExitCode
 if($captureStatus -eq 'INCOMPLETE'){
  $status='INCOMPLETE'
  # Preserve the existing timeout (124) and setup failure (4) meanings.
  # Every other incomplete-capture case returns the dedicated nonzero code 2.
  if($PrimaryExitCode -ne 124 -and $PrimaryExitCode -ne 4){$code=2}
 }
 [pscustomobject]@{
  Status=$status
  ExitCode=$code
  CaptureStatus=$captureStatus
  CaptureProblems=@($problems)
  PrimaryStatus=$PrimaryStatus
  PrimaryExitCode=$PrimaryExitCode
  WorkerExitCode=$WorkerExitCode
 }
}
