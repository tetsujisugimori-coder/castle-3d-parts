# Stage 3-D-5D：Guide Face 0分類器の誤差上界を分離する

## 検証対象と意味
固定Guide Face 0（負X端面、外輪4辺・内輪4辺、保存pcurve8使用）に限り、同じ固定BRepと以前のOCCT 7.8.1正式原票を再利用する。分類点を増やさず、5点の既存のIN/OUT/ONと誤差予算を別々に評価する。

「入力値をbinary64へ保存する際の誤差」「理想的なリング領域に対する座標変動への頑健性」「OCCTの交差判定・公差を通じた分類結果の全点誤差」は別の対象である。前二者について条件付きの厳密数値上界を出し、最後は十分な根拠がなければUNKNOWNとする。

## 取得済みの数値とOCCTソース
- Face 0の支持Planeの実効枠は `S(u,v)=(-200,-130-v,990+u) mm`。UV外輪 `R=[0,60]×[-130,0]`、穴の開内部 `H=(9,51)×(-36,-14)`、閉Face `D=R\H`。負X端面の8辺は保存pcurveと同一使用で対応し、D2端面の全区画同値性は既存証拠で確認済み。
- [正式原票 #14687880897](https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/44855960971/artifacts/14687880897)の `native-face0.stdout.json` では、Faceの公差として `1e-7 mm`、UV分類器へ渡した公差として `9.999999999999999e-10` を記録。値は**分類に使う設定・返値**であり、誤差の総和の保証上界ではない。
- [OCCT 7.8.1 Precision.hxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/Precision/Precision.hxx#L160-L165)では `Confusion=1e-7`、[同PConfusion](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/Precision/Precision.hxx#L295-L305)は既定のパラメータ長100に対して `Confusion/100`。これは公差の設計値で、境界の計算誤差上界ではない。
- [BRep_Tool::Tolerance(F)](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRep/BRep_Tool.cxx#L133-L144)は少なくとも `Precision::Confusion()` を返す。したがって1e-7を原BRepの厳密な最大形状変動量と同一視しない。
- [TopClass_FaceClassifier.gxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/TopClass/TopClass_FaceClassifier.gxx#L55-L151) は指定点から判定線を用意し、FaceのWire/Edgeと交差・向き付き遷移を計算する。対応する[TopClass_Classifier2d.gxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/TopClass/TopClass_Classifier2d.gxx#L71-L209)では浮動小数の交差判定およびON・IN・OUTの分岐がある。
- [BRepClass_Intersector.cxx](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRepClass/BRepClass_Intersector.cxx#L98-L134) は頂点公差を曲面パラメータ解像度へ写像し、[同Perform](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRepClass/BRepClass_Intersector.cxx#L349-L409)は別の分岐でその値を使用する。Face公差1e-7、引数PConfusion1e-9だけを加算して「最大分類誤差1.01e-7」とする推論は不成立。

## この固定入力について数学的に上界が得られる範囲

**A：入力係数の2進表現への量子化誤差。** 抽出されたFace 0のPlane、8保存pcurveの係数・端点・パラメータ区間、実効Location、固定UV5点は整数または分母が2の冪の分数で、binary64へ厳密表現できることを全要素について検証する。よって**これらの記録値をbinary64へ符号化する操作に限り誤差上界0 mm**。これはnativeの評価演算・内部geometryとの差異がゼロとの主張ではない。

公差の表示値と名目十進定数の丸め差は別に有理数で計算する。今回の原票ではPConfusionの名目 `1e-9` に対する実値の絶対差は約 `1.45e-25`、Faceの名目 `1e-7` に対する実値の絶対差は約 `4.53e-24`。これは**十進公差定数のbinary64符号化差**であり、幾何境界の誤差や分類誤差の上界ではない。

**B：数学的リングに対する座標摂動の条件付き上界。** 理想モデルの外輪と内輪は有限の軸平行線分8本なので、各点から境界への厳密な最大ノルム（L∞）最短距離 `d` を有理数演算で求める。境界を固定し、**問い合わせ点のUV座標誤差のみが厳密にd未満**であれば、その数学的なINまたはOUT分類は変化しない。面と3Dの平面写像は直交単位ベクトルなので、この限定された写像の距離倍率は1。測定点のd：

| UV | 理想状態 | 厳密なd (mm) | 変位許容量 |
|---|---|---:|---|
| (5,-20) | IN | 4 | UV座標誤差L∞ < 4 |
| (20,-20) | OUT（穴） | 6 | < 6 |
| (9,-20) | ON（内輪） | 0 | 正の保証半径なし |
| (0,-20) | ON（外輪） | 0 | 正の保証半径なし |
| (-1,-20) | OUT（外側） | 1 | < 1 |

数学的な穴と外輪に密着する点には最小距離0が存在するため、**全連続UV領域に対して一律の正の頑健距離は存在しない**。誤差評価を全点に拡張するには、境界集合の変動・演算誤差と境界付近のON意味論を別に証明する必要がある。

**C：まだ上界と呼べない量。** 実OCCT分類器が交差を計算する全中間演算、端点/辺/頂点公差の伝播、演算順序、分岐、有限実誤差、内部Shapeの集合占有の差について、今回の証拠は**一律の有限誤差上界を与えない**。0、PConfusion、Face tolerance、または5点PASSを代用品にしない。

## 実装と証拠
`face0_error_bounds.py` は、前工程の `face-region.json`、`native-face0.stdout.json`、`face0-uv-report.json`、元の`trim-correspondence.json`を読み、元SHAと実測・過去PASSを照合する。原ソースの全係数がbinary64へ厳密に符号化できるか、5点の厳密なL∞境界距離と正の条件付き許容半径、公差定数の符号化差を出力する。`test_face0_error_bounds.py`は非2進分数、入力/出力不一致、摂動した座標・Plane、境界半径0、UNKNOWNの誤昇格を合成反例で拒否する。

同じPR #46の専用CIに、前工程で取得済みの原票だけを分析する**一つの小さいstep**を追加する。新しいnative実行・点サンプリング・専用workflowは増設しない。原ZIPは元の承認範囲に限定し、既存原本を上書きしない。

## 判定と次の最小課題
- 入力値のbinary64量子化と理想リングに対する条件付き点の頑健半径：**証明可能なら限定PASS**。
- OCCT分類器のすべてのUV点の実誤差上界：**UNKNOWN**。なぜ有限上界が導けないかも根拠を記録する。
- native Face全点集合同値、実Solid材料/空洞包含、実区間安全性：**従来のUNKNOWN / NOT_TESTED維持**。
- 次に実誤差を確定させるには、固定8辺に対する実際の使用分岐・各Edge/Vertex公差・交差算術の検査、丸めモードと演算の有向丸め包絡などを限定的に証明する。単に多くの点を追加する経路は採らない。
