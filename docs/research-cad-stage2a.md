# Stage 2-A 研究根拠とCADの連携

Issue #16。基準main: `fb7b4375aaa29ecdfa9bbd1a8b2174cb6549aa74`。PR #14（検証追補）とPR #15（試作CAD）は統合済み。未解決の原資料入手・個体同定はIssue #9、正式制作の残件は#3、研究層は#4/#10/#12に残る。既存220ファイルを変更しない追加実装。

## 契約と分類

既存JSONが正本。SRC10/OBS6/VER6/CMP1/HYP2/DEC2の27レコードをGit commitから読み、path・実byte SHA256・revision（未定義はnull）・完全内容を固定する。OBSのsource参照、VERのobservation参照、CMPのmember参照、HYPのsource/target/comparison参照、DECの固定HYPを辿る。相互の競合・集合重複は証拠依存の辺ではない。依存辺は不存在・重複ID・循環を拒否。版が複数あるDEC/VERは全historyを保存し最新を表示。

VER→HYP/CMPは「検証追補の影響範囲」であり、旧HYP/DECが新VERを承認したとの意味ではない。DECの旧HYP pinは元commitから別に照合し、最新HYPに黙って差し替えない。SRCの確認、OBSの報告事実/解釈、HYPのC、DECの保留とCADのDを分離する。A/B/C/Dの既存定義は変更しない。資料の検証成功も歴史上の形態確定やCAD採用承認を意味しない。

部品IDは既存 `wooden-palisade-late-sengoku-v0`。CAD版はprototype-v1と基準commitで固定。5柱・2横木・幅4.95m。高さ2m、幅0.15m、芯間1.2m等はすべてD。7つの設計パラメータ中、数値変更を実装するのは既存CADが持つpost_height/post_width/post_center_spacing/post_count/rail_levelsの5項目。cross_section/arrangementは未確定の説明値で、変更適用対象外。

元の経路はFCStd→STEPとFCStd→中間mesh→blend→GLB。旧meshをSTEP由来とは偽らない。新しい作業コピー経路のみ、再読込したSTEPの7solidsから対応付け・メッシュ化してBlenderへ渡す。

## 候補・判断・反映

`scripts/research-cad.mjs` のproposeはbefore/after snapshot差分と明示した数値提案から不変payload/hash/候補IDを生成する。新SRC、状態/内容/版変更、撤回、DECの変化、補助抽出記録の更新を検出。根拠変更は保守的に5数値へ影響候補を通知し、値は自動補完しない。nullは保持し承認不可。before/afterの内容・hash・commitを両方保存する。

初期statusはproposed。proposed/deferred→approved/rejected/deferredを独立イベントへ追記する。既存DEC-0001/0002はheld・reference_onlyのまま。追加名前空間`DEC-WORK-*`は**D作業コピーに限定した設計変更判断**で、史実採用のDECを新設/昇格しない。actor・UTC日時・理由、候補hash・研究snapshot hash・CAD hashを固定する。

approvedだけがapplicationを作成でき、パラメータ/単位/部品/範囲/版を再検証する。現在の研究byte差・新しいsourceファイル・削除・CAD原本差は古い承認として拒否。元CADの正式適用は禁止。再生成は別の新規フォルダへ明示実行する。反映済みappliedへはcompleteコマンドだけで進め、実manifest・全出力・入力コピー・承認原票・外部auditと埋込audit・実行コード原票と現在版を照合する。任意の64桁hashを反映証拠と認めない。

承認者名付きローカルJSONとGitレビュー権限による運用。SHAは署名/本人認証ではない。コード・全履歴・全成果物を同時に書換可能な攻撃者を認証する仕組みはStage 2-B以降。書込み権限を持つ者はレビューで差分を確認する。旧run1〜4とpre-fix-appliedは反例修正の過程を残した原証拠であり、最終appliedの根拠ではない。最終根拠はrun5/6。

## 手順

Node 22+、git履歴、FreeCAD module・Blenderを使用する。元ファイルはそのまま保持する。下記の出力は新規パスを指定し、既存出力へ上書きしない。

