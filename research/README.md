# 第3層：比較・復元仮説台帳

Issue #10。JSONが正本、index.mdは生成物。既存SRC10件・OBS6集合・木柵v0・第1/2層の規則と試験を変更しない。

## 構造

- comparisons/CMP-0001.json: 比較記録。CMPを新しい安定IDとする。OBSと史料箇所へ一方向参照する。
- hypotheses/HYP-0001.json 以降: 1仮説1ファイル。観察事実ではなく推定C。
- schema/: JSON Schema 2020-12の厳格な既存サブセット。未知キーは拒否。構造検査と参照・意味契約を組み合わせる。
- history/records.json: 各CMP/HYPの全文版snapshotとSHA256。現行版と一致し、過去版を削除しない。
- baseline.json: 固定main 37531176a21a8922bf23b1bc8fff1b704d9f252fの全既存blob。CIでGit実treeと照合する。

## 実行

依存追加なし。Node.js 22以上。

```sh
node scripts/hypothesis-register.mjs
node scripts/hypothesis-register.mjs --write
node scripts/hypothesis-register.mjs --kind hypothesis --site 山中城 --status unverified --unknown yes
node scripts/hypothesis-register.mjs --kind comparison --observation OBS-0006 --source SRC-0008
node --test
```

オプション: kind=all/hypothesis/comparison、site（城郭名の完全一致）、observation、source、status、unknown=yes/no。無指定は全件検証と生成一覧の一致確認。--writeは検証後のみ一覧を生成。検索でも全台帳を先に検証し、不整合を検索結果から隠さない。未確認有無はHYP.unknowns/CMP.limitationsの有無。初期記録は全件未確認あり。

## 登録と改訂

1. SRC/OBSの原記録と箇所を読み、本文/図版/報告者解釈の確認範囲を確認する。登録候補だけで確認済みにしない。
2. CMPは1比較問い1レコード。各memberの城郭は参照OBSと一致。数値はOBS measurementの値・単位・範囲・測定対象をそのまま参照snapshot化。未知はnull/空の参照と制限説明。数値が空だから0とはしない。
3. HYPは研究上の独立した問い・形状案と支持候補・不利情報・未知・適用限界を持つ。支持候補はfactかsource_interpretationを指定し、出典参照も覆う。単に未確認の項目を無理に仮説化しない。
4. 新IDは既存最大IDの次の番号。一度使ったIDは再利用しない。競合リンクは対称にするが、根拠にはしない。HYPをsupportへ入れられず、根拠循環を作れない。
5. 改訂はrevisionを1増やし、revision_historyへ日付・理由・状態・根拠を追加。過去の履歴接頭部を保持する。現在レコードの全文とcanonical JSON SHA256をhistory/records.jsonへ追加し、旧snapshotを残す。canonical/hash関数はscripts/hypothesis-register.mjsから利用できる。
6. 同じID・revisionの無言変更は現行snapshot不一致として拒否。既存mainに存在するsnapshotの改変/削除はCIが拒否。初回PR内の履歴もGit差分と独立レビューで照合する。hashは歴史的正確性や悪意ある同時改変を証明しない。
7. unverified以外の状態変更はOBS項目の根拠を必須とする。partly_supportedは支持項目との対応、counterevidence/rejectedは反証項目を必須とする。unverified/under_review/partly_supported/counterevidence/rejectedは研究評価の状態で、史実確定を表さない。確定状態は提供しない。
8. 正常・故障入力と再生成を試し、Draft PRと独立レビューへ提出する。未入手資料はIssue #9で別途追跡する。

## 初期範囲と限界

比較1件は山中城OBS-0001〜0005と田中城（熊本県和水町）OBS-0006。山中城の5集合には重複候補があり個体数を合計しない。田中城の19柱穴を19個別レコードへ展開しない。

HYP-0001は板塀支持案、HYP-0002は小径木柵との関係案。同じ対象を考える競合案で、同一時期/同一場所の構造を証明せず、城全体で異なる柵・塀が共存した可能性も排除しない。後者は小径木と土塁上柱穴の対応未確認という大きな限界がある。報告者の用途解釈を観察事実へ昇格しない。

年代は既存SRC/OBSに個々の集合の確定年代抽出契約がないためnull。対象研究の1590年前後を、すべての出土品の年代として転記しない。将来の年代採録には別の根拠・抽出契約が必要。

数値の意味契約は現行SRC-0008/L01/M01〜M05のみ。新規measurementや年代を許可するときは根拠の抽出契約と故障試験を同時に追加する。テキストの歴史学的妥当性は自動判定できず、独立レビューが必要。

原報告書の新規入手・全図版再確認・現地測量は行っていない。今回の確認は固定GitHub SRC/OBSの参照・記載内容。本文確認済みの表示は第2層の既存確認記録を継承し、本作業による新たな原資料確認ではない。CAD/STEP/GLB生成、Web UI変更、ブラウザ/実機Safariは対象外・NOT_TESTED。

状態をunverifiedへ戻す場合も、状態変更がある改訂には構造化根拠を必要とする。counterevidence/rejectedの改訂根拠は反証候補へ対応し、partly_supportedは対象OBSのfactを少なくとも1件支持候補に含む。これは歴史的正しさの自動判定ではなく、他城類例だけの昇格や根拠欠落を防ぐ最低限の契約。過去snapshotも参照の実在を検査する。史料訂正で参照先が廃止される場合は、IDを削除せず廃止を版として残す方針を別途設計する。
