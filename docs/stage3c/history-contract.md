# Stage 3-C 状態履歴の契約

対象は試作Dの扉角度0〜90度、閂位置0〜0.14 m。扉角度が0以外なら閂位置は0、閂位置が0以外なら扉角度は0でなければならない。NaN、Infinity、bool、範囲外、矛盾状態は拒否する。角度と閂位置は別操作とし、暗黙の解錠・閉鎖はしない。

## CAD文書トランザクション

`cad/stage3c/history.py` の `begin_session`、`apply_state`、`undo`、`redo`、`reset` を使う。一つの文書の有効状態と空のnative Undo/Redo履歴から開始する。無関係の既存履歴は本APIが自動削除しない。利用者が明示的に整理するか、別プロセスで保存文書を開き直す。操作前に文書の状態、Undo/Redo件数・履歴名・未確定transactionを照合する。外部編集や別の履歴との混在は拒否する。

有効な角度または閂位置の変更を一transactionとする。拒否・同一状態の再指定はtransactionを開始せず、Redoを消さない。Undo/Redoの目標状態も事前検証する。実行後は姿勢とnative件数・履歴名の移動を検証する。不意のnative結果は反対操作で復旧を確認する。復旧を証明できなければ `HISTORY_RECOVERY_FAILED` としてセッションを使用不能にし、成功扱いしない。FreeCADのtransaction上限で古い履歴が失われたときはledgerも同じ範囲へ縮める。

FreeCADではopenTransaction時点でRedoが破棄され得る。予期せぬnative実行エラーの後に姿勢が戻っても、消えたRedoまで復旧したとは保証しない。模擬試験ではこの挙動も再現する。Resetは閉鎖・解錠へのUndo可能な一操作で、履歴消去ではない。

文書保存は状態・BRepを保存する。APIのledgerは保存しない。保存・終了・別プロセス再読込後は保存状態から空の履歴で開始し、前プロセスへのUndoは約束しない。直接プロパティ編集は本APIのinterlock外であり、不正状態を作り得る。保存前後の `validate_document` と新セッション開始時の検査で検出する。標準GUIの任意のUndo操作まで本APIが介入するという意味ではない。

API根拠は [FreeCAD 1.0.0 DocumentPy実装](https://github.com/FreeCAD/FreeCAD/blob/1.0.0/src/App/DocumentPyImp.cpp) と [native transaction実装](https://github.com/FreeCAD/FreeCAD/blob/1.0.0/src/App/Document.cpp)。実ソフトでの受入は正式CIのnative原票と別プロセス再読込で判定する。

## Web履歴

`site/stage3c/history.mjs` は外から書き換えられないstate/past/futureを持ち、全状態を既存のWeb transitionで検証する。施錠・解錠・角度入力はそれぞれ一操作。アニメーションは開始から停止・終端までを一操作へまとめる。途中停止のUndoは開始姿勢、Redoは停止姿勢へ戻る。開始姿勢へ戻った単一gestureはnet-noopとし、履歴を増やさず既存Redoを保持する。

Undo後の新しい有効な変更はRedoを破棄する。不正操作・同一状態の指定はstateと両stackを変えない。保存snapshot APIはschemaと有効状態だけを保存し、他者のpast/futureをインポートしない。restoreは空の履歴で始まる。現在のページには永続保存機能を追加せず、ページ再読込は閉鎖・解錠・空履歴へ戻る。カメラの視点復帰は状態履歴に含めない。

3-Bは `lockMode=false` のままで、施錠・Undo/Redo UIや3-C履歴を利用しない。共有viewerの変更は最終候補の3-B/3-A/2-D回帰で別検証する。

## RED→GREENと証拠

`scripts/stage3c-history-red-green.py NEW_OUTPUT` は同じ反例を修正前fixtureと現実装へ適用する。旧未提出CAD履歴draftの不正Undo/Redo目標、最初の候補で見逃したnative履歴名改変、提出済み開始HEADで未実装だったWeb履歴の欠落を区別して記録する。修正前fixtureは受入対象ではなく失敗再現用である。

Pythonのtransaction double、CAD/Web状態64組の一致、Web純粋履歴試験、実ブラウザの状態/BBox復元、実FreeCADのnative transaction/BRep/保存再読込は別の検査である。doubleの成功をnative成功へ昇格させない。
