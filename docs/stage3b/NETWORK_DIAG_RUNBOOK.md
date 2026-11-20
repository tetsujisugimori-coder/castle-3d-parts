# Stage 3-B 通信診断：固定HEADでの実行と原票保全

Issue #43／PR #44専用。診断基盤のPASSは旧通信障害の解決ではない。障害PENDING／根本原因UNKNOWN、元PR #40 HOLDを維持する。

## GitHub Actions：default branchへの導入後

1. `Stage 3-B transport diagnostic (bounded)` の `Run workflow` で `expected_head` に対象Git commitの**40桁SHA**を指定する。
2. 実際のcheckout SHAを `git rev-parse HEAD` から取得し、手動時は指定SHAと比較。artifact名に**実checkout SHA**とrun ID／attemptを含める。起動refの `github.sha` を対象コミットと誤認しない。
3. workflowの外側15分上限、依存バージョン、専用原票（identity/results/evidence-status/transport/trace/PNG）、GitHub artifact digestを確認する。
4. 手動workflowはdefault branchへの導入後だけ使える。指定commitに診断ソースがない場合は失敗する。既存runの再実行は新しいSHAの選択ではない。

## Windows PowerShell 7：Draft中の固定SHA診断

`scripts/stage3b-transport-cli.ps1` を**診断ランナーを含む承認済みcheckout**から実行する。Git・Node 22・PowerShell 7、Windowsの `Get-CimInstance` を必要とする。入力はすべて絶対パス。Worktree、依存領域、ブラウザ領域、証拠領域には**存在しない新規パス**を指定する。既存領域を上書き・削除しない。

```powershell
$params = @{
  ExpectedHead = '<40桁のGit commit SHA>'
  RepositoryPath = '<承認済みリポジトリの絶対パス>'
  WorktreePath = '<新規のworktree絶対パス>'
  DependenciesPath = '<新規の依存保存先絶対パス>'
  BrowsersPath = '<新規のブラウザ保存先絶対パス>'
  EvidenceRoot = '<新規の原票保存先絶対パス>'
  TimeoutSeconds = 900
}
& './scripts/stage3b-transport-cli.ps1' @params
```

controllerは別のPowerShell workerを起動し、workerの開始から**worktree作成、npm依存インストール、ブラウザインストール、P2証拠負対照、診断までを単一の900秒上限で監督**する。外側準備や既存repoの取得は時間上限の対象外。ユーザーが許可した領域以外に保存しない。

タイムアウト時は `System.Diagnostics.Process.Start` で生成時から関連付けられたプロセスハンドルを保持し、起動後にPIDを使ってハンドルを探し直さない。生成時のハンドル取得に失敗した場合、または停止直前の確認ができない場合は自動停止を要求しない。生成時のハンドルと開始時刻、停止直前の観測によって同一性を確認できる場合に限り、保持したworkerオブジェクトの `Kill()` で**元workerだけ**の停止を試みる。PID番号だけを指定する `taskkill` は使用しない。同一性が確認不能なら停止要求を出さず `TIMEOUT_RECOVERY_UNKNOWN` と記録する。子孫は強制停止しないため、残留プロセスの不在を保証しない。回収状態は `TIMEOUT_RECOVERED` / `TIMEOUT_RESIDUAL` / `TIMEOUT_RECOVERY_UNKNOWN` に区別し、すべてexit 124。事前・事後の列挙不能は回収不明であり、**親子関係を離脱した未知プロセスの不在まで保証しない**。確認できない場合にPASSとしない。

`EvidenceRoot`にcontroller/worker receipts、worker stdout/stderr、終了時の収録判定と、`diagnostic/`の原結果を保存する。通信判定PASSでも必須trace/PNG・結果記録欠落なら `INCOMPLETE`／exit 2。加えて**Windows CLIのstdout/stderrの収録をworker結果とは別に判定**し、転送未完・例外・flush失敗・ファイル欠損・再取得不一致の場合は `captureStatus=INCOMPLETE` として、通常のworker終了0でも最終`INCOMPLETE`／exit 2にする。正常に0 bytesで終わるstderrは欠落ではない。`controller-receipt.json` に一次`workerExitCode`・`primaryStatus`・`primaryExitCode`と最終判定・収録障害を分離して保持する。タイムアウトのexit 124と準備失敗exit 4は維持し、収録不足は別欄で記録する。証拠完備の期待値違反はFAIL／exit 1。

**CLIのWindows実機での15分超過・子孫回収の実証はNOT_TESTED**。workflowではPowerShell構文解析を確認できるが、実回収を証明したとは扱わない。必要になった時点で承認済み領域の合成ケースを使い、原ログと残留プロセスを別途照合する。

## 受入境界

初回CIの履歴FAILと同一HEAD再実行PASS、合成故障は分離する。元原ZIPを上書きせず、再発時はブラウザ`requestfailed/response/pageerror`とNode`request/connection/clientError/socket`を時系列照合する。
