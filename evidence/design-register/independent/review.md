# 第4層・独立レビュー

2026-11-08。実装担当とは別の担当がコード・原台帳を読み、独自反例と回帰を実行した。旧担当244試験成果は未回収で、本判定には使用していない。

## 判定

総合PARTIAL。現在の初期D-only/reference_only範囲の技術レビューPASS。未解決P1/P2なし。最終GitHub CI・原artifactの独立照合はこのレビュー時点ではNOT_TESTEDであり、マージ判定の前提として別途必要。

## 独立反例と修正

P2：validate(rows)が原本のファイルhashだけを検査し、渡された旧版の理由・担当・時刻変更を許容。cadReadも改変済み初版を出力した。また検証の第二引数で空manifestを渡すと旧版削除を受理した。

同一controls.mjsの5反例を修正前・後で再実行。修正前は5件すべて誤受理、修正後はHISTORY_INPUT_MUTATEDまたはBASELINE_OVERRIDE_FORBIDDENで5件すべて拒否。旧検証器・Schema・baseline・台帳2件をbyte snapshot保存。replay.pyは隔離コピーでそのセットを復元しRED→GREENを再現する。

historical_value/hypothesis_valueの値昇格は当初Schema TYPEに阻まれ、狙った意味検査に未到達だった。修正後は両方UNCONFIRMED_VALUEで拒否することを独立確認。

別の隔離コピーでon-disk manifestと初版全部を削除したが、INITIAL_MANIFEST_CHANGEDで拒否。disk-history-red.jsonという名前だが記録内容は修正後拒否結果であり、失敗/誤受理を示すものではない。

更に試験専用ローカルcommitへrevision2を追加した後、その版を削除。PR_BASE_SHAをそのcommitに固定しpreserve()を実行するとPR_HISTORY_LOSTで拒否。後続版保全には正しいPR_BASE_SHAが必要。reference API単体だけを長期履歴監査の代替にしない。

## 最終実行

- 全220試験：220 PASS、0 FAIL、0 skip。
- 検証CLI：PASS。生成一覧・CAD読取JSON一致。
- 固定main 454230e4ae36e10ab49c7688358f33b7a53a42e7の既存94ファイル保全試験PASS。
- 検証器SHA256：a70af94ab44c03d7f8d7720fc99a0ab8409ce5b68287a73d080daf7576ce2eed
- Schema SHA256：82ff188c395e317f6e9a6708379a83b8cbe6f8cb6e301a408c092cb8d3eac169

## 制限・次工程

A/B/C/Dの根拠分類は定義済みだが、現在の値検証は既存v0のDだけに限定。A/B/Cの実値登録、承認されたCAD適用は未実装であり、この範囲を全面完成とは判定しない。史料値・仮説値はnull、両仮説は保留。原報告書・図版の独立照合、歴史的形態の確証、実機Safari・正式CAD実操作は未実施。生成物に史実確定やCAD許可を示す出力はない。

## 再実行

`python3 evidence/design-register/independent/replay.py` は隔離ローカルcloneを作り、旧版セットと同一反例、現行版、後続履歴削除を実行する。外部GitHubへのpushや原作業資料の改変は行わない。旧版REDは意図的exit1、現行GREENはexit0。再現結果はreplay-results.json。

## 提出後CIの再レビュー

初回提出d56f93dのdesign/hypothesis CI成功に対し、既存prototype CIが浅いcheckoutで固定Git原本を参照できず220中23FAILとなった。原ZIPを独立取得して確認。テストをskipせず、既知commitのHYP原byteと全baseline hashを検証器にpinする限定fallbackへ修正した。Git原本取得可能時の照合は維持する。

独立したGit履歴なしコピーで修正版CLIはPASS。固定HYP snapshotを1文字改変するとHYP_SNAPSHOT_PIN、exit1となった。shallow-results.jsonに保存。後続HYP/commitの無制限fallbackを認めるものではない。新HEADのCI再成功と原artifact照合はこの追記時点では未確認。
