# 簡易木戸 Stage 3-A

Issue #24。書込み先は castle-3d-parts のみ。既存木柵と独立した試作D部品 `GATE-SIMPLE-01` を追加する。歴史的な存在・構造・寸法は未認定であり、特定城への配置は実施しない。

## 成果物と名前空間

- CAD仕様: `cad/stage3a/spec.json`（メートル、Z-up）
- CAD正本: `cad/stage3a/generated/{B0,B1,B2}/assembly.FCStd`
- 変換物: 同ディレクトリのSTEP、blend、GLB
- Native TechDraw: `native-front/top/side/pivot/connection.svg`
- Web選択用CAD投影: `drawing.svg` と `link-manifest.json`
- 設計境界: [research-boundary.json](research-boundary.json)

木戸B0/B1/B2は0/45/90度の姿勢識別。木柵の改訂版B0/B1/B2とは別物。CADのmmからメートルへの変換、Z-upからGLBのY-upへの変換を各検証器で照合する。

## 実行

既存のFreeCAD/PySide2/TechDrawとBlenderが必要。実行前に現在の `cad/stage3a/run.py` の引数を確認し、新規出力先を指定する。既存原本や旧証拠を出力先にしてはならない。

- `python3 cad/stage3a/check.py`: 保存済み原成果物・hash・ID・実行記録のportable照合。ネイティブアプリを実行した代替にはならない。
- `node --test`: 既存＋追加契約と負対照。
- `node scripts/build-stage3a-site.mjs`: Stage 2-Dサイトを合成して新部品の入口を付加する候補ビルド。旧ソースを変更しない。
- `node scripts/stage3a-browser.mjs`: Chromium/WebKitの16表示条件、故障対照、既存木柵3版を確認する。既存ブラウザ資源の場所はスクリプト環境変数を参照。

## 公開境界

本PRでは既存Pages workflowのビルド命令を変更していない。候補サイトは新しいビルダーと専用CIで検証するが、現行本番への恒常接続・公開は実施しない。最終的に公開するには、新ビルダーへの接続を別の承認判断として扱う。CAD原本、研究台帳、旧証拠974パスの不変検査を継続する。

## 検証を区別する

FreeCADの実API・Qtオフスクリーン実行、STEP再読込、Blender background再読込、ブラウザの自動操作、手動GUI操作、実機iPhoneは別の母数。実行していないGUI手操作・物理入力を成功とは記録しない。3姿勢の干渉照合は静的検査であり、扉の支持強度や全角度の安全性を証明しない。

## 独立レビューで修正した点

角度パラメータを30°へ変更した際、初期実装は扉の原点だけ移動し回転が追従しなかった。Rotation.Angleも式連動し、各初期姿勢から30°変更・保存・再読込・元姿勢復帰を確認する。さらにportable監査が姿勢配列空でも成功を返す問題を修正し、3姿勢と角度を厳密検査する。

Native接続図には既存木柵B0の端柱と上段横木を参照形状として含める。これらは図面用であり、7部材の木戸STEP/GLBへの混入はしない。3Dの組立表示は別途、既存木柵GLBを再利用する。

Native寸法の数値だけでなく線の方向・位置も独立目視で監査し、原点からX方向だけの補助線を廃止した。柱・扉高はZ方向、扉幅・厚みは姿勢角に追従する実部材端点、開口は左右内端、軸半径は中心から円周、接続材長は実両端に式連動する。図枠の尺度表記は1:16.667へ修正した。

初期接続材は柱と線接触だけだったため、長さを0.30mから0.45mへ変更し、外端±1.05mを維持したまま柱前面に0.0126m²の面接触を設けた。これは幾何学的接触の検証であり、締結具・強度・現実の施工の立証ではない。

`source_commit`は原木柵を固定した開始mainを表す。新規実装の検証対象HEAD/treeはCI・ブラウザ原記録で別に示す。原CADの由来と新規検証のcommitを混同しない。
