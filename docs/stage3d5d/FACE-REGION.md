# Stage 3-D-5D：Guide内輪を持つ端面1面の連続領域照合

## 実行対象
- PR #46の既存ブランチ。元のCAD、D2契約、既存72件保存pcurveと原票は変更しない。
- Guideの負X端面Face 0（Reversed）。外輪1・内輪1、各4使用。ほかの9面、実Solid材料全体、連続運動は今回の受入範囲外。
- 元FCStd SHA256 c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a、Guide BRep SHA256 043b1fb89aad7bf3004afeb1bf62c352e47250420c4e6f6f852265125e3cf261、D2 SHA256 88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa、既存72式 trim-correspondence.json SHA256 412e4488136ecb28a59a616c4d33d010ffaf75ff4e3ab962bfcf138920f9afe3。

## 厳密な候補面領域の定理
保存されたPlane/Line係数を正確な実数として扱う明示的な**数学的モデル**では、Face 0のPlaneは
S(u,v) = (-200, -130-v, 990+u) mm
である。Outer UV閉長方形 R = [0,60]×[-130,0]、Innerの開長方形 H = (9,51)×(-36,-14) について、面領域 D=R\H を定義する（内輪上の点は面に含む）。候補面領域の面積は 60×130−42×22 = 6876 mm² となる。

実際にFreeCAD/OCCTから採取されたFace 0の外輪・内輪の計8使用を、前回の**保存pcurveと72式の一対一対応がPASSした原票**へ同じFace/Wire/Edge/使用順のキーで接続する。表示係数で pcurveと3D LineのAffine等式、使用方向、全パラメータ範囲の端点、閉じた4辺の接続、法線とFace Orientation、正負の巻き方向、UVBoundsを再検査する。欠落・重複・不一致はFAILとする。サンプリングだけの等式検査ではない。

Outer/Innerがそれぞれ厳密な軸平行長方形であり、InnerがOuter内部に正距離で入ることから、Dは正則閉集合（自身の内部の閉包）である。面上の座標区間をすべて含む原子格子に分割すると、その各開セルでDの占有は一様である。D2 Guideの4閉材料箱の負X端面も正則閉な有限和集合となるため、全開原子セルの占有が両方向で一致すれば、**内輪/外輪を含む全連続端面領域の数学的モデルは等しい**。この中点計算は有限点による任意曲面の推測ではなく、全端点で分割した領域の厳密な記号判定である。

## PASSに含まれない内容
- この定理は、FreeCAD APIが返した二進係数を正確な値と定義し、保存pcurveとPlaneの数学的表現、通常のBRep Faceのtrim領域意味論を前提とする。OCCT内部の実評価・公差を含む連続幾何集合までの厳密同値と有限実誤差上界は**UNKNOWN**。
- Face 0の領域がD2の1枚の端面と一致しても、ほかの9面の実領域・接続・法線の総合意味論と、実Solid材料の全点集合、実空洞包含は**UNKNOWN**。
- 実区間0〜35/32 mmの連続運動、全状態の配置誤差・安全性は**NOT_TESTED**。既存72件・16点観測や代表モデル距離1mmをnative実安全PASSに昇格しない。

## 試験と保全
新規 face_region.py と test_face_region.py のみを追加し、専用workflowの保存pcurve検証の**後**で同じ実行の trim-correspondence.json と stored-pcurve-report.json を直接使用する。新規原票は face-region/face-region.json（対象Face、8使用、UV区間、閉領域定義、D2端面比較、UNKNOWN項目と原物SHA）。合成試験は欠落Wire/Edge、巻き方向、保存使用の欠落/重複、パラメータ域、Plane位置、直線係数、穴の閉塞・移動、Face向き、内輪の接触を別々に拒否する。

固定HEAD CIで単体・実FreeCAD経由の原票生成・SHA manifest・失敗ログを確認し、得られた原ZIPを取得して必要範囲でCRC/サイズ/SHA再照合する。元の原証拠を上書きせず、独立再実行・独立レビューを行っていなければその限界を明示。**限定受入は表示係数の連続面領域数学モデルに限る。PRはDraft・マージHOLD。**
