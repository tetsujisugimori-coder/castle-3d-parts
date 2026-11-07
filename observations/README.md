# 遺構・遺物観察台帳（第2層）

[生成一覧](index.md) / [JSON Schema](schema/observation.schema.json) / [設計・検証](../docs/observation-register-stage2.md) / [第1層](../sources/index.md)

JSONが正本。`records/OBS-NNNN.json` を1観察対象または1資料上識別可能な集合に対応させる。IDは削除・再利用せず、城名や年代から独立する。第1層の史料ID・箇所IDを参照し、本文や図版の全体照合を意味しない。

## 記録の境界

- `facts`：資料で報告された観察事項の要約／必要最小限の引用。歴史的真実を自動的に確証しない。
- `source_interpretations`：資料の著者・発行者に帰属させた解釈。記載事実と分離する。
- 復元仮説・CAD表示用の仮寸法は登録しない。将来の第3・4層がOBS IDを参照する。
- `position.reported_location` は資料上の位置、`findspot` は出土位置。`original_installation` は原報告者の解釈IDを必要とする。分からなければnull。
- 不明な単値はnull、まだ得ていない測定値群は空配列。unknownsに不足を記す。0や架空の文字列で補わない。
- 観察レコード件数を遺構・遺物数として加算しない。同じ柱穴への別資料の言及は同一・重複候補として保持する。

## 集合と個別

初期6件はすべてcollection。田中城P1〜P19は集合の`original_ids`に保持し、19個別JSONへ機械展開しない。個別化には原資料の識別子と参照が必要。実読した図の識別子集合をextractions.jsonに固定し、数量や普通名詞の本文一致を識別子とは認めない。`member_of`で集合へつなげる。既存集合レコードは消さない。

`same_object_candidate`、`overlap_candidate` は未確定の関連で、統合・数量確定を行わない。異なる城郭間は `comparison` のみ。比較資料の値を対象城郭の測定値へ転記しない。

## 参照と確認

`source_id + location_id`、第1層のlocator全文、locatorオブジェクトSHA-256、URL・取得PDF SHAを固定する。頁は印刷ページと1始まりPDFページを別管理。図と表の番号も別。第1層の本文・図版確認を超える昇格は検査器で拒否する。

本文 `checked` は記載した箇所の部分確認、図 `checked` は指定図のみ。第1層台帳を読んだだけの場合は `source_register_only` + `not_checked` とし、直接確認へ昇格させない。現地確認や考古学的証明ではない。

第1層の出典箇所を正当に更新した際は、旧snapshotとの不一致を一旦停止理由として、根拠を再確認してから明示的に更新する。自動追従しない。新たな位置・識別子・報告値が第1層の箇所要約に含まれない場合も、まず第1層の箇所契約を別レビューで整える。検査器を通すために架空の要約へ変更しない。

## 数値

`basis`はreported（報告記載値）、measured（確認方法を伴う独自測定）、source_estimate（出典付き報告者推定と解釈ID）を区別。初期値はすべてreported。この段階で受理するのもreportedのみ。measured/source_estimateは識別語を予約するが、証拠契約が追加レビューされるまで受入不可。復元者の推定は別層。

`statistic`は単値・範囲・平均・最大・最小。範囲ではvalue=null、lower/upperに値を持つ。単値ではlower/upper=null。元値・元単位・原表記を必ず残す。長さはmm/cm/m、数量はcount（正整数）で、長さと数量の変換は禁止。数量や長さ0は今回対象では不正値として拒否。

報告値は `extractions.json` の実読・レビューした数値契約に結合する。測定対象・統計・元単位・元値・原表記を一組として照合し、同じ箇所の別数値へのすり替えを拒否する。契約自身の内容の正しさは独立した原資料確認が必要。測定値・報告者推定値の受入契約はまだ未実装で、basisを変えて契約を迂回することは拒否する。

## コマンド

追加パッケージ不要、Node 22以上。

```sh
node scripts/observation-register.mjs --write
node scripts/observation-register.mjs
node scripts/observation-register.mjs --site=山中城 --kind=postholes
node scripts/observation-register.mjs --scope=collection --source=SRC-0008
node scripts/observation-register.mjs --status=partial_checked --unknowns=true
node --test
node scripts/build-site.mjs
```

フィルターは完全一致・AND。未知のオプションはエラー、該当なしは空配列。`--write`は全件の一覧だけを生成し、抽出結果で正本を切り詰めない。フィルターだけでも先に全台帳・全参照・生成一覧を検証する。

## 追加手順

1. main、Issue/PR、既存SRC/OBSを検索して重複を検討する。
2. 出典箇所を実読。本文・図・表、引用と解釈を分ける。
3. 集合／個別の同定範囲を決める。未同定を架空の個体へ分割しない。
4. JSONを追加し、出典snapshot、元数値、未確認、候補関連を残す。
5. 一覧を生成し正負試験、保全試験、CIを実施する。
6. 別担当の出典・コードレビューを経てDraft提出する。ソフトウェア検査と研究上の確証を別判定する。

PDF・図版は再配布せず公式リンクを管理する。Web管理画面、GIS座標付与、CAD生成、自動マージ、史実判定は実装していない。
