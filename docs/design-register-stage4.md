# 第4層：採用履歴とCADパラメータ根拠

## 範囲と再開経緯
旧担当による244試験・修正成果は今回の環境では未回収。消失とは断定せず、その試験を今回の証拠として使わない。main 454230e4ae36e10ab49c7688358f33b7a53a42e7を独立取得し、既存191試験を再実行してから新実装した。

## 正本と履歴
`design/decisions/DEC-0001-r1.json` のように一判断の各版を独立したJSONに保存する。変更時は新しいrevisionファイルを追加しprevious、理由、状態変更根拠を記録する。旧版を消さない。HYPはID・revision・SHA256（JSONファイルの原byte）・固定Git commitとpathを記録。検証はgit showで固定原本を読むため、履歴取得が必要。取得できない場合はfail closed。

DEC-0001はHYP-0001（板塀）、DEC-0002はHYP-0002（小径木柵）を保留。両仮説は未検証C。支持、反証、競合、未確認は固定HYPから参照する。判断採用は史実の確定を意味しない。

## パラメータ契約
史料値・仮説値・試作用値を別フィールドに保管。A直接情報、B比較推定、C復元仮説、D試作設定の区別をSchemaに保持する。ただし初期ソフトウェア契約ではA/B/Cの数値入力は未対応で拒否する。次工程で根拠抽出・測定方法の契約を追加して初めて扱う。

現時点の史料値・仮説値はすべてnull。柱高2m、柱幅0.15m、柱芯間隔1.2m、5本、横木2段はcatalogの試作D。断面・配置は明示的な契約がないためnull。柱穴残存深さを柱高や根入れにしない。他城の測定値を対象城の実測値へ転用しない。

CAD出力は `design/cad-reference.json`。全入力検証後のみ生成し、reference_only、write_allowed=falseを維持。正式FreeCAD・STEP・Blender・GLBの制作はIssue #3へ分離。自動CAD適用機能なし。

## 操作・再生成
- `node scripts/design-register.mjs`：検証、既存保全、生成一致。
- `node scripts/design-register.mjs generate`：Markdownと読取JSON再生成。
- `node scripts/design-register.mjs search --site 山中城 --status held`：検索。
- `--part` / `--hypothesis` も利用可能。結果は各旧版を含む。
- `node --test tests/*.test.mjs`：正常・故障・回帰。
- `node scripts/design-evidence.mjs design-evidence`：ログとHEAD/tree/hashを収集。

既存94ファイルのSHA256と固定Git原本を照合する。既存CIは変更せず追加workflowで全試験を実行。ソフトウェア試験は原報告書・図版・遺構形態の学術的確証、実機Safari、FreeCAD実操作の代わりではない。これらはUNKNOWN / NOT_TESTED。

初期2判断のhashは検証器へ固定。将来のPRではPR_BASE_SHAに存在する全判断版をbyte比較し、削除と書換を拒否する。ローカルで将来の旧版保全まで確認する場合もPR_BASE_SHAを指定すること。コードと検証基準を同時に改変する行為に対する暗号署名やアクセス制御の代わりではなく、独立レビューを継続する。
