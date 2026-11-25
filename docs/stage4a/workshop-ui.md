# Stage 4-A 第2便・操作画面増分（Refs #49 / PR #50）
## 現行の確認範囲
正式CIの実行版と受入判定は [PR #50](https://github.com/tetsujisugimori-coder/castle-3d-parts/pull/50) に記録する。工房は試作Dの参照模型を扱う開発用画面で、第4工程で予定する展示室からの入口とビルド統合は対象外。
## 開発用画面
リポジトリのルートで `python -m http.server 8000 --bind 127.0.0.1` を実行し、`http://127.0.0.1:8000/previews/stage4a/workshop.html` を開く。固定Three.js 0.180.0 CDNへの接続が必要。既存展示室・Pagesへの導線とビルド統合は次工程。公開していない。
- 左の部品棚で木柵/木戸を選択・追加する。新規IDは未使用のP番号、初期座標はmax(0,既存X)+6m。これは干渉を回避できる保証ではない。
- 配置リストまたは3Dクリックで対象を選択し、座標・90度回転・削除を操作する。接続点はデータ契約で検証する。使用済みポートは新規接続候補から除く。接続先と移動側を指定して整列する場合、移動側は未接続で方向が適合していなければならない。
- 手動JSON保存（テキスト表示またはダウンロード要求）、貼り付け・ファイル読込・代表配置の再読込を提供する。v2契約、カタログSHA、既存資産の照合を再利用。ファイル上限4,000,000 bytes、読込テキストは契約の上限に従う。
- UIは処理を直列化する。検証→GLB準備→同期シーン反映→データ確定の順序とし、準備・反映失敗時に前の有効設計を保持する。反映後にUI更新が失敗した場合は操作を停止して再読み込みを求める。WebGL喪失は操作停止。自動保存なし。
- 確認範囲は試作D、参照専用、アンカー一致。全体干渉・物理強度・史実・実Solid安全性・実運動・山中城への配置を認定しない。Stage 3-B HOLDと西櫓未配置を維持。
## 試験
専用Node試験は `node --test tests/stage4a-assembly.test.mjs tests/stage4a-workshop.test.mjs tests/stage4a-glb-scene.test.mjs tests/stage4a-workshop-ui.test.mjs` で実行する。契約55・編集16・GLB10・UI制御10の計91件。

工房の正式CIは Playwright 1.56.1 / Three.js 0.180.0 で Chromium・WebKit を実行する。各ブラウザの条件は、375/390/765/1280px × 通常/Reduced の8件、375px通常・390px Reduced のタッチ相当2件、木戸GLBの欠落・不正バイトの故障2件。正式CIの設定は `.github/workflows/stage4a-workshop.yml`。ローカル実行では `PW_MODULE` と `THREE_ROOT` を固定依存先、`STAGE4A_OUT` を証拠出力先に設定して `node scripts/stage4a-workshop-browser.mjs` を実行する。

- 通常条件では編集と接続、キーボードによるF01→G01の選択、3Dマウス選択、クリップボードからのJSON貼付けとファイル読込、ダウンロードしたJSONの実バイト、狭幅表示を確認する。
- タッチ相当条件はPlaywrightのタップを使い、各対象への信頼済み `touchstart/end` と `pointerType=touch` の `pointerdown/up`、3D選択と保存データを確認する。最小再現の有効・無効対照とマウス対照を別に記録する。WebKit WPEではタップが届いても `navigator.maxTouchPoints` が0になるため、この値は観測情報として記録する。
- 故障対照は欠落とSHA不一致を理由別に確認し、故障解除後に同じページを再読込して3配置・21メッシュ・2接続と保存同値性まで検査する。
- 物理iPhone Safari・実機タッチ・ピンチ・連続ドラッグはNOT_TESTED。Stage 3-B HOLD、西櫓未配置、実Solid安全性UNKNOWN、代表実運動NOT_TESTED。
