# castle-3d-parts

歴史体験Webで再利用する城郭3D部品を、城別の展示から独立して保管するリポジトリ。戦国末期から始め、年代と史料根拠を混ぜずに拡張する。

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
