# Stage 3-B 通信診断の固定HEAD実行手順

対象：Issue #43／PR #44。診断専用であり、既存Stage 3-Bの44条件契約、実CAD証明、障害対応PENDINGを置き換えない。

## 1. GitHub Actions（診断workflowがdefault branchに導入された後）

1. Actionsの `Stage 3-B transport diagnostic (bounded)` を選択し、`Run workflow` を開く。
2. `expected_head` に**診断対象Git commitの40桁SHA**を指定する。Workflow側は同SHAをcheckoutし、実checkout SHAを比較して不一致なら停止する。**そのcommitに診断スクリプトが含まれることが前提**。古いcommitに後から診断を注入する機能ではない。
3. 15分の外側job timeoutを維持。CI原artifactの名前・run・job・SHA・stderr・`results.json`・`evidence-status.json`・`transport.jsonl`・trace/PNGを確認する。
4. GitHubの再実行ボタンは**元のrunのSHA/ref**を再実行するものであり、新しい障害の任意SHAを調べる機能ではない。`workflow_dispatch`はdefault branchにworkflowが存在するまで利用できない。PRがDraftの間は下記CLI経路を利用する。

## 2. Windows PowerShell（Draft中も使える固定HEADの診断経路）

事前条件：Git、Node 22、ネットワーク経由のPlaywright/Three依存インストールが許可されていること。**診断対象HEADを受け取った承認済みrepo**で、専用の未使用worktree・依存保存先・原票保存先を準備する。既存フォルダーや証拠を上書き・削除しない。

```powershell
$sha = '<診断対象の40桁Git commit SHA>'
$repo = '<承認済みcastle-3d-parts cloneの絶対パス>'
$worktree = '<新規・未使用のworktree絶対パス>'
$deps = '<新規・未使用の依存保存先絶対パス>'
$browsers = '<新規・未使用のPlaywrightブラウザ保存先絶対パス>'
if ($sha -cnotmatch '^[0-9a-fA-F]{40}$') { throw 'invalid SHA' }
git -C $repo cat-file -e "$sha^{commit}"
if ($LASTEXITCODE -ne 0) { throw 'commit is not available locally' }
git -C $repo worktree add --detach $worktree $sha
if ($LASTEXITCODE -ne 0) { throw 'worktree creation failed' }
Set-Location $worktree
if ((git rev-parse HEAD).Trim() -cne $sha) { throw 'checkout HEAD mismatch' }
if (Test-Path 'stage3b-transport-ci') { throw 'output directory exists' }
$env:PLAYWRIGHT_BROWSERS_PATH = $browsers
npm install --prefix $deps --ignore-scripts --no-audit --no-fund playwright@1.56.1 three@0.180.0
if ($LASTEXITCODE -ne 0) { throw 'dependencies failed' }
& "$deps/node_modules/.bin/playwright.cmd" install chromium webkit
if ($LASTEXITCODE -ne 0) { throw 'browser installation failed' }
$env:PW_MODULE = "$deps/node_modules/playwright/index.mjs"
$env:THREE_DIR = "$deps/node_modules/three"
node --test scripts/stage3b-transport-evidence.test.mjs
if ($LASTEXITCODE -ne 0) { throw 'evidence gate test failed' }
$p = Start-Process -FilePath node -ArgumentList @('scripts/stage3b-transport-diagnostic.mjs','stage3b-transport-ci') -WorkingDirectory $worktree -PassThru -RedirectStandardOutput 'stage3b-transport-stdout.log' -RedirectStandardError 'stage3b-transport-stderr.log'
try { Wait-Process -Id $p.Id -Timeout 900 -ErrorAction Stop } catch { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; throw 'diagnostic timeout: inspect residual child processes' }
$p.Refresh()
if ($p.ExitCode -ne 0) { throw "diagnostic exit=$($p.ExitCode); preserve raw results" }
```

出力は`stage3b-transport-ci/`とstdout/stderr原票。15分超過時は終了状態・残留ブラウザプロセスを記録し、所有者承認なしに既存領域を削除しない。ログやZIPの上書き・再実行結果との混合はしない。別担当は保存先の原物を直接再取得し、必要な範囲でbyte/SHA/CRCを確認する。

## 3. 判定

- `PASS`：正常5と合成負対照1が期待どおり、必須trace/PNG/results/transport/identityが揃う。
- `INCOMPLETE`／exit 2：保存エラー、ファイル欠落・空、基本形式不正、ケース数不足。通信の結果を残したまま証拠の完全性を否定する。
- `FAIL`／exit 1：証拠は完備しているが通信・合成対照の期待値が不成立。
- 旧実障害が再現しなければ`NON_REPRODUCED`。原因が実測されなければ`UNKNOWN`、Issue #43は`PENDING`。

原票欠落の負対照は`node --test scripts/stage3b-transport-evidence.test.mjs`で検証。旧集計はtrace保存失敗×6でもexit 0、新集計はINCOMPLETE／exit 2にする。
