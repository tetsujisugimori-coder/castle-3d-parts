# Stage 4-A 第2便・操作画面増分（Refs #49 / PR #50）
## 開発用画面
リポジトリのルートで `python -m http.server 8000 --bind 127.0.0.1` を実行し、`http://127.0.0.1:8000/previews/stage4a/workshop.html` を開く。固定Three.js 0.180.0 CDNへの接続が必要。既存展示室・Pagesへの導線とビルド統合は次工程。公開していない。
- 左の部品棚で木柵/木戸を選択・追加する。新規IDは未使用のP番号、初期座標はmax(0,既存X)+6m。これは干渉を回避できる保証ではない。
- 配置リストまたは3Dクリックで対象を選択し、座標・90度回転・削除を操作する。接続点はデータ契約で検証する。使用済みポートは新規接続候補から除く。接続先と移動側を指定して整列する場合、移動側は未接続で方向が適合していなければならない。
- 手動JSON保存（テキスト表示またはダウンロード要求）、貼り付け・ファイル読込・代表配置の再読込を提供する。v2契約、カタログSHA、既存資産の照合を再利用。ファイル上限4,000,000 bytes、読込テキストは契約の上限に従う。
- UIは処理を直列化する。検証→GLB準備→同期シーン反映→データ確定の順序とし、準備・反映失敗時に前の有効設計を保持する。反映後にUI更新が失敗した場合は操作を停止して再読み込みを求める。WebGL喪失は操作停止。自動保存なし。
- 確認範囲は試作D、参照専用、アンカー一致。全体干渉・物理強度・史実・実Solid安全性・実運動・山中城への配置を認定しない。Stage 3-B HOLDと西櫓未配置を維持。
## 試験
`node --test tests/stage4a-assembly.test.mjs tests/stage4a-workshop.test.mjs tests/stage4a-glb-scene.test.mjs tests/stage4a-workshop-ui.test.mjs`
既存専用55件、編集16件、GLB10件、今回UI制御10件を対象とする。試験記述の件数であり実行成功数ではない。
ブラウザ試験候補 `node scripts/stage4a-workshop-browser.mjs` はPlaywright 1.56.1 / Three.js 0.180.0を既存試験と同様に利用。PW_MODULEとTHREE_ROOTを案件別に準備済みの依存先へ設定し、STAGE4A_OUTを案件別証拠領域へ設定する。Chromium/WebKit各8通常条件（375/390/765/1280px × 通常/Reduced）および各2故障条件。試験用HTTPサーバーはlocalhostのみで公開対象を限定し、CDNの代わりに固定ローカルThree.jsを供給する。実操作、JSON同値性、画面幅、失敗時の無効化、スクリーンショット/trace/HEAD/treeを取得する試験候補。現時点では実行未確認。物理iPhone Safari、ダウンロードの実ファイル照合、タッチ実機、独立レビュー、正式原証拠保全は未検証。