1. `node scripts/research-cad.mjs snapshot --ref HEAD --out /tmp/current.json`
2. 以前のsnapshotと今回のsnapshot、`[{"parameter":"post_height","proposed_value":2.2,"unit":"m"}]`等の**明示的D試験値**をchanges.jsonへ保存。
3. `node scripts/research-cad.mjs propose --before old.json --after /tmp/current.json --changes changes.json --reason 'D作業コピーの試験' --out candidate.json`
4. 差分・対象・値・単位・根拠・未知事項を人が確認。`node scripts/research-cad.mjs decide --candidate candidate.json --status approved --id DEC-WORK-任意の一意ID --actor '判断者' --at 2026-11-08T13:00:00Z --reason '判断理由' --out approved.json`。却下/保留はstatusをrejected/deferredへ。
5. `node scripts/research-cad.mjs application --candidate approved.json --out application.json`
6. `python3 -B scripts/cad-regenerate.py --application application.json --output /tmp/new-cad-run`（親フォルダは存在が必要）。保存/再読込とmanifest記録まで実行。詳細はcad-regeneration-stage2a.md。
7. リポジトリ内に保存した実行結果に対して `node scripts/research-cad.mjs complete --candidate approved.json --manifest evidence/任意run/manifest.json --id DEC-WORK-任意反映ID --actor '確認者' --at 2026-11-08T13:10:00Z --reason '実結果確認' --out applied.json`。
8. rollbackは元prototype-v1を選び直す。正式原本は不変で、過去作業コピー・判断・候補は消さない。これは任意CADへの履歴編集/逆操作機能ではない。

`node scripts/research-cad.mjs trace --id SRC-0002` / `--id site/cad/palisade.glb`で順引き/逆引き。`check`で既存原本の保全検査。

## 実証と結果

- ケース1: GLB→blend→mesh→FCStd→DEC→HYP/CMP→VER/OBS/SRCの逆引きPASS。
- ケース2: 合成HYP撤回による差分と影響検出PASS。実台帳は変えず、合成snapshotは承認APIへ入れない。未承認の原本hashは不変。
- ケース3: 高さ2.0→2.2mの試験D値をDEC-WORKで明示承認し作業FCStdへ反映。史料由来ではない。
- ケース4: FreeCAD 1.0.0→STEP再読込→STEPメッシュ→Blender 4.3.2→blend/GLB再読込を実行PASS。5柱2横木、幅4.95m・奥行0.249m・高さ2.2m。
- ケース5: run5/run6のgeometry・構造・mesh一致。GLB byte hash一致。FCStd日時/ZIP時刻、STEP日時差。blendは構造一致だがbinary差の全原因未特定。バイナリ完全決定性PASSとはしない。
- ケース6: rejected/deferredではapplication拒否。既存FCStd/STEP/blend/GLBと研究を含む220ファイル不変。

ケース原票はevidence/stage2a/demo。cases.jsonのcase3〜5は実行前状態を残した原票。最終結果はdemo/applied.json、real-run/run5/manifest.json、real-run/comparison-reviewed.jsonで確認する。

## UI・テスト・CI

`node scripts/build-site.mjs && node scripts/build-research-cad.mjs`後distを配信し`/research-cad/`へ。新しい閲覧専用UIから、パラメータ・27研究記録・根拠差分・候補の5状態・承認/反映履歴・実結果を確認できる。既存Three.js GLBを埋込み、候補選択で3Dを変更しないと明記。候補確認とCLI反映を分離。新規コードを既存CAD閲覧コードに混ぜない。

`node --test`、`python3 -B tests/cad-regeneration.test.py`、`node scripts/research-cad-evidence.mjs /tmp/evidence`。CI research-cad.ymlは原本・候補・反映証拠と全回帰、Chromium/WebKit×4幅×2motionの16条件を検査する。CIは同梱の実CAD証拠を検証するだけでFreeCAD/Blenderを起動したとは主張しない。実起動は別のheadlessログ。

ローカルChromium8条件と故障5件PASS、WebKitは依存不足BLOCKED。最終16条件はCI原票で判断。CDNは非改変Three.js 0.180.0のlocal route mappingで、CDN配信経路そのものは未検証。GUI、実機Safari/VoiceOver、物理入力、完全offline、TechDraw再作図、正式CAD採用、史実寸法確定はNOT_TESTED/対象外。古い寸法注記を誤表示しないよう変更作業コピーからTechDrawを除去する。

## 次Stage 2-B

複数部品と改訂済み作業コピーを基点にした連続改訂、パラメータ別の精密影響分析、正式CAD採用の別承認契約、Git上の承認者権限/署名、変更後GLBの比較プレビュー、TechDraw再作図、GUI/実機Safari、原報告の追加照合を進める。
