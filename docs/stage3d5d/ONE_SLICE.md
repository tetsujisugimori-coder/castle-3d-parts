# Stage 3-D-5D: Bolt/Guideの代表1姿勢・1区間の実BRep診断

出発点はPR #39統合済みmainのmerge commit affa6e3375f2cffd09e31c0b062a3ae7fd1f4faa。Issue #38に紐付く独立研究であり、Draft PR #40/#41の受入・保全・HOLDを変更しない。

## 対象と判断境界
- 固定FCStd cad/stage3c/generated/assembly.FCStd SHA-256 c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a、D2契約 cad/stage3d2/contract.json SHA-256 88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa。二部材 GATE_Bolt と GATE_BoltGuide_Left のみ。
- 扉0°、移動区間D2第1葉 ordinal 0 [0,35/32] mm、代表姿勢は中点 35/64 mm（0.546875 mm）。新たな葉分割はしない。
- 数学モデルではGuideの4個の閉AABB材料に対し、Bolt断面から定義した閉じた通過セルと各材料の軸方向の分離を厳密なFractionで証明する。最小分離1 mmから代表点まわりの最大並進量35/64 mmを控除した**条件付きモデル下限29/64 mm**は実CADの誤差・安全余裕ではない。
- 実BRepの材料外側について、Bolt/Guideの実Shapeから名目の閉材料モデルを引いた差の観測体積を計測する。**値0でも包含証明ではない**。差が正なら候補モデルの見直し対象として扱う。
- 空洞内側について、Guideの実Shapeと閉通過セルの最短距離および交差体積を観測する。**距離が正でも実空洞の全点保証ではない**。接触・貫通・数値誤差は観測として切り分ける。
- OCCTのBoolean/Distanceは浮動小数・カーネル公差と計算失敗を含む。したがって材料外側・空洞内側・有限実誤差・実区間安全性の値はすべてUNKNOWN/NOT_TESTEDのままで、どんな結果値・自己申告フラグでもPASSへ昇格しない。

## 実行経路
cad/stage3d5d/one_slice.py は固定原物とD2依存ファイルのSHAを検査し、FCStd ZIP内部の原BRepを読み取る。XMLの保存姿勢が0/0であることを確認し、読み取ったBoltを隔離メモリ上で中点移動する。原FCStdは再計算・修復・保存しない。出力は観測と欠落理由を区別したJSONのみ。テストで接触、変異、見かけのゼロ差・正距離からの誤昇格を拒否する。

専用workflowは当該新規パスへのPR変更時だけ、読取専用権限で1 native jobを実行し、原出力をartifactとして収録する。CI成功は研究コードの実行が完了した意味であり、CAD安全証明の成功ではない。出力からGit checkoutのHEAD/tree/parentsと固定原物のハッシュを対応付ける。原artifactの保存・再取得監査は実施していなければPENDINGとする。

## 実CADの証明に残る前提（今回の対象を広げない）
1. OCCTの面/trim/pcurve/3D曲線から**実材料集合が外側境界に含まれる**ことを連続かつ保守的に示す根拠。Boolean結果の体積ゼロだけでは不足。
2. Guideの内向き壁・両端の開放・向きから**閉通過セル全体が実CADの開空洞にある**ことを示す根拠。材料外側包含から空洞内側包含を推論しない。
3. 実BRep・浮動小数API・配置合成の有限実誤差、および全区間のDocument状態関数が参照並進と一致する証明。欠落項は勝手に0としない。

受入の初期状態は総合PARTIAL、研究診断のみ限定検証対象、実CAD代表区間NOT_TESTED、実CAD128区間NOT_TESTED、既存解析128 PASSは別集計。元のD4のUNKNOWN128も履歴として維持。旧CAD/Web/ledger/既存workflowは変更しない。マージ・公開・Draft解除なし。
