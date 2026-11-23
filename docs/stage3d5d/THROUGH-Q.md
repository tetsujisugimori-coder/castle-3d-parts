# Stage 3-D-5D：D2の貫通領域Qと実Guide BRep全10面の限定検証

## 実施対象と固定領域
固定PR #46の `GATE_BoltGuide_Left.Shape.brp`、OCCT 7.8.1、D2 `cad/stage3d2/contract.json` のみを使う。Qは**新設形状ではない**。D2の既存 `moving_box` のY/Z断面 `[-115,-95]×[1000,1040]` とGuideの固定4つの材料箱のX範囲 `[-200,-180]` から、両端を1 mmずつ越す閉直方体
`Q=[-201,-179]×[-115,-95]×[1000,1040]`（mm）を再構成する。前後の本体端面を通り抜ける試験領域である。

## 数学的な境界非交差を検証する方法
`through_q.py` は固定CAD、D2、Guide BRep、`trim-correspondence.json` のSHA-256を先に検査する。実抽出済み全10 Face（Face 0と9の穴を含む）と、既存保存pcurve48使用についてFace/Wire/Edge/useの一対一対応を再照合する。各FaceでPlane、normal、外輪と内輪の方向、4頂点、線分の始点・方向、pcurveと3D Lineの**全パラメータ域のアフィン等式**を有理数で検査する。不足・重複・直線の変化・穴の欠損・境界がQを横切る場合はFAIL。

平面矩形1枚を3Dの閉AABBとして記述し、内輪のあるFace 0/9は外輪閉長方形から内輪の開内部を除いた領域を**4つの閉矩形帯**に分解する。これらの帯とQの閉AABBとのユークリッド距離の二乗を有理数で厳密に計算する。座標が直交軸に沿うため、この距離は各帯とQの真の最短距離と一致する。有限点をサンプリングして全体を推測する方式ではない。

10面の候補境界とQは各面で正距離となり、最小距離がちょうど1 mmであることを要求する。D2の4閉材料箱とQも非交差を要求する。これが意味するのは**保存された二進係数を正確値とするモデル上での非交差**であり、OCCT実装の有限実誤差まで保証した距離1mmではない。

## OCCT 7.8.1での直接観測
`guide_q_native.cpp` は元BRepを読み、固定10 Face・1 Solid・1 Shellを確認し、`BRepCheck_Analyzer`とShell Closed flagを記録。以前と同じQを `BRepPrimAPI_MakeBox` で診断専用に作り、`BRepExtrema_DistShapeShape` で**全10 FaceとQの距離**を取得する。Q内部の既存16点試験に含まれる中心 `(-190,-105,1020)` の `BRepClass3d_SolidClassifier` 観測は今回1点のみ再利用し、OUTを要求する。

実測距離が正で有理数モデルの期待値と数値的に整合した場合に限り、**固定10面に対する数値観測PASS**とする。ただし `BRepExtrema_DistShapeShape` の最小値は形式的な下界の証明ではないし、`BRepCheck_Analyzer.IsValid()` だけで理想BRepと実有限精度集合の一致を数学的に証明したことにはならない。

## 連続空洞の位相条件
Qは凸集合だから連結である。次の条件が**すべて成立するなら**、Qの中心1点OUTからQ全体OUTを導ける。
1. 固定Guideが有効な向き付き閉Solidで、その材料集合の境界が全10 Faceのトリム済み幾何集合に一致する。
2. Qとその全境界面が交差せず、10 Faceで完全な材料境界を構成する。
3. 分類したOUTが材料集合の外部を正しく表す。

集合論上、Qが連結で材料境界から離れていれば、材料の内部/外部の区分はQの中で変化しない。この条件付き含意は**数学的に正しい**。しかし上記のOCCT数値APIの記録だけで1〜3を有限実誤差込みの全点に保証する証明は未完了。よって`conditional_continuity_model=PASS`だが`native_full_q_void_inclusion=UNKNOWN`を維持し、これを自動PASSに昇格しない。

## 合格範囲と保全
- 保存した全10 Faceの有理数モデルにおけるQ非交差、最小1mm：PASSが可能。
- OCCT同一実BRepでの全10面距離・有効Solid・中心1点OUT：数値観測PASSが可能。
- 実BRepに対する有限実上界付きのQ全点空洞包含：UNKNOWNのまま。
- 代表姿勢の閂干渉、0〜35/32 mmの連続運動、128区間、残りの部品：NOT_TESTED/対象外を維持。

専用CIの既存FreeCAD抽出、保存pcurve、端面証明、元の5点トレース結果の後に新たなネイティブ検査を1ステップだけ追加する。元CAD、D2契約、保存pcurve、既存証拠、GitHub mainは変更しない。PR #46 Draft・マージHOLD継続。
