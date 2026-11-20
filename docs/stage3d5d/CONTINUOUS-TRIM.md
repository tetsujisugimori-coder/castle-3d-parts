# Stage 3-D-5: 代表区間での実BRepと連続幾何の照合

対象は GATE_Bolt / GATE_BoltGuide_Left、扉 0°、D2 第1葉 [0,35/32] mm、中点 35/64 mm。PR #46 の既存原票・モデル・判定はそのまま残す。#39 の候補モデルと #40/#41 の先行結果を設計根拠にするが、未統合のコードを取り込んだり、別カーネルでの観測をこの実行の属性に転記したりしない。

## 判定の境界

| 項目 | 検証する範囲 | 実BRepの集合に対する判定 |
| --- | --- | --- |
| P1 曲線–曲面 | FaceごとのEdge使用を採取。Planeとアフィン曲線の係数を比較し、成立時の等式をパラメータ区間全域に適用する | API係数の限定等式とnative同値は別。保存pcurveと生成pcurveの由来、カーネル内部の厳密値は未認定 |
| P2 trim・Orientation・材料側 | Face・Wire・Edge使用と端点の対応を扱う。Wireの外側・内側、向きとSolid内部を区別する | UNKNOWN。OCCTの位相・向き・有限点の観測だけでは、実Solidの占有集合全体を証明できない |
| P3 実材料の外側包含 | 既存D2と有理数閉材料候補の双方向包含を維持 | UNKNOWN。候補の境界とnative材料集合を結ぶ定理が未成立 |
| P4 実空洞の内側包含 | Guide候補の両端を抜ける閉通過セルと開空洞を別に検査 | UNKNOWN。実空洞への包摂はP3と別に独立した証明が必要 |
| P5 有限実誤差 | 厳密F64値への有理数化、単位換算と物理幾何への上界を区別 | UNKNOWN。#40の既存8項目の実誤差は未立証項をゼロに置き換えない |
| P6 配置と全状態 | 保存Shape・Document Shape・Object・親連鎖・API global、両端と中点を照合 | 全状態UNKNOWN。量の変換・式評価・再計算の全域境界は別条件 |
| P7 代表実区間の安全性 | D2名目モデルの解析下限は29/64 mm | NOT_TESTED。P3〜P6を満たさず、実CADの安全余裕ではない |

APIが報告するLine/Plane係数を二進有理数として扱った場合、合成したアフィン関数の定数項・一次係数の一致は、その定義域の全点に及ぶ。点サンプルの数を増やしても、この等式や実誤差の上界にはならない。APIのSameParameter/SameRangeフラグが別途取得できても、対応する内部公差の判定を超えた厳密等式とは扱わない。

## 固定BRepで得た結果

FreeCAD 1.0.0 / OCCT 7.8.1のAPI表示値で、Bolt 24使用、Guide 48使用の全72件が厳密アフィン係数・区間一致。内訳はLine2d 56・Line2dSegment 16。共有辺の逆方向ペア、閉路18本、内輪2本、候補材料側の開セル38件を検査した。開セルの判定はD2候補材料のものであり、OCCTのclassifierを全点で証明したものではない。

FCStd SHA-256は `c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a`、Bolt Shape.brpは `45ee396f5ac16f70d3eba4ab8ab21df86811c7757d4279ff4a37c2973d87c820`、Guide Shape.brpは `043b1fb89aad7bf3004afeb1bf62c352e47250420c4e6f6f852265125e3cf261`。保存BRepのCurve2ds表はBolt 24・Guide 48だが、個数一致だけでは各API返値の由来を証明できない。OCCTの [BRep_Tool API](https://www.occt3d.com/dev/doc/refman/html/class_b_rep___tool.html) は平面のpcurveを生成でき、保存有無の区別には明示出力が必要。このFreeCAD APIからは保存由来およびSameParameter/SameRangeのnativeフラグを確定しない。次の最小課題は、同じBRepを同じカーネルで開き、Face–Edge使用ごとの保存フラグ・パラメータ域・Locationと、ここで確立した式の入力を一対一に結ぶこと。

## 配置の確認

隔離コピーだけをDocumentとして復元し、既存の状態設定関数で 0・35/64・35/32 mm を別々に再計算する。元FCStdとコピーの前後SHAを保つ。保存ShapeはBRep自身のLocation付きで読み込む。XMLやObject Placementを同じShapeに再適用しない。親は実際に取得できたGeoFeatureGroup連鎖を合成し、API globalと照合する。空の連鎖は親階層一般の成立証明にはならない。BoltのPlacement式も採取するが、3姿勢で合うことから状態全域の一致を推定しない。

3姿勢・2部材の4比較（Object vs Shape、親合成 vs global、保存Shape vs Documentの行列、頂点集合）は、ローカルFreeCAD 1.0.0 / OCCT 7.8.1で全24項目一致した。両部材の親連鎖は観測上空。Boltの中点のX平行移動は保存時の −400 mm から −399.453125 mm、Guideは不変。採取した式は扉角0を代入して実数演算として簡約するとBoltのXだけが変位に一次で依存し、Guideは変位から独立する。ただし、全ての値でネイティブ式評価・再計算・位相が維持されることまでは、この観測からは導かない。

## 既存8項の適用

[#40 ERRORS.json](https://github.com/tetsujisugimori-coder/castle-3d-parts/blob/bbf76540baa866c32b9c35612c6738dd679d72be/docs/stage3d5c/ERRORS.json) のID・単位・合算規則を維持する。次表は今回追加できた根拠と、各実誤差を有限にできない理由。上界はいずれも未確定（null）。

| 既存ID | 証拠と限界 |
| --- | --- |
| geometry | 配向した候補境界とD2の集合比較。nativeの全点分類から候補に移す定理が未成立 |
| extraction | Curve/SurfaceのAPI係数を全区間で比較。保存pcurve由来、値取得の包絡が未確認 |
| kernel_representation | 原BRepバイトとAPIの元である版を固定。OCCT内の評価・公差の上界は未成立 |
| coordinate_transform | 3姿勢の取得行列・頂点は厳密比較。native全域合成と未観測親配置の上界なし |
| unit | 表示値を二進有理数に持ち上げた後のmm→mの1/1000は厳密。native経路を含む誤差上界ではない |
| arithmetic_rounding | 有理数による合成・比較自体には丸めなし。CAD側の評価・変換の累積誤差は未評価 |
| state_generation | 状態関数・Placement式と3姿勢を観測。連続全入力での実装の誤差上界なし |
| continuous_displacement | 解析モデルの最大変位35/64 mm。実状態の連続対応を仮定しない限り実上界にはできない |

## 再実行と証拠

Debian trixieのFreeCAD Pythonモジュールを利用する。固定ソース外に新規出力を作る。

```sh
python3 -B -m unittest discover -s cad/stage3d5d -p 'test_*.py' -v
QT_QPA_PLATFORM=offscreen python3 -X faulthandler -B cad/stage3d5d/one_slice.py <new-native-output>
QT_QPA_PLATFORM=offscreen python3 -X faulthandler -B cad/stage3d5d/placement_observation.py <new-placement-output> <new-private-scratch>
```

専用CIは実行checkout・tree・engine・終了値・標準入出力と収録SHAを残す。隔離コピーそのものは新規原票に含めない。旧HEAD 642f5320 の専用run 44755771104 と原ZIP 14638586073 は別記録。旧HEAD全体は17成功・1失敗（Stage 3-Cの stage3a ブラウザjob）であり、専用native成功から全体CI成功に読み替えない。
