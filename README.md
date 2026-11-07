# castle-3d-parts

歴史体験Webで再利用する城郭3D部品を、城別の展示から独立して保管するリポジトリ。戦国末期から始め、年代と史料根拠を混ぜずに拡張する。

## 制作ツールと役割

**方針：CADを原本とし、BlenderでWeb展示用のモデルに仕上げる。** ソフトの利用可能性は八兵衛の2026年10月30日までの確認記録に基づく。作業時の再確認が必要。

| 担当 | ソフト | 成果物・目的 |
| --- | --- | --- |
| 史料・根拠 | 根拠JSON | 実在・形状寸法・他城類例・演出を分離 |
| 寸法とCAD原本 | FreeCAD（確認例 1.0.0） | FCStd、TechDraw設計図、STEP |
| 造形・質感 | Blender（確認例 4.3.2） | blend、最適化されたGLB |
| 補助的な形状生成 | OpenSCAD（確認例 2021.01） | パラメトリック形状の実験 |
| 地形と座標 | QGIS（確認例 3.40.6） | 地形、位置・尺度の照合 |
| 展示 | Three.js / GitHub Pages | GLB閲覧、寸法表示、スマートフォン操作 |
| 将来の体験 | Godot（確認例 4.6.3） | インタラクティブ体験を必要に応じて検討 |
| 補助制作 | GIMP / Inkscape | テクスチャ、図・説明素材 |

基本経路：**史料根拠JSON → FreeCAD（CAD・STEP）→ Blender（GLB）→ Three.js（Web）**。QGISは地形・地理的な配置に使用する。各段階は寸法一致と再読込を確認し、未検証なら未検証と記録する。ソフト名・版は標準経路の説明であり、特定バージョンに固定する要件ではない。

今回の木柵 v0 は**Three.jsが直接形状を生成する暫定試作**であり、FreeCAD原本・Blender作成GLBと一致した正式部品ではない。これを段階的にCAD起点へ移行する。詳細は [AGENTS.md](AGENTS.md) を参照。

## Stage 0: 木柵 v0（操作・配信の試作）

- GitHub Pagesで回転・拡大、柱数・高さ・間隔・横木数の変更ができるThree.js展示。
- 初期値は5本・柱高2m・柱芯1.2m・柱幅0.15m・横木2段。**すべて仮寸法**。
- 根拠データ: catalog/wooden-palisade-v0.json。存在根拠／形状寸法／他城類例／演出補完を分離。
- FreeCAD用マクロ: cad/build_palisade.FCMacro。FreeCAD上で実行すれば .FCStd と .step を generated/ に生成する設計。**Stage 0では実行未検証**。
- Web展示はThree.jsでモデルを動的生成。現時点のPagesはFreeCAD/Blender/GLBの実データを読み込んでいない。

## 開発・確認

Node.js 22以上があれば追加パッケージ不要。

1. node --test
2. node scripts/build-site.mjs
3. Pythonの簡易HTTPサーバー等で dist/ を配信し、ブラウザで表示

Pages配信は .github/workflows/pages.yml で、mainに統合した後にActionsがdistをアップロードする。PRでは .github/workflows/checks.yml が単体テスト・配信素材生成を確認する。Three.jsは固定バージョンのCDNに依存するため、オフライン表示は未対応。

## 今回の受入範囲

- [x] メートル基準のパラメータと全幅計算
- [x] 履歴・根拠の分類と未確認表記
- [x] ブラウザ3D操作、レスポンシブ表示の実装
- [x] Node.jsの自動テスト記述
- [ ] 実ブラウザでの表示確認（PC/iPhone Safari）
- [ ] FreeCADマクロ実行での原本・STEP確認
- [ ] Blenderによる制作とGLBエクスポート
- [ ] QGIS地形との整合・山中城への実寸配置
- [ ] 歴史的な寸法・形状の確証

GitHub運用はIssue → branch → Draft PR → 独立レビュー → merge。各城は将来、使用した部品の固定バージョンを記録する。

## 関連

初回実装計画: Issue #1。

## 城郭研究史料台帳（研究第1期）

[史料一覧](sources/index.md) と [登録手順・状態の定義](sources/README.md) を参照。初期9候補を10レコードに整理し、版・分冊、入手・本文・図版の確認を分離する。第1層だけの実装で、遺構・仮説・3D部品の自動生成は行わない。既存木柵の歴史的妥当性を確定するものでもない。

- `node scripts/source-register.mjs` : 台帳と生成一覧の整合性検査
- `node scripts/source-register.mjs --write` : JSONからMarkdown一覧を更新
- `node scripts/source-register.mjs --site=山中城` : 城郭別JSONの抽出
- `node --test` : 既存試作と台帳の正対照・負対照

調査結果・原本未入手・版差は [第1期記録](docs/source-register-stage1.md) に記載。PDFや図版は再配布しない。

## 城郭研究 遺構・遺物観察台帳（第2層）

[観察一覧](observations/index.md) / [登録・CLI抽出](observations/README.md) / [設計と確認範囲](docs/observation-register-stage2.md)。初期6集合記録。第1層10資料を参照し、報告事項と報告者解釈、出土場所と元設置候補を分離する。研究確認はPARTIALで、木柵v0やCAD寸法の史実性を承認しない。`node scripts/observation-register.mjs` で検証する。第1層資料の「第2層未実装」は当時の記録として保持する。
