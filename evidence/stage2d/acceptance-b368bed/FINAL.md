# Stage 2-D 最終受入報告

## A. 総合判定
**PARTIAL**。正式公開ビルドへの接続、候補の一時本番デプロイ、実公開URL上の自動操作と原アセット照合は成立した。実機iPhone SafariはNOT_TESTED。Draft・未マージであり、承認された検証後は元mainの公開内容へ戻す運用をとった。恒常公開の採用は依頼者の判断に残る。

## B. 限定マージ推奨
**YES（検証した汎用閲覧・ビルド統合の範囲）**。最終9 workflows、独立レビュー、実公開URL16条件が成立。史実確定、実機Safari受入、WebGLが利用できない環境での3D表示、native TechDraw SVGそのものの双方向選択まで保証する判定ではない。自動マージは行っていない。

## C. GitHub情報
- [Issue #22](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/22)
- [Draft PR #23](https://github.com/tetsujisugimori-coder/castle-3d-parts/pull/23)
- branch: `feat/stage2d-pages-integration`
- 評価対象HEAD: `b368bedd2cfa67cf6eeda53e8234ef8460aebaf2`
- tree: `9d6620277aead6021a3da070bbd41d8646916c08`
- 統合済みStage2Cの開始基準/main: `dec85b596f6b82bfd69129e4b1edbc75d182318c`
- 正式GitHub連携でcommit/refを更新。認証済みCLI pushと表現しない。
- 公開URL試験専用branch: `evidence/stage2d-public-b368bed`、workflow commit `14e114dfd958d765545fe9297d8a97153fcff4dd`。このworkflowは実装b368を固定checkoutする。試験設定commitと実装対象を混同しない。

## D. 公開確認
公開URL: https://tetsujisugimori-coder.github.io/castle-3d-parts/

1. [候補本番デプロイ42605570058](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42605570058) SUCCESS。PRプレビューではなく実本番を一時変更。mainは未変更。
2. 2026-11-09 20:03 JSTに80公開URLを通常HTTPSで取得し、79ファイルのバイトhashと識別manifestのcommit/tree/アセットhashがすべて一致。秘密の証明書例外やCDN置換なし。
3. 設定済みChromeでトップ→閲覧、ガイド、研究画面、Back/Forward/Reloadを確認。ただしWebGLがDisabledのため3D contextを生成できず、B0/B1/B2すべて安全停止。この失敗と画像を保全し、モデル表示成功とは扱わない。
4. 別経路の[実公開URL試験42606066587](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42606066587) SUCCESS。GitHub Actions Ubuntu24.04、Chromium141/WebKit26、16条件・160チェック。実公開HTTPS URLを使用しCDN無置換。3D/図面選択、57寸法、版切替、URL/再読込、研究リンクを確認。実行前後のmanifestは同一b368/tree9d。公開サイトへの故障注入は行っていない。
5. [元main復元42607054459](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42607054459)。SUCCESS。20:13 JSTの通常HTTPS再取得で、トップと旧stage2cのhashが開始前と一致し、候補manifestは元どおり404。環境設定も一時許可を削除しmain1件・tags0件へ復元。production-restoration.jsonとブラウザ記録を参照。候補の一時公開試験結果と、最終的な旧main公開状態を区別する。

## E. 実装内容
- 既存Pages workflowのbuild呼出しを合成ビルダーへ接続。Stage2Cの元rendererを再利用し、公開トップ入口・project-prefix URL・参照研究JSON・操作ガイド・識別manifestを追加。
- B0/B1/B2、3DとSVGの双方向選択、寸法差分、正面/側面/平面、スマートフォンのタブ、retryを維持/統合。
- 連動図面は**TechDraw実寸照合済みCAD投影図**。native TechDrawの正面/平面/側面SVGは別リンクで提供し、連動図面をnative出力と偽らない。native SVG自身への部品選択連携は今回未実装。
- WebKitのsame-document履歴経路を通常document navigationへ変更。副作用として改訂版変更時に視点・図面拡大率・選択がリセットされる。
- 変更対象の詳細はPR diffとdocs/stage2d/README.md。新CADモデル・研究根拠の再制作なし。

## F. 検証結果
### 自動検査
- 最終候補の9 workflowsすべてSUCCESS。
- Node425/425、portable CAD5/5。
- 最終CI merge-ref `5651e8afeb779e8d4705e64416be25a8a1ad2c16` と提出HEADはtree一致。
- ローカル公開ビルド相当:16条件160チェック＋20故障対照。
- 実公開URL:別の16条件160チェック、故障注入0。
- 375/390/765/1280 ×通常/reduced motion ×Chromium/WebKit。実入力はPlaywright mouse/keyboard・emulated touchであり実機物理操作ではない。
- 全19寸法の表示値、URL/選択control/loaded版、元データhashを各改訂で照合。
- GLB/SVG旧版、欠損部品、重複寸法、読込失敗とretry、遅延応答、context loss、SVG script/external resourceを拒否することを確認。
- 原本948パス保持:939 byte-identical、9は明示的コード/ワークフロー移行。旧bytesとbefore/after hashを保管し、第三のbytesや原本改ざんを拒否。CAD/STEP/blend/GLB/SVG・研究資料は不変。
- 公開物81ファイルのパターン検査で秘密情報/非公開Space参照の一致0。公開ビルドにFCStd/STEP/blend/PDFを追加していない。Three.js0.180.0 MITを確認。パターン検査を万能な秘密検出保証とはしない。

### 性能
各条件3回を事前固定、各engine24標本。値は同じcontext内のnavigation-to-ready壁時計値で、実機cold-loadや改善率ではない。

| 環境 | Chromium初期表示中央値 | WebKit初期表示中央値 |
|---|---:|---:|
| 最終CIローカル配信・CDN固定bytes |233ms|229.5ms|
| 実公開URL・CDN無置換 |216.5ms|261.5ms|

実公開URLの版遷移中央値はChromium246.5ms/WebKit282.5ms（各24標本、B0再表示も含む）。前後改善実験ではないので、これを高速化率に換算しない。モデル/図面のresource duration、版別値、取得可能なheap値は原JSONに保持。WebKit heapは欠測。物理メモリ/GPU使用量、入力遅延の独立計量は未検証。

### 原証拠
- [最終CI](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42604464401)
- [contracts13666763693](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42604464401/artifacts/13666763693): `c125209f1718b5d302a6b32ec52c9e94d604347d7a7fbc8c53773235b8cec4b0`
- [browser13666644183](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42604464401/artifacts/13666644183): `a7e70b02c5831a4b34ac93a8b164752070abc747426e45586029be362599bc4b`。16 PNG・20 trace ZIP。
- [実公開URL13667657898](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42606066587/artifacts/13667657898): `5c6cd4002c9718344d97dd5d4f7e3a4e83e1e7ad4900c20fb9392e89157a8a7d`。16 PNG・16 trace ZIP、前後manifest、実装git情報。
- 失敗した旧run/ZIPはacceptance-outline.mdと既存evidence/stage2d/に区別して記載。Artifactの現行expires_atは2027-02-07であり永久保存と主張しない。

## G. iPhone Safari
実機試験は**NOT_TESTED**。guide.html/READMEに12項目、機種/iOS/URL/SHA、動画・操作反復と失敗記録の手順を用意。物理ピンチ、指の精度、スクロール競合、縦横切替、バックグラウンド復帰、実機GPU/メモリは未確認。自動WebKitやviewport resizeで代用したことにしない。

## H. 残存課題
- 未解決の確認済みP1/P2は独立レビューでは見つからなかった。
- 非拡大の細い横木は約1.5CSSpx。WebKit375/765でそのままの選択失敗を観測。今回受入は実UIでpan/zoom後の通常click/emulated tap（最小8.9325CSSpx）と44pxの部品リスト代替。物理指の操作性は未受入。
- WebGL利用不可のブラウザでは全連携を安全停止。将来、2D単独閲覧を分離する改善候補はあるが今回実装しない。
- 改訂時の視点/図面条件保持は未実装。document navigationによる安全なURL履歴を優先。
- native TechDraw SVG自体の双方向選択、実機Safari、恒常公開は次判断/工程。試作Dの寸法を史実へ昇格させない。

## I. 独立レビュー
[固定HEAD独立COMMENTレビュー](https://github.com/tetsujisugimori-coder/castle-3d-parts/pull/23#pullrequestreview-5824905330)。原ZIP・hash・画像・独立build・反例と実製品履歴を確認し、限定技術PASS/限定マージYES/総合PARTIAL。独立担当は製品コードの修正を行っていない。最小fixtureの早いBackを原traceで指摘し、実製品のcontrol/URL/19寸法検査強化を提案。修正実装は提出側が行った。[実公開URL・復元の独立追補](https://github.com/tetsujisugimori-coder/castle-3d-parts/pull/23#pullrequestreview-5825093161)も投稿・読戻し完了。原ZIP/実ホスト通信/画像、復元3URLの独立HTTP、main-only復元画像を照合した。

## 個別受入 A–M
|項目|判定|範囲|
|---|---|---|
|A 正式Pages統合|PARTIAL|公開build接続・一時本番試験PASS、未マージのため恒常公開は未決|
|B 公開入口|PASS|候補一時公開中のトップ導線|
|C 3D表示・操作|PASS|ローカル相当/実公開URLの自動2engine。WebGL無効ブラウザと実機は含めない|
|D 設計図|PARTIAL|CAD投影図の連動操作PASS、native TechDrawは別リンク。native自体の双方向選択未実装|
|E 双方向選択|PASS|3Dと連動CAD投影SVG。細部は拡大/リスト代替|
|F 版切替・差分|PASS|B0/B1/B2。視点resetを明示|
|G 57寸法整合|PASS|元データ不変・全表示値/hash一致|
|H 自動ブラウザ|PASS|指定16条件をローカル相当と実公開URLで各実施|
|I 実機Safari|NOT_TESTED|手順と記録項目のみ|
|J 公開URL直接検証|PASS|80URL取得＋実公開160checks。候補検証後は旧mainへ復元|
|K CI・デプロイ|PASS|9候補workflows＋一時本番deploy＋公開URL試験。復元は別証拠|
|L 根拠/試作値|PASS|A/B/C/Dと未確認を明示、全寸法D|
|M 既存保全|PASS|939不変＋9厳密コード移行、原成果物不変|
