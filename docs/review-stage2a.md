# Stage 2-A 独立レビュー

担当: 実装担当とは別の独立レビューワー。実装コード修正・GitHub投稿は実施していない。
対象原本: main `fb7b4375aaa29ecdfa9bbd1a8b2174cb6549aa74`。
依頼書: ユーザー添付「貼り付けたテキスト(20261108-115740).txt」を直接読んで確認。AGENTS.md、既存DEC・CAD生成元、新規承認・変換コードを照合。

## 判定

独立安全レビュー: PASS（限定されたD作業コピー経路）。全体受入・限定マージ推奨は最終HEADのCI/UI検査と併せて判断する。公開・Draft解除・mergeは本レビューの承認外。

## 独立検証結果

- mainの全220追跡ファイルをgit showの原bytesと直接照合し、差分0。baseline.json自身の申告だけには依存していない。`evidence/stage2a/independent/artifact-check.json`。
- 提出run1/run2の全manifest記載出力hashを実ファイルから再計算して一致。input.FCStdはmainのFCStdと一致。
- 独立担当自身が同じ承認済みapplicationから3回目を実行。実FreeCAD 1.0.0とBlender 4.3.2のheadless/background実行、FCStd/STEP/blend/GLBの保存・再読込がPASS。原本不変。`independent/real-run/`。
- run1との比較でFreeCAD/Blender audit、STEP由来meshはJSON一致。寸法4.95 × 0.249 × 2.2 m、柱5・横木2、7mesh・84triangle。GLBはbyte一致。`independent/comparison.json`。
- FCStd差はDocument.xml LastModifiedDateとZIP時刻、STEP差は時刻正規化後一致。blend差の正確な内部フィールドは未特定で、構造一致のみ主張する。
- 既存DECはheld、cad.write_allowed=false。作業コピーのDEC-WORK承認とは別で、正式採用・史料実測値への昇格はない。初期CADはD値、4.95 m・柱5・横木2。
- 独立反例: 未承認/保留/却下apply、循環・欠落参照、part/basis/decision IDを改変し再hash、承認後数値改変と再hash、根拠偽装と再hash、単位不一致、新規/改変/削除研究資料、原GLB改変は拒否。`counterexamples.mjs` / `red.json` / `green.json`。
- engine試験40件とrunner負例8件を独立再実行しPASS（実行時のコード段階。最終CIとは別）。`runner-tests.log`。

## 発見事項と同一反例の修正前後

1. P2: 実manifestなしで適当な64桁hashだけを渡すとappliedになった。独立REDを保存し主担当へ通知。修正でdecide(applied)を拒否、completeによる実成果物検証へ変更。同一反例はGREEN。修正前ソースは`independent/red-source/`、ソースhashはred/green.jsonに記録。
2. P2: complete導入後も、input.FCStdを文字列へ破壊、manifest.application_sha256をゼロへ変更、manifest内FreeCAD寸法を[1,1,1]へ変更の各ケースがappliedになった。`manifest-counterexamples.mjs` / `manifest-red.json`。修正前ソースは`manifest-red-source/`。同じ3破壊操作を新しいrun3で再実行し、OUTPUT_HASH / APPLICATION_FILE_HASH / AUDIT_MISMATCHで拒否（`manifest-green.json`）。旧run1/2は原票application欠落のため新しいcompleteでは拒否され、元証拠として保全。

3. 追加検査: manifest.source_scriptsを任意5パスとゼロhashへ変更するとcompleteが受理。`source-counterexample.mjs` / `source-red.json` / `source-red-source/`。期待5パスと現在コードbytesへの照合が追加され、同一反例はEXECUTION_SOURCESで拒否（`source-green.json`）。コードが変わると旧runによるcompleteも拒否する。

- 改修後runnerでも独立再生成を追加実行しPASS（`real-run-final/`）。その後実行元hash照合が強化されたため、この旧runは現在のcomplete用証拠には使用しない。最終コードの再実行は`real-run-verified/`。

## 境界・未検証

- reviewer名付きローカルJSONとGitレビュー権限を承認の運用境界とする。hashは署名ではなく、全履歴・成果物・コードを同時に改ざんできる攻撃者の本人認証は提供しない。
- GUI操作、TechDrawの修正後図面、実機iPhone Safariは本レビューではNOT_TESTED。変更後TechDrawは省略され、寸法測定と混同していない。
- UIブラウザ検査、GitHub CI、Draft PRの最終HEADは別証拠を参照する。ここで成功を先取りしない。
- 新規ファイル中心のレビューであり、過去の全研究内容の学術的確定や全ソフトの安全監査ではない。

## 最終ローカル再検証

最終検査対象engine SHA-256: `8e731948efc3d74fea1e51c335d72ad455467182eb08d806430c1ad31608c64d`。
独立担当の最終実生成 `independent/real-run-verified/` はPASS。正当な実manifestからcompleteがappliedとなる正常系も確認（`complete-positive.json`）。同じ最終実生成を破壊した3反例はすべて拒否（`manifest-green-final.json`）。構造比較もPASS（`comparison-final.json`）。

確認した修正対象の未解決P1/P2はなし。コードが今後変わった場合は、この記録を新しいHEADの検証済み証拠に流用せず、対象差分と実行元hashを再確認する。原本・未確認史料・GUI等の制限は上記のとおり。
