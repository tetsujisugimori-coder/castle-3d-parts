#Requires -Version 7.0
# Stage3B fixed-HEAD CLI. All outcomes and logs are preserved; no cleanup.
[CmdletBinding(DefaultParameterSetName='Controller')]
param(
 [Parameter(Mandatory,ParameterSetName='Controller')][ValidatePattern('^[0-9a-fA-F]{40}$')][string]$ExpectedHead,
 [Parameter(Mandatory,ParameterSetName='Controller')][string]$RepositoryPath,
 [Parameter(Mandatory,ParameterSetName='Controller')][string]$WorktreePath,
 [Parameter(Mandatory,ParameterSetName='Controller')][string]$DependenciesPath,
 [Parameter(Mandatory,ParameterSetName='Controller')][string]$BrowsersPath,
 [Parameter(Mandatory,ParameterSetName='Controller')][string]$EvidenceRoot,
 [Parameter(ParameterSetName='Controller')][ValidateRange(1,900)][int]$TimeoutSeconds=900,
 [Parameter(Mandatory,ParameterSetName='Worker')][string]$WorkerConfig
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'stage3b-cli-capture-decision.ps1')
function SaveJson([string]$Path,[object]$Data) {
 [IO.File]::WriteAllText($Path,($Data|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
}
function ProcessTree([object[]]$Processes,[int]$Root) {
 $ids=[Collections.Generic.HashSet[int]]::new()
 $queue=[Collections.Generic.Queue[int]]::new()
 [void]$ids.Add($Root);$queue.Enqueue($Root)
 while($queue.Count -gt 0){
  $parent=$queue.Dequeue()
  foreach($item in $Processes){
   $id=[int]$item.ProcessId
   if([int]$item.ParentProcessId -eq $parent -and $ids.Add($id)){$queue.Enqueue($id)}
  }
 }
 @($Processes|Where-Object {$ids.Contains([int]$_.ProcessId)})
}
if($PSCmdlet.ParameterSetName -eq 'Worker'){
 $c=Get-Content -LiteralPath $WorkerConfig -Raw -Encoding UTF8|ConvertFrom-Json
 $started=[DateTimeOffset]::UtcNow.ToString('o');$code=4;$state='INCOMPLETE';$issue=$null
 try{
  & git -C $c.repo cat-file -e "$($c.sha)^{commit}"
  if($LASTEXITCODE -ne 0){throw 'Git object missing'}
  & git -C $c.repo worktree add --detach $c.worktree $c.sha
  if($LASTEXITCODE -ne 0){throw 'worktree add failed'}
  Push-Location -LiteralPath $c.worktree
  try{
   if((& git rev-parse HEAD).Trim() -cne $c.sha){throw 'SHA mismatch'}
   if(-not(Test-Path -LiteralPath 'scripts/stage3b-transport-diagnostic.mjs')){throw 'Diagnostic unavailable in HEAD'}
   $env:PLAYWRIGHT_BROWSERS_PATH=$c.browsers
   & npm install --prefix $c.deps --cache $c.cache --ignore-scripts --no-audit --no-fund playwright@1.56.1 three@0.180.0
   if($LASTEXITCODE -ne 0){throw 'npm failed'}
   & (Join-Path $c.deps 'node_modules/.bin/playwright.cmd') install chromium webkit
   if($LASTEXITCODE -ne 0){throw 'browser install failed'}
   $env:PW_MODULE=Join-Path $c.deps 'node_modules/playwright/index.mjs'
   $env:THREE_DIR=Join-Path $c.deps 'node_modules/three'
   & node --test 'scripts/stage3b-transport-evidence.test.mjs'
   if($LASTEXITCODE -ne 0){throw 'offline controls failed'}
   & node 'scripts/stage3b-transport-diagnostic.mjs' $c.output
   $code=[int]$LASTEXITCODE
   $state=if($code -eq 0){'PASS'}elseif($code -eq 2){'INCOMPLETE'}else{'FAIL'}
  }finally{Pop-Location}
 }catch{$issue=$_.Exception.Message;$state='INCOMPLETE';$code=4}
 finally{
  SaveJson (Join-Path $c.evidence 'worker-receipt.json') @{startedUtc=$started;endedUtc=[DateTimeOffset]::UtcNow.ToString('o');expectedHead=$c.sha;status=$state;exitCode=$code;error=$issue}
 }
 exit $code
}
$sha=$ExpectedHead.ToLowerInvariant()
$inputs=@($RepositoryPath,$WorktreePath,$DependenciesPath,$BrowsersPath,$EvidenceRoot)
foreach($path in $inputs){if(-not[IO.Path]::IsPathFullyQualified($path)){throw "Must use absolute path: $path"}}
$paths=@($inputs|ForEach-Object {[IO.Path]::GetFullPath($_).TrimEnd('\','/')})
$repo,$worktree,$deps,$browsers,$evidence=$paths
if(-not(Test-Path -LiteralPath $repo -PathType Container)){throw 'repository missing'}
for($i=0;$i -lt $paths.Count;$i++){
 for($j=$i+1;$j -lt $paths.Count;$j++){
  $a=$paths[$i]+'\';$b=$paths[$j]+'\'
  if($a.StartsWith($b,[StringComparison]::OrdinalIgnoreCase) -or $b.StartsWith($a,[StringComparison]::OrdinalIgnoreCase)){throw 'Overlapping paths'}
 }
}
foreach($path in @($worktree,$deps,$browsers,$evidence)){if(Test-Path -LiteralPath $path){throw "Refuse existing destination: $path"}}
New-Item -ItemType Directory -Path $evidence -ErrorAction Stop|Out-Null
$config=Join-Path $evidence 'worker-config.json'
SaveJson $config @{sha=$sha;repo=$repo;worktree=$worktree;deps=$deps;browsers=$browsers;evidence=$evidence;cache=Join-Path $evidence 'npm-cache';output=Join-Path $evidence 'diagnostic'}
$start=[DateTimeOffset]::UtcNow.ToString('o')
$worker=$null;$code=4;$status='INCOMPLETE';$workerExitCode=$null;$problem=$null;$seen=@();$remaining=@();$timedOut=$false;$snapshotOk=$false;$killExit=$null
$workerHandle=[IntPtr]::Zero;$workerSafeHandle=$null;$workerStartTicks=$null;$workerIdentityReady=$false;$stopAuthorized=$false
$stdoutStream=$null;$stderrStream=$null;$stdoutTask=$null;$stderrTask=$null
try{
 $pwsh=(Get-Process -Id $PID).Path
 $arguments='-NoProfile -NonInteractive -File "'+$PSCommandPath+'" -WorkerConfig "'+$config+'"'
 # .NET Process.Start holds the native creation handle; never reopen a PID.
 $info=[System.Diagnostics.ProcessStartInfo]::new()
 $info.FileName=$pwsh
 $info.UseShellExecute=$false
 $info.CreateNoWindow=$true
 $info.RedirectStandardOutput=$true
 $info.RedirectStandardError=$true
 foreach($arg in @('-NoProfile','-NonInteractive','-File',$PSCommandPath,'-WorkerConfig',$config)){
  [void]$info.ArgumentList.Add([string]$arg)
 }
 $stdoutStream=[IO.File]::Create((Join-Path $evidence 'stdout.log'))
 $stderrStream=[IO.File]::Create((Join-Path $evidence 'stderr.log'))
 $worker=[System.Diagnostics.Process]::Start($info)
 if($null -eq $worker){throw 'Worker process creation returned null'}
 # Only accept a SafeHandle that belongs to the creation-returned Process.
 try{
  $workerSafeHandle=$worker.SafeHandle
  if($null -eq $workerSafeHandle -or $workerSafeHandle.IsInvalid -or $workerSafeHandle.IsClosed){
   throw 'Creation-owned SafeHandle unavailable'
  }
  $workerHandle=$workerSafeHandle.DangerousGetHandle()
  $workerStartTicks=$worker.StartTime.ToUniversalTime().Ticks
  $workerIdentityReady=($workerHandle -ne [IntPtr]::Zero)
 }catch{$workerIdentityReady=$false;$problem='Creation-owned handle unavailable: '+$_.Exception.Message}
 # Drain both pipes concurrently, avoiding stdout/stderr buffer deadlocks.
 $stdoutTask=$worker.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
 $stderrTask=$worker.StandardError.BaseStream.CopyToAsync($stderrStream)
 try{$timedOut=(-not $worker.WaitForExit($TimeoutSeconds*1000))}
 catch{$worker.Refresh();if(-not $worker.HasExited){$timedOut=$true}else{throw}}
 if($timedOut){
  $code=124;$status='TIMEOUT_RECOVERY_UNKNOWN'
  try{$before=@(Get-CimInstance Win32_Process -ErrorAction Stop);$seen=@(ProcessTree $before ([int]$worker.Id));$snapshotOk=(@($seen|Where-Object {[int]$_.ProcessId -eq [int]$worker.Id}).Count -eq 1)}
  catch{$problem='Pre-stop enumeration unavailable: '+$_.Exception.Message}
  # Never use taskkill /PID: that number may now identify an unrelated process.
  # Kill() without the entireProcessTree flag targets only the captured worker.
  if($workerIdentityReady -and $snapshotOk){
   try{
    if(-not $worker.HasExited -and
       $null -ne $workerSafeHandle -and -not $workerSafeHandle.IsClosed -and
       -not $workerSafeHandle.IsInvalid -and
       $workerSafeHandle.DangerousGetHandle() -eq $workerHandle -and
       $worker.StartTime.ToUniversalTime().Ticks -eq $workerStartTicks){
      $stopAuthorized=$true
      $worker.Kill()
      $killExit=0
    }else{$problem='Worker identity unavailable; no stop requested'}
   }catch{$problem='Handle-bound worker termination failed: '+$_.Exception.Message}
  }else{$problem='Worker handle or process observation unavailable; no stop requested'}
  Start-Sleep -Seconds 2
  if($snapshotOk){
   try{
    $after=@(Get-CimInstance Win32_Process -ErrorAction Stop)
    $remaining=@($seen|Where-Object {
     $old=$_;@($after|Where-Object {$_.ProcessId -eq $old.ProcessId -and $_.CreationDate -eq $old.CreationDate}).Count -gt 0
    })
    if($remaining.Count -gt 0){$status='TIMEOUT_RESIDUAL'}
    elseif($killExit -eq 0){$status='TIMEOUT_RECOVERED'}
   }catch{$problem='Post-kill enumeration unavailable: '+$_.Exception.Message}
  }
 }else{
  $worker.Refresh();$workerExitCode=[int]$worker.ExitCode;$code=$workerExitCode
  $status=if($code -eq 0){'PASS'}elseif($code -eq 1){'FAIL'}else{'INCOMPLETE'}
 }
}catch{$problem=$_.Exception.Message;$code=4;$status='INCOMPLETE'}
finally{
 # Capture is independent from the worker's primary exit status.
 $primaryExitCode=$code;$primaryStatus=$status
 $captureProblems=[Collections.Generic.List[string]]::new()
 $capturePaths=@(
  [pscustomobject]@{name='stdout';task=$stdoutTask;stream=$stdoutStream;path=(Join-Path $evidence 'stdout.log')},
  [pscustomobject]@{name='stderr';task=$stderrTask;stream=$stderrStream;path=(Join-Path $evidence 'stderr.log')}
 )
 foreach($entry in $capturePaths){
  $task=$entry.task;$stream=$entry.stream;$streamName=$entry.name
  $expectedBytes=$null
  if($null -eq $task){
   [void]$captureProblems.Add("$streamName transfer not started")
  }else{
   try{
    if(-not $task.Wait(2000)){
     [void]$captureProblems.Add("$streamName transfer incomplete")
    }elseif($task.IsCanceled -or $task.IsFaulted){
     [void]$captureProblems.Add("$streamName transfer unsuccessful")
    }
   }catch{
    [void]$captureProblems.Add("$streamName transfer exception: "+$_.Exception.Message)
   }
  }
  if($null -eq $stream){
   [void]$captureProblems.Add("$streamName output stream missing")
  }else{
   try{
    # Flush(true) asks FileStream to flush buffered data to disk.
    $stream.Flush($true)
    $expectedBytes=[long]$stream.Length
   }catch{
    [void]$captureProblems.Add("$streamName flush failure: "+$_.Exception.Message)
   }
   try{$stream.Dispose()}
   catch{[void]$captureProblems.Add("$streamName close failure: "+$_.Exception.Message)}
  }
  if(-not(Test-Path -LiteralPath $entry.path -PathType Leaf)){
   [void]$captureProblems.Add("$streamName output file missing")
  }else{
   try{
    $readback=[IO.File]::Open($entry.path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
    try{
     $bytes=[long]$readback.Length
     # Empty stderr is valid if capture completed.
     if($null -ne $expectedBytes -and $bytes -ne $expectedBytes){
      [void]$captureProblems.Add("$streamName readback length mismatch")
     }
    }finally{$readback.Dispose()}
   }catch{
    [void]$captureProblems.Add("$streamName readback failure: "+$_.Exception.Message)
   }
  }
 }
 $decision=Resolve-Stage3BCaptureDecision -PrimaryExitCode $primaryExitCode -PrimaryStatus $primaryStatus -WorkerExitCode $workerExitCode -CaptureProblems @($captureProblems.ToArray())
 $status=$decision.Status;$code=$decision.ExitCode
 SaveJson (Join-Path $evidence 'controller-receipt.json') @{
  startedUtc=$start;endedUtc=[DateTimeOffset]::UtcNow.ToString('o')
  scope='worktree,dependency install,browser install,offline tests,diagnosis';timeoutSeconds=$TimeoutSeconds
  expectedHead=$sha;workerPid=if($worker){[int]$worker.Id}else{$null};status=$status;exitCode=$code
  primaryStatus=$decision.PrimaryStatus;primaryExitCode=$decision.PrimaryExitCode;workerExitCode=$workerExitCode
  captureStatus=$decision.CaptureStatus;captureProblems=$decision.CaptureProblems
  timeout=$timedOut;killExitCode=$killExit;processSnapshotAvailable=$snapshotOk
  workerIdentityReady=$workerIdentityReady;stopAuthorized=$stopAuthorized
  launchIdentitySource='System.Diagnostics.Process.Start creation-owned handle'
  stopMethod='Process.Kill(creation-owned worker only; no PID taskkill)';workerStartTicks=$workerStartTicks
  observed=@($seen|ForEach-Object {@{pid=$_.ProcessId;created=$_.CreationDate;name=$_.Name}})
  residual=@($remaining|ForEach-Object {@{pid=$_.ProcessId;created=$_.CreationDate;name=$_.Name}})
  error=$problem;limitation='Detached or unobserved child processes cannot be proven absent'
 }
}
Write-Output "Stage3B diagnosis: $status; evidence=$evidence"
exit $code
